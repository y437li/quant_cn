"""Project exception hierarchy; every raised error is a `QuantCnError` (CODING_STANDARD §2.5)."""

from __future__ import annotations


class QuantCnError(Exception):
    """
    Purpose:
        Root of every exception the package raises, so callers catch project errors in one place.

    Contract:
        Input:
            message: str  -- human-readable reason; may be empty
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        pipeline.LocalRunner.run  -- catches any project error to close the run as failed
        cli.QuantCnCli.run        -- turns project errors into exit code 1
        core.ConfigError          -- subclass
        core.DataSourceError      -- subclass
        core.LakeError            -- subclass
        core.SchemaError          -- subclass
        pipeline.PrefectRunner    -- injected type or call
        risk.RiskSnapshot  -- injected type or call

    Test cases:
        TC-QCE-001  every project exception is a QuantCnError subclass
    """


class ConfigError(QuantCnError):
    """
    Purpose:
        Configuration is missing, malformed or unsafe (e.g. lake root inside the repository).

    Contract:
        Input:
            message: str  -- which key is wrong and why
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        core.UpdateAllSettings  -- invalid config/update_all.yaml
        cli.UpdateCommands      -- unknown make targets
        core.OpportunitySettings  -- invalid config/discovery_rules.yaml
        core.SectorMonitorSettings  -- invalid config/sector_monitors.yaml
        core.AppPublisherSettings  -- invalid config/app_publishers.yaml
        industry_graph.TaxonomyChangeSet  -- a bad version file
        industry_graph.NodeLineageBuilder  -- missing successor, retire loop
        core.SentAlertLog  -- malformed notify_sent.json
        core.NotifySettings  -- invalid config/local.notify.yaml, unknown recipient
        core.VolatilityMonitorSettings  -- invalid config/volatility_monitor.yaml
        core.RatesFxMonitorSettings  -- invalid config/rates_fx_monitor.yaml
        core.SectorEarningsSignalSettings  -- invalid config/sector_earnings_signal.yaml
        core.RetailGaugeSettings  -- invalid config/retail_gauge.yaml
        core.SmallCapWatchSettings  -- invalid config/smallcap_watch.yaml or its local file
        data_loading.DocumentRetyper      -- unknown source
        core.Config.load                   -- bad YAML, unsafe lake root
        core.Config.get_dataset            -- unknown dataset name
        data_loading.TushareClient         -- missing token
        data_loading.FetcherFactory.build  -- unknown sweep kind
        industry_graph.ProductTaxonomy     -- missing folder, bad file, duplicate node id
        pipeline.DownloadPipeline.run      -- unknown dataset requested
        pipeline.CuratePipeline            -- injected type or call
        factor.FactorFactory               -- injected type or call
        data_loading.DocumentDownloader  -- unknown document source
        data_loading.DeepSeekClient      -- API key missing
        core.PositionsBook  -- unreadable or invalid positions book
        data_loading.ManualSeriesClient  -- invalid or duplicate manual series rows
        core.MailSender  -- raises it
        core.MailSettings  -- raises it
        core.FuturesMonitorSettings  -- invalid config/futures_monitor.yaml
        core.EtfCtaSettings  -- invalid config/etf_cta.yaml
        core.EtfCtaViews  -- invalid views file or unknown view target
        core.LabelSource  -- malformed label_sources.yaml

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """


class SchemaError(QuantCnError):
    """
    Purpose:
        A DataFrame does not satisfy its declared Schema (columns, dtypes, primary key).

    Contract:
        Input:
            message: str  -- the failing column or key
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        industry_graph.GraphQuery  -- bad dates
        lake.GraphStore  -- unknown graph table
        core.Schema.normalize  -- value not convertible to the declared dtype
        core.Schema.validate   -- column set, dtype or primary-key violation
        lake.LabelStore  -- malformed label rows
        industry_graph.EdgeSpanBuilder  -- bad as_of
        industry_graph.NodeEdgeBuilder  -- bad as_of

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """


class DataSourceError(QuantCnError):
    """
    Purpose:
        The external data source failed: API error code, retries exhausted, malformed response.

    Contract:
        Input:
            message: str  -- endpoint and vendor message
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        core.IMessageSender  -- empty input, osascript failure
        data_loading.CboeClient  -- bad index code, unexpected CSV, retries exhausted
        data_loading.TushareClient.query  -- non-zero code after retries, network failure
        core.BaseFetcher.run              -- records the failing key, then re-raises
        core.PermissionDeniedError        -- subclass
        data_loading.AkshareClient        -- injected type or call
        data_loading.BaostockClient       -- injected type or call
        data_loading.CninfoClient         -- missing date range
        data_loading.EastmoneyReportClient -- unknown report kind
        data_loading.AppStoreClient        -- missing country or unknown chart
        data_loading.NbsHousePriceClient   -- a release without the 70-city tables
        data_loading.NppaGameClient        -- unknown channel, list without the approval table
        data_loading.DocumentDownloader  -- failed download recorded
        data_loading.RequestPacer        -- failure after retries
        industry_graph.PdfTextExtractor   -- unreadable or non-PDF file
        industry_graph.ApplicationExtractor -- reply does not fit the shape
        industry_graph.ValuationExtractor  -- reply does not fit the shape
        industry_graph.QuarterlyNoteExtractor  -- reply does not fit the shape
        industry_graph.GuidanceExtractor  -- unknown doc type, reply does not fit the shape
        industry_graph.ContractExtractor  -- reply does not fit the shape
        industry_graph.BaseQuotedExtractor  -- reply without an items list
        industry_graph.EntityAliasExtractor  -- reply without an items list
        industry_graph.BrokerViewSynthesizer  -- unknown scope, reply does not fit the shape
        industry_graph.BusinessModeExtractor  -- reply does not fit the shape
        industry_graph.PricingAdjudicator  -- reply does not fit the shape, label not allowed
        industry_graph.MoatExtractor  -- reply does not fit the shape

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """


class PermissionDeniedError(DataSourceError):
    """
    Purpose:
        The account lacks permission (points) for an endpoint; the dataset is blocked, not broken.

    Contract:
        Input:
            message: str  -- endpoint and vendor message
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        data_loading.TushareClient.query  -- vendor message matches a permission marker
        pipeline.LocalRunner.run          -- marks the step blocked and continues with the next
        pipeline.PrefectRunner            -- injected type or call

    Test cases:
        TC-QCE-001  subclass of DataSourceError and QuantCnError
    """


class LakeError(QuantCnError):
    """
    Purpose:
        The local lake cannot be read or written: missing dataset, failed atomic write, bad catalog.

    Contract:
        Input:
            message: str  -- path or dataset involved
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        portfolio.OpportunityDocument  -- missing output directory
        lake.TaskLog                -- ledger write / read / view
        pipeline.TaskStatusBuilder  -- status file write
        cli.UpdateCommands          -- view refresh warning
        portfolio.OpportunityScreen  -- no session, RetailGauge table missing
        lake.ValuationHistoryReader  -- unknown field
        portfolio.SectorMonitorBuilder  -- missing output directory
        calculation.VolatilityMonitorBuilder  -- empty opt_daily, missing output dir
        calculation.RatesFxMonitorBuilder  -- no line has data, missing output dir
        portfolio.SectorEarningsSignalBuilder  -- missing output directory
        calculation.RetailGaugeFeatureBuilder  -- no data loaded
        lake.DatedTableStore  -- unreadable or missing table
        calculation.RetailGaugeModel  -- predict / save before fit, unreadable model
        calculation.RetailGaugeNowcaster  -- too few quarters, no backtest / calibration
        calculation.RatesFxSeriesReader  -- an unreadable table (caught: empty series)
        portfolio.SmallCapWatchBuilder  -- empty curated.daily, missing output dir
        portfolio.BuybackMonitorBuilder  -- missing output directory
        data_loading.DocumentManifestWriter -- manifest write
        data_loading.DocumentRetyper      -- file move
        lake.ParquetWriter         -- atomic write failed
        lake.TradingCalendar       -- trade_cal not downloaded yet
        lake.LakeQuery.sql         -- DuckDB query error
        cli.QuantCnCli             -- backup target missing
        portfolio.EtfProxyBuilder  -- no share rows, missing output directory
        risk.FactorMonitorBuilder  -- risk frames missing, missing output directory
        lake.Compactor             -- injected type or call
        pipeline.DownloadPipeline  -- injected type or call
        lake.FetchLog              -- injected type or call
        lake.LakeCatalog           -- injected type or call
        lake.RunLog                -- injected type or call
        pipeline.DeriveStep        -- injected type or call
        lake.DerivedViews          -- injected type or call
        lake.PitAligner            -- injected type or call
        lake.ProjectCatalog        -- injected type or call
        lake.QualityViews          -- injected type or call
        lake.RebuildAudit          -- injected type or call
        lake.LakeReader            -- injected type or call
        lake.TickerAliasMap        -- injected type or call
        data_loading.DocumentDownloader  -- metadata missing, manifest write
        lake.DocumentViews               -- view creation
        cli.DocumentCommands             -- catalog busy when refreshing document views
        portfolio.WatchlistBuilder  -- empty curated.daily, missing output directory
        lake.StatementVersionReader  -- view missing, bad dates
        risk.RiskModel  -- injected type or call
        portfolio.HoldingsRiskBuilder  -- no risk session, missing output directory
        visualization.MorningReportBuilder  -- raises it
        calculation.MacroMonitorBuilder  -- every macro table missing, missing output directory
        calculation.FuturesMonitorBuilder  -- empty fut_daily, missing output directory
        portfolio.MarginPanelBuilder  -- missing output directory
        portfolio.BuybackEventsBuilder  -- missing output directory
        portfolio.EtfCtaBook  -- no fund_daily rows, missing output directory

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """
