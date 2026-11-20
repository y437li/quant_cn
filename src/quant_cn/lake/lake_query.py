"""The read API over the lake: SQL through the catalog connection (D-009)."""

from __future__ import annotations

import re
from collections.abc import Sequence

import duckdb
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import PRICE_PANEL
from quant_cn.lake.lake_catalog import LakeCatalog

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SCHEMAS = ("raw", "curated", "derived", "quality", "meta", "project")


class LakeQuery:
    """
    Purpose:
        Run read queries against the catalog views; the only way code above the lake reads data.

    Contract:
        Input:
            catalog: LakeCatalog
        Output:
            instance; `sql`, `has_view`, `read_prices`, `register_frame`, `list_views`
        Raises:
            (none at construction)

    Used by:
        portfolio.OpportunityScreen  -- injected type or call
        lake.ValuationHistoryReader  -- injected type or call
        calculation.HolderCountPanel  -- stk_holdernumber
        calculation.RetailGaugeFeatureBuilder  -- matrices, chips
        calculation.RetailGaugeEvaluator  -- forward prices
        cli.GaugeCommands  -- wires it
        portfolio.SectorMetricReader  -- sector monitor reads
        portfolio.AppRankReader  -- App Store chart reads
        portfolio.BuybackMonitorBuilder  -- listing titles, holder trades, market caps
        portfolio.MarketSignalReader  -- valuation, forecasts, surveys
        calculation.VolatilityMonitorBuilder  -- options, shibor, calendar, cboe_vix
        calculation.RatesFxSeriesReader  -- curves, US yields, shibor, FX, fixing, index EP
        calculation.RatesFxMonitorBuilder  -- curve snapshot
        calculation.EarningsEventBuilder  -- statements, previews, flashes, prices (plan 35)
        calculation.ConsensusPanelBuilder  -- report_rc consensus (plan 36)
        portfolio.SectorEarningsSignalBuilder  -- members, L2 indices, holder counts (plan 35)
        portfolio.SmallCapWatchBuilder  -- daily, limits, indices, ETF prices and shares
        data_loading.DocumentRetyper      -- manifest read
        lake.TradingCalendar         -- reads raw.trade_cal
        lake.Compactor.rebuild       -- reads raw files through DuckDB
        cli.QuantCnCli               -- composition root
        pipeline.CuratePipeline      -- injected type or call
        pipeline.DeriveStep          -- injected type or call
        lake.DerivedViews            -- injected type or call
        lake.PitAligner              -- injected type or call
        cli.ServiceBuilder           -- injected type or call
        data_loading.FetcherFactory  -- injected type or call
        lake.QualityViews            -- injected type or call
        lake.ReleaseLagChecker       -- injected type or call
        lake.LakeReader              -- injected type or call
        lake.TickerAliasMap          -- injected type or call
        pipeline.UniverseStep        -- injected type or call
        lake.ExposureReader          -- injected type or call
        pipeline.EvaluationStep      -- injected type or call
        pipeline.FeatureStep         -- injected type or call
        cli.ResearchCommands         -- injected type or call
        cli.DocumentCommands             -- injected type or call
        data_loading.DocumentDownloader  -- metadata and manifest reads
        portfolio.WatchlistBuilder       -- prices, valuation and consensus for the watchlist
        portfolio.EtfProxyBuilder        -- ETF basics, shares and prices for the proxy
        portfolio.LookThroughWeights     -- index weights for ETF baskets in the holdings risk
        lake.StatementVersionReader      -- statement versions known on a date
        risk.RiskModel  -- injected type or call
        risk.RiskModelFactory  -- injected type or call
        pipeline.RiskModelStep  -- injected type or call
        pipeline.RiskValidationWriter  -- injected type or call
        risk.RiskInputLoader  -- injected type or call
        risk.FactorMonitorBuilder  -- injected type or call
        portfolio.HoldingsHistoryWriter  -- injected type or call
        portfolio.HoldingsRiskBuilder  -- injected type or call
        cli.AppServiceBuilder  -- wires it
        lake.ChipStructureReader  -- injected type or call
        lake.FundamentalSignalReader  -- injected type or call
        cli.ReportCommands  -- last session for `morning-report`
        calculation.MacroMonitorBuilder  -- curated macro tables
        calculation.FuturesMonitorBuilder  -- fut_basic and fut_daily
        calculation.IndexFuturesMonitor  -- derived futures views, index closes
        calculation.FuturesBrokerNets  -- derived.fut_holding_brokers
        lake.BuybackLedger  -- curated.repurchase
        lake.ShareholderYieldReader  -- daily_basic yields
        lake.MarginSignalReader  -- margin_detail
        portfolio.MarginPanelBuilder  -- margin_detail, daily, daily_basic
        portfolio.BuybackEventsBuilder  -- repurchase, stock_basic, daily_basic
        portfolio.EtfCtaBook  -- fund_daily, fund_nav
        industry_graph.LegacyLabelImporter  -- public dates of documents

    Test cases:
        TC-LQ-001  sql returns a DataFrame with parameters bound
        TC-LQ-002  bad SQL raises LakeError
        TC-LQ-003  has_view reflects which views exist
        TC-LQ-004  read_prices returns PRICE_PANEL rows in range, filtered and sorted
        TC-LQ-005  register_frame makes a frame joinable; list_views includes it and curated views
    """

    def __init__(self, catalog: LakeCatalog) -> None:
        self._catalog = catalog

    def sql(self, query: str, params: Sequence[object] | None = None) -> pd.DataFrame:
        """
        Purpose:
            Execute a query and return the result as a DataFrame.

        Contract:
            Input:
                query:  str                      -- DuckDB SQL, `?` placeholders
                params: Sequence[object] | None  -- bound in order
            Output:
                DataFrame  -- may be empty
            Raises:
                LakeError  -- DuckDB error (syntax, missing view, type)
        """
        try:
            return self._catalog.connection.execute(query, list(params or [])).df()
        except duckdb.Error as exc:
            raise LakeError(f"query failed: {exc}") from exc

    def has_view(self, name: str) -> bool:
        """
        Purpose:
            True if `schema.view` exists in the catalog.

        Contract:
            Input:
                name: str  -- "raw.trade_cal", "curated.daily", ...
            Output:
                bool
            Raises:
                LakeError  -- catalog unreadable
        """
        schema, _, view = name.partition(".")
        found = self.sql(
            "SELECT 1 FROM duckdb_views() WHERE schema_name = ? AND view_name = ?", [schema, view]
        )
        return not found.empty

    def read_prices(
        self, start: str, end: str, tickers: Sequence[str] | None = None
    ) -> pd.DataFrame:
        """
        Purpose:
            Adjusted daily prices from `derived.prices_adj` for a date range.

        Contract:
            Input:
                start, end: str                 -- YYYYMMDD, inclusive
                tickers:    Sequence[str] | None  -- ts_code filter; None = all
            Output:
                DataFrame  -- PRICE_PANEL, sorted by (trade_date, ts_code); suspended days absent
            Raises:
                LakeError    -- view missing (run curate) or query failure
                SchemaError  -- the view no longer matches PRICE_PANEL
        """
        codes = list(tickers) if tickers is not None else None
        raw = self.sql(
            "SELECT * FROM derived.prices_adj WHERE trade_date BETWEEN ? AND ? "
            "AND (? IS NULL OR list_contains(?, ts_code)) ORDER BY trade_date, ts_code",
            [start, end, codes, codes],
        )
        return PRICE_PANEL.validate(PRICE_PANEL.normalize(raw, strict=True))

    def register_frame(self, name: str, frame: pd.DataFrame) -> str:
        """
        Purpose:
            Expose an in-memory frame as a view so SQL can join it with lake views.

        Contract:
            Input:
                name: str  -- identifier ([A-Za-z_][A-Za-z0-9_]*)
                frame: DataFrame
            Output:
                str  -- the view name to use in SQL
            Raises:
                ValueError  -- name is not a plain identifier
                LakeError   -- registration failed
        """
        if not _IDENTIFIER.match(name):
            raise ValueError(f"not a plain identifier: {name!r}")
        try:
            self._catalog.connection.register(name, frame)
        except duckdb.Error as exc:
            raise LakeError(f"cannot register {name}: {exc}") from exc
        return name

    def list_views(self) -> list[str]:
        """
        Purpose:
            Every lake view as "schema.view", plus registered frames by bare name.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- sorted
            Raises:
                LakeError  -- catalog unreadable
        """
        views = self.sql("SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal")
        out = [
            f"{s}.{v}" if s in _SCHEMAS else v
            for s, v in zip(views["schema_name"], views["view_name"], strict=True)
        ]
        return sorted(out)
