"""Composition root for the app's portfolio documents (watchlist, holdings risk; plan 15 ph7f)."""

from __future__ import annotations

import json
from pathlib import Path

from quant_cn.calculation.earnings_event_builder import EarningsEventBuilder
from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.app_publisher_settings import AppPublisherSettings
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.positions_book import PositionsBook
from quant_cn.core.sector_earnings_signal_settings import SectorEarningsSignalSettings
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.lake.buyback_ledger import BuybackLedger
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.fundamental_signal_reader import FundamentalSignalReader
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.margin_signal_reader import MarginSignalReader
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.shareholder_yield_reader import ShareholderYieldReader
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.portfolio.app_rank_reader import AppRankReader
from quant_cn.portfolio.condition_evaluator import ConditionEvaluator
from quant_cn.portfolio.developer_sales_reader import DeveloperSalesReader
from quant_cn.portfolio.holdings_history_writer import HoldingsHistoryWriter
from quant_cn.portfolio.holdings_risk_builder import HoldingsRiskBuilder
from quant_cn.portfolio.market_signal_reader import MarketSignalReader
from quant_cn.portfolio.position_reviewer import PositionReviewer
from quant_cn.portfolio.sector_earnings_signal_builder import SectorEarningsSignalBuilder
from quant_cn.portfolio.sector_metric_reader import SectorMetricReader
from quant_cn.portfolio.sector_monitor_builder import SectorMonitorBuilder
from quant_cn.portfolio.watchlist_builder import WatchlistBuilder
from quant_cn.risk.risk_decomposer import RiskDecomposer
from quant_cn.risk.risk_model_factory import RiskModelFactory

# Style ETF heat (plan 15 ph7g) comes from the app document written by `make etf-proxy`.
ETF_FILE = Path("research_space/prototypes/chain_view/etf_proxy.json")


class AppServiceBuilder:
    """
    Purpose:
        Wire the builders behind the app's watchlist and holdings pages with their condition
        evaluation (筹码结构, statements, manual series) so the CLI stays a thin dispatcher.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_evaluator`, `build_watchlist`, `build_holdings_risk`,
            `build_sector_monitor`, `build_sector_earnings_signal`
        Raises:
            (none at construction)

    Used by:
        cli.ResearchCommands  -- `watchlist`, `holdings-risk`, `sector-monitor` and
                                 `sector-earnings-signal` commands

    Test cases:
        TC-ASB-001  each builder is wired with its evaluator / reviewer on a sample lake
        TC-ASB-002  the evaluator gets the style heat z from etf_proxy.json; none without it
        TC-ASB-003  build_sector_monitor wires the sector monitor from config/sector_monitors.yaml
        TC-ASB-004  build_sector_earnings_signal wires the 财报季信号 builder (plan 35)
    """

    def build_evaluator(self, config: Config, catalog: LakeCatalog) -> ConditionEvaluator:
        """
        Purpose:
            Condition evaluator over the lake of `catalog`.

        Contract:
            Input:
                config, catalog
            Output:
                ConditionEvaluator  -- chips with the RetailGauge from derived.retail_gauge; heat
                                       metrics ("<style>_etf_z") from etf_proxy.json when present
            Raises:
                (none)
        """
        query = LakeQuery(catalog)
        aliases = TickerAliasMap(catalog, query, config.ticker_aliases)
        versions = StatementVersionReader(query, aliases, DateCodec())
        chips = ChipStructureReader(query)
        heat = self._read_heat(config.repo_root / ETF_FILE)
        capital = ShareholderYieldReader(query, BuybackLedger(query))
        return ConditionEvaluator(
            chips,
            FundamentalSignalReader(versions, query),
            heat,
            MarginSignalReader(query),
            capital,
        )

    def build_watchlist(self, config: Config, catalog: LakeCatalog) -> WatchlistBuilder:
        """
        Purpose:
            Watchlist builder with entry conditions evaluated.

        Contract:
            Input:
                config, catalog
            Output:
                WatchlistBuilder
            Raises:
                (none)
        """
        evaluator = self.build_evaluator(config, catalog)
        return WatchlistBuilder(config, LakeQuery(catalog), DateCodec(), evaluator)

    def build_sector_earnings_signal(
        self, config: Config, catalog: LakeCatalog
    ) -> SectorEarningsSignalBuilder:
        """
        Purpose:
            财报季信号 builder (plan 35, D-172) over the lake of `catalog`.

        Contract:
            Input:
                config, catalog
            Output:
                SectorEarningsSignalBuilder
            Raises:
                ConfigError  -- invalid config/sector_earnings_signal.yaml
        """
        settings = SectorEarningsSignalSettings.load(config.repo_root)
        query = LakeQuery(catalog)
        events = EarningsEventBuilder(settings, query, DateCodec())
        return SectorEarningsSignalBuilder(settings, events, query)

    def build_sector_monitor(self, config: Config, catalog: LakeCatalog) -> SectorMonitorBuilder:
        """
        Purpose:
            Sector monitor builder (plan 31 ph4) over the lake of `catalog`.

        Contract:
            Input:
                config, catalog
            Output:
                SectorMonitorBuilder
            Raises:
                ConfigError  -- invalid or missing config/sector_monitors.yaml or
                config/app_publishers.yaml
        """
        settings = SectorMonitorSettings.load(config.repo_root)
        root = config.lake.root
        writer = ParquetWriter(root)
        query = LakeQuery(catalog)
        return SectorMonitorBuilder(
            settings,
            SectorMetricReader(settings, query, GraphStore(writer, root)),
            DeveloperSalesReader(LabelStore(writer, root, DateCodec()), settings.history_months),
            RealizedVolCalculator(settings.pct_window, settings.pct_min_obs),
            ChipStructureReader(query),
            AppRankReader(
                settings, AppPublisherSettings.load(config.repo_root), query, DateCodec()
            ),
            MarketSignalReader(
                settings,
                query,
                RealizedVolCalculator(settings.val_window, settings.val_min_obs),
                DateCodec(),
            ),
        )

    def build_holdings_risk(
        self, config: Config, catalog: LakeCatalog, book: PositionsBook, benchmark: str
    ) -> HoldingsRiskBuilder:
        """
        Purpose:
            Holdings risk builder with the lake history writer and the position reviewer.

        Contract:
            Input:
                config, catalog; book: PositionsBook; benchmark: str (index_code)
            Output:
                HoldingsRiskBuilder
            Raises:
                ConfigError  -- unknown risk model in config
        """
        query = LakeQuery(catalog)
        model = RiskModelFactory(query).build(config.risk_model)
        history = HoldingsHistoryWriter(query, ParquetWriter(config.lake.root))
        reviewer = PositionReviewer(book, self.build_evaluator(config, catalog))
        decomposer = RiskDecomposer()
        return HoldingsRiskBuilder(book, query, model, decomposer, history, benchmark, reviewer)

    @staticmethod
    def _read_heat(path: Path) -> dict[str, float]:
        if not path.exists():
            return {}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {
            s["metric"]: float(s["z"])
            for s in doc.get("styles") or []
            if s.get("metric") and s.get("z") is not None
        }
