"""RetailGauge CLI commands: `retail-gauge` and `retail-gauge-backtest` (plan 21 ph3)."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from rich.console import Console

from quant_cn.calculation.company_cycle_panel import CompanyCyclePanel
from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.calculation.retail_gauge_evaluator import RetailGaugeEvaluator
from quant_cn.calculation.retail_gauge_feature_builder import RetailGaugeFeatureBuilder
from quant_cn.calculation.retail_gauge_model import RetailGaugeModel
from quant_cn.calculation.retail_gauge_nowcaster import RetailGaugeNowcaster
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.opportunity_settings import OpportunitySettings
from quant_cn.core.positions_book import PositionsBook
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.valuation_history_reader import ValuationHistoryReader
from quant_cn.portfolio.opportunity_document import OpportunityDocument
from quant_cn.portfolio.opportunity_rules import OpportunityRules
from quant_cn.portfolio.opportunity_screen import OpportunityScreen
from quant_cn.portfolio.style_fit_checker import StyleFitChecker
from quant_cn.risk.risk_model_factory import RiskModelFactory

MODEL_DIR = ("meta", "models", "retail_gauge")


class GaugeCommands:
    """
    Purpose:
        The 散户温度计 RetailGauge commands (plan 21 ph3, D-142, D-155, D-167):
        - `retail-gauge-backtest --end`: expanding walk-forward at every quarter end
          (derived/reports/retail_gauge/backtest.parquet), then the quarterly evaluation
          (evaluation.parquet); prints the mean IC, hit rates and avoid excess;
        - `retail-gauge --start --end`: daily readings for every session in [start, end]
          (default: the last session), one quarter at a time, into derived/retail_gauge
          (the last session's features into derived/retail_gauge_features); models are
          trained on first use of a retrain key and saved under meta/models/retail_gauge;
        - `opportunity-list --date`: the daily opportunity list (plan 21 ph4) on the last
          session on or before the date (default today) into derived/opportunity_list, the
          user's holdings excluded; prints the listed names and near-misses; with `--out`
          also writes opportunities.json (OpportunityDocument) for the app (ph5).
        All read the lake read-only and take the write lock only to refresh the derived
        views at the end.

    Contract:
        Input:
            console: Console
        Output:
            instance; `build_parser`, `_run_retail_gauge`, `_run_retail_gauge_backtest`,
            `_run_opportunity_list` (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- dispatch

    Test cases:
        TC-QCC-019  retail-gauge on an empty lake: the LakeError is reported (exit 1), nothing
                    written
        TC-QCC-020  opportunity-list on an empty lake: the LakeError is reported (exit 1),
                    nothing written
    """

    def __init__(self, console: Console) -> None:
        self._console = console

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
        """
        Purpose:
            Add the `retail-gauge`, `retail-gauge-backtest` and `opportunity-list` subcommands.

        Contract:
            Input:
                sub: argparse subparsers of QuantCnCli
            Output:
                None
            Raises:
                (none)
        """
        rg = sub.add_parser(
            "retail-gauge", help="daily 散户温度计 readings -> derived/retail_gauge"
        )
        rg.add_argument("--start", default=None, help="YYYYMMDD (default: --end)")
        rg.add_argument("--end", default=None, help="YYYYMMDD (default: today)")
        bt = sub.add_parser("retail-gauge-backtest", help="walk-forward + evaluation of the gauge")
        bt.add_argument("--end", default=None, help="YYYYMMDD (default: today)")
        ol = sub.add_parser("opportunity-list", help="daily opportunity list -> derived/")
        ol.add_argument("--date", default=None, help="YYYYMMDD (default: today)")
        ol.add_argument("--out", type=Path, default=None, help="app data dir: opportunities.json")

    def _run_retail_gauge(self, config: Config, args: argparse.Namespace) -> int:
        end = args.end or dt.date.today().strftime("%Y%m%d")
        start = args.start or end
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            features, nowcaster = self._build(config, catalog)
            features.load(end)
            sessions = [str(d) for d in features.sessions]
            days = [d for d in sessions if start <= d <= end] or sessions[-1:]
            quarters: dict[str, list[str]] = {}
            for d in days:
                quarters.setdefault(d[:4] + str((int(d[4:6]) - 1) // 3), []).append(d)
            rows = 0
            for batch in quarters.values():
                out = nowcaster.run(batch)
                rows += len(out)
                self._console.print(f"retail gauge {batch[0]}..{batch[-1]}: {len(out)} rows")
        finally:
            catalog.close()
        self._refresh_views(config)
        self._console.print(f"retail gauge: {len(days)} sessions, {rows} rows")
        return 0

    def _run_retail_gauge_backtest(self, config: Config, args: argparse.Namespace) -> int:
        end = args.end or dt.date.today().strftime("%Y%m%d")
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            _, nowcaster = self._build(config, catalog)
            backtest = nowcaster.run_walk_forward(end)
            settings = RetailGaugeSettings.load(config.repo_root)
            query, writer = LakeQuery(catalog), ParquetWriter(config.lake.root)
            report = RetailGaugeEvaluator(settings, query, writer).run(backtest)
        finally:
            catalog.close()
        self._refresh_views(config)
        self._console.print(report.round(3).to_string(index=False))
        mean = report[["ic", "hit_top", "hit_bottom", "avoid_excess"]].mean()
        self._console.print(
            f"retail gauge backtest: {len(report)} quarters, IC {mean['ic']:.3f}, "
            f"top hit {mean['hit_top']:.0%}, bottom hit {mean['hit_bottom']:.0%}, "
            f"avoid excess {mean['avoid_excess']:.2f}%"
        )
        return 0

    def _run_opportunity_list(self, config: Config, args: argparse.Namespace) -> int:
        date = args.date or dt.date.today().strftime("%Y%m%d")
        book = PositionsBook.load(config.repo_root)
        catalog = LakeCatalog(config.lake.root, config.datasets, read_only=True)
        try:
            screen = self._build_screen(config, catalog)
            out = screen.build(date, book)
            session = str(out["as_of"].iloc[0]) if not out.empty else date
            previous = screen.read_previous(session)
            screen.write(out)
        finally:
            catalog.close()
        self._refresh_views(config)
        if args.out is not None:
            document = OpportunityDocument(OpportunitySettings.load(config.repo_root))
            path = document.write(document.build(out, previous, session), args.out)
            self._console.print(f"opportunities -> {path}")
        for row in out.to_dict("records"):
            new = " new" if row["is_new"] else ""
            self._console.print(
                f"{row['rank']:>2} {row['status']:<6} {row['ts_code']} {row['name']} "
                f"pct {row['pct']:.2f}{new}  hit {row['rules_hit']}  missing {row['missing']}"
            )
        listed = int((out["status"] == "listed").sum()) if not out.empty else 0
        self._console.print(
            f"opportunity list {date}: {listed} listed, {len(out) - listed} near-misses"
        )
        return 0

    @staticmethod
    def _build_screen(config: Config, catalog: LakeCatalog) -> OpportunityScreen:
        settings = OpportunitySettings.load(config.repo_root)
        query, codec = LakeQuery(catalog), DateCodec()
        aliases = TickerAliasMap(catalog, query, config.ticker_aliases)
        return OpportunityScreen(
            settings,
            query,
            ChipStructureReader(query),
            ValuationHistoryReader(query),
            StatementVersionReader(query, aliases, codec),
            CompanyCyclePanel(codec, config.discovery),
            RiskModelFactory(query).build(config.risk_model),
            OpportunityRules(settings),
            StyleFitChecker(settings),
            DatedTableStore(ParquetWriter(config.lake.root)),
        )

    def _refresh_views(self, config: Config) -> None:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            DerivedViews(catalog, LakeQuery(catalog), config.datasets).refresh_tables()
        finally:
            catalog.close()

    def _build(
        self, config: Config, catalog: LakeCatalog
    ) -> tuple[RetailGaugeFeatureBuilder, RetailGaugeNowcaster]:
        settings = RetailGaugeSettings.load(config.repo_root)
        query, writer = LakeQuery(catalog), ParquetWriter(config.lake.root)
        holders = HolderCountPanel(query)
        tables = DatedTableStore(writer)
        features = RetailGaugeFeatureBuilder(settings, query, holders, tables)
        root = config.lake.root.joinpath(*MODEL_DIR)
        nowcaster = RetailGaugeNowcaster(
            settings,
            features,
            holders,
            writer,
            tables,
            root,
            lambda: RetailGaugeModel(settings),
        )
        return features, nowcaster
