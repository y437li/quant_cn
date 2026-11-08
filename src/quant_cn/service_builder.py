"""Composition of pipelines, runners and readers from Config (the cli's service factory)."""

from __future__ import annotations

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.code_table_builder import CodeTableBuilder
from quant_cn.core.docs.contract_linter import ContractLinter
from quant_cn.core.docs.decisions_reader import DecisionsReader
from quant_cn.core.docs.doc_table_builder import DocTableBuilder
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.plan_reader import PlanReader
from quant_cn.core.docs.registry_reader import RegistryReader
from quant_cn.core.docs.repo_files import RepoFiles
from quant_cn.data_loading.akshare_client import AkshareClient
from quant_cn.data_loading.baostock_client import BaostockClient
from quant_cn.data_loading.cninfo_client import CninfoClient
from quant_cn.data_loading.eastmoney_report_client import EastmoneyReportClient
from quant_cn.data_loading.fetcher_factory import FetcherFactory
from quant_cn.data_loading.tushare_client import TushareClient
from quant_cn.factor.factor_evaluator import FactorEvaluator
from quant_cn.factor.factor_factory import FactorFactory
from quant_cn.factor.factor_preprocessor import FactorPreprocessor
from quant_cn.factor.signal_combiner import SignalCombiner
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.exposure_reader import ExposureReader
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.panel_cache import PanelCache
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.project_catalog import ProjectCatalog
from quant_cn.lake.run_log import RunLog
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from quant_cn.pipeline.curate_pipeline import CuratePipeline, DeriveStep
from quant_cn.pipeline.download_pipeline import DownloadPipeline
from quant_cn.pipeline.evaluation_step import EvaluationStep
from quant_cn.pipeline.feature_step import FeatureStep
from quant_cn.pipeline.runner import BaseRunner, LocalRunner
from quant_cn.pipeline.universe_step import UniverseStep
from quant_cn.statistic.block_bootstrap import BlockBootstrap
from quant_cn.statistic.hac_variance import HacVariance
from quant_cn.statistic.ic_calculator import IcCalculator
from quant_cn.statistic.ic_significance import IcSignificance
from quant_cn.statistic.multiple_testing_adjuster import MultipleTestingAdjuster
from quant_cn.statistic.neutralizer import Neutralizer
from quant_cn.statistic.quantile_returns import QuantileReturns
from quant_cn.statistic.return_stats import ReturnStats
from quant_cn.statistic.standardizer import Standardizer
from quant_cn.statistic.winsorizer import Winsorizer


class ServiceBuilder:
    """
    Purpose:
        Wire services for the CLI commands (the composition root's constructors): download and
        curate pipelines with the chosen runner, and the project catalog.

    Contract:
        Input:
            (none)
        Output:
            instance; `build_download_pipeline`, `build_curate_pipeline`, `build_features`,
            `build_evaluation`, `build_runner`,
            `build_project_catalog`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli        -- download, curate, project-catalog commands
        cli.ResearchCommands  -- injected type or call

    Test cases:
        TC-QCC-002  download --dry-run on an empty lake exits 0 and lists datasets
        TC-QCC-003  curate on a mini lake exits 0 and reports derived digests unchanged on rerun
    """

    def build_download_pipeline(
        self, config: Config, catalog: LakeCatalog, show_progress: bool, runner: str = "local"
    ) -> DownloadPipeline:
        """
        Purpose:
            DownloadPipeline wired to the lake, Tushare client and chosen runner.

        Contract:
            Input:
                config, catalog; show_progress: bool; runner: "local" | "prefect"
            Output:
                DownloadPipeline
            Raises:
                (none)
        """
        clock, codec = Clock(), DateCodec()
        writer = ParquetWriter(config.lake.root)
        fetch_log = FetchLog(catalog)
        run_log = RunLog(catalog, clock)
        calendar = TradingCalendar(LakeQuery(catalog))
        client = TushareClient(config.tushare, clock)
        factory = FetcherFactory(
            config,
            client,
            writer,
            fetch_log,
            run_log,
            clock,
            calendar,
            codec,
            extra_clients={
                "akshare": AkshareClient(clock),
                "baostock": BaostockClient(clock),
                "cninfo": CninfoClient(clock),
                "eastmoney": EastmoneyReportClient(clock),
            },
            query=LakeQuery(catalog),
        )
        executor = self.build_runner(run_log, runner, show_progress)
        return DownloadPipeline(config, factory, executor, catalog, fetch_log, clock, codec)

    def build_curate_pipeline(
        self, config: Config, catalog: LakeCatalog, show_progress: bool, runner_name: str = "local"
    ) -> CuratePipeline:
        """
        Purpose:
            CuratePipeline wired to compactor, derived views, PIT aligner and chosen runner.

        Contract:
            Input:
                config, catalog; show_progress: bool; runner_name: "local" | "prefect"
            Output:
                CuratePipeline
            Raises:
                (none)
        """
        clock, query = Clock(), LakeQuery(catalog)
        compactor = Compactor(catalog, query, ParquetWriter(config.lake.root), clock)
        views = DerivedViews(
            catalog, query, config.datasets, config.futures_categories, config.ticker_aliases
        )
        aligner = PitAligner(catalog, query, DateCodec())
        runner = self.build_runner(RunLog(catalog, clock), runner_name, show_progress)
        writer = ParquetWriter(config.lake.root)
        universe = UniverseStep(query, writer, config.universe)
        derive = DeriveStep(views, aligner, query, config.lake.root / "meta" / "manifest")
        features = (
            self.build_features(config, catalog, query, views, derive) if config.factors else None
        )
        return CuratePipeline(
            config, compactor, views, aligner, query, catalog, runner, universe, derive, features
        )

    def build_features(
        self,
        config: Config,
        catalog: LakeCatalog,
        query: LakeQuery,
        views: DerivedViews,
        derive: DeriveStep,
    ) -> FeatureStep:
        """
        Purpose:
            FeatureStep wired from config/factors.yaml (factors and campaign settings).

        Contract:
            Input:
                config; catalog; query; views; derive  -- the curate run's shared instances
            Output:
                FeatureStep
            Raises:
                (none)
        """
        camp = config.campaign
        pre = FactorPreprocessor(
            Winsorizer(k=camp.winsorize_k) if camp.winsorize_k else None,
            Standardizer() if camp.standardize else None,
            Neutralizer() if camp.neutralize else None,
        )
        weights = camp.weights or {f.name: 1.0 for f in config.factors}
        return FeatureStep(
            query,
            self.build_reader(config, catalog),
            FactorFactory(config.factors, TradingCalendar(query), DateCodec()),
            ExposureReader(query),
            pre,
            SignalCombiner(weights, Standardizer(), camp.min_factors),
            ParquetWriter(config.lake.root),
            views,
            derive,
            camp.start,
        )

    def build_runner(self, run_log: RunLog, name: str, show_progress: bool) -> BaseRunner:
        """
        Purpose:
            LocalRunner, or PrefectRunner for name "prefect" (optional extra "flows", D-022).

        Contract:
            Input:
                run_log: RunLog; name: "local" | "prefect"; show_progress: bool
            Output:
                BaseRunner
            Raises:
                ModuleNotFoundError  -- prefect requested but the "flows" extra is not installed
        """
        if name == "prefect":
            from quant_cn.pipeline import prefect_runner  # noqa: PLC0415 -- optional extra (D-022)

            return prefect_runner.PrefectRunner(run_log)
        return LocalRunner(run_log, show_progress=show_progress)

    def build_reader(self, config: Config, catalog: LakeCatalog, cache: bool = False) -> LakeReader:
        """
        Purpose:
            The lake read API (D-089): PIT aligner, alias map, calendar and an optional cache.

        Contract:
            Input:
                config: Config; catalog: LakeCatalog (read-only is fine)
                cache:  bool  -- True in notebooks (PanelCache), False in pipelines
            Output:
                LakeReader
            Raises:
                (none)
        """
        query = LakeQuery(catalog)
        return LakeReader(
            catalog,
            query,
            config.datasets,
            PitAligner(catalog, query, DateCodec()),
            TickerAliasMap(catalog, query, config.ticker_aliases),
            TradingCalendar(query),
            PanelCache() if cache else None,
        )

    def build_evaluation(self, config: Config, catalog: LakeCatalog) -> EvaluationStep:
        """
        Purpose:
            EvaluationStep for the configured campaign (2,000 seeded block-bootstrap resamples).

        Contract:
            Input:
                config: Config; catalog: LakeCatalog
            Output:
                EvaluationStep
            Raises:
                (none)
        """
        camp, query = config.campaign, LakeQuery(catalog)
        boot = BlockBootstrap(resamples=2000, seed=0)
        evaluator = FactorEvaluator(
            IcCalculator(),
            IcSignificance(HacVariance(), boot),
            MultipleTestingAdjuster(),
            QuantileReturns(5),
            ReturnStats(),
            boot,
            camp.horizons,
        )
        params: dict[str, dict[str, object]] = {f.name: dict(f.params) for f in config.factors}
        params["score"] = dict(camp.weights)
        return EvaluationStep(
            query,
            self.build_reader(config, catalog),
            evaluator,
            ParquetWriter(config.lake.root),
            camp.id,
            params,
            camp.start,
        )

    def build_project_catalog(self, config: Config, catalog: LakeCatalog) -> ProjectCatalog:
        """
        Purpose:
            ProjectCatalog over the repository with the contract linter.

        Contract:
            Input:
                config, catalog
            Output:
                ProjectCatalog
            Raises:
                (none)
        """
        root = config.repo_root
        tables, scanner = MarkdownTableReader(), CodeScanner()
        code = CodeTableBuilder(root, scanner, DocstringParser(), RegistryReader(tables))
        files = RepoFiles(root)
        docs = DocTableBuilder(
            root, files, IndexReader(tables), DecisionsReader(tables), PlanReader(tables)
        )
        return ProjectCatalog(catalog, code, docs, config.datasets, ContractLinter(root), Clock())
