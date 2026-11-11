# Class Registry

Single source of truth for every class, base class, exception, schema and allowed standalone
function in `quant_cn`. Rules: `plans/standards/CODING_STANDARD.md` §5. Maintained with the `registry` skill.

**Before writing anything new:** search this file and `grep` the codebase. Extend or subclass a match
instead of writing a duplicate.
**After creating or changing a class:** update its index row *and* its detail block in the same
change set, and add the new caller to the `Used by` of every class or method it calls.

Layers: 1 core, 2 lake, 3 data_loading, 4 pipeline/statistic, 5 back_testing/portfolio, 6 research_space.

---

## A. Index (one row per class; details in section B)

| Class | Module | Layer | Base | Purpose (one line) | Public methods (count) | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|---|
| `Black76Model` | `quant_cn.calculation.black76_model` | 4 | none | Price European options on a forward (Black-76, discounted at the continuous rate) and invert a price to implied volatility | 3 | `research_space/notebooks/20260927_vix_calculation.ipynb`, `calculation.GammaExposureCalculator` | `tests/calculation/test_black76_model.py` (TC-BM-001..004) | 2026-09-27 |
| `ExpiryClock` | `quant_cn.calculation.expiry_clock` | 4 | none | Convert (trade_date, expiry) to the time units the VIX formulas use | 3 | `calculation.VixCalculator` | `tests/calculation/test_expiry_clock.py` (TC-EC-001..003) | 2026-09-27 |
| `ForwardPriceEstimator` | `quant_cn.calculation.forward_price_estimator` | 4 | none | Per term: F = K* + e^{RT}(C - P) at the strike K* with the smallest /C - P/, and K0 the largest strike at or below F. | 1 | `calculation.VixCalculator`, `calculation.GammaExposureCalculator` | `tests/calculation/test_forward_price_estimator.py` (TC-FPE-001..002) | 2026-09-27 |
| `FuturesPositioning` | `quant_cn.calculation.futures_positioning` | 4 | none | Per trading day for one CFFEX index-futures product (IF, IH, IC, IM): total open interest and its change, the main contract's price change, the OI x price regime (new shorts, long liquidation, short covering, new longs), top-20 broker gross long / short / net summed over the product's contracts, and the main contract's basis to the index, raw and annualised to its third-Friday expiry | 3 | `research_space/notebooks/20260929_positioning_flows.ipynb` | `tests/calculation/test_futures_positioning.py` (TC-FP-001..004) | 2026-09-27 |
| `GammaExposureCalculator` | `quant_cn.calculation.gamma_exposure_calculator` | 4 | none | Estimate the gamma dealers carry per option and strike, in CNY of underlying they must trade for a 1% move: GEX = sign * Gamma_F * OI * multiplier * F^2 * 1%, with Gamma from Black-76 at each option's own implied volatility | 3 | `research_space/notebooks/20260929_positioning_flows.ipynb` | `tests/calculation/test_gamma_exposure_calculator.py` (TC-GEC-001..004) | 2026-09-27 |
| `MarginLadderEstimator` | `quant_cn.calculation.margin_ladder_estimator` | 4 | none | Estimate where margin-financed positions face forced selling | 2 | `research_space/notebooks/20260929_positioning_flows.ipynb` | `tests/calculation/test_margin_ladder_estimator.py` (TC-MLE-001..004) | 2026-09-27 |
| `OptionChainBuilder` | `quant_cn.calculation.option_chain_builder` | 4 | none | Join the option master (opt_basic) with daily prices (opt_daily) into one tidy chain per underlying, and turn one expiry of it into a strike x (call, put) quote table. | 2 | `calculation.VixCalculator`, `calculation.GammaExposureCalculator` | `tests/calculation/test_option_chain_builder.py` (TC-OCB-001..003) | 2026-09-27 |
| `RiskFreeCurve` | `quant_cn.calculation.risk_free_curve` | 4 | none | Continuously compounded risk-free rate for a tenor in calendar days, from the latest SHIBOR fixing on or before the date, linearly interpolated between tenors and clamped outside them. | 1 | `calculation.VixCalculator`, `calculation.GammaExposureCalculator` | `tests/calculation/test_risk_free_curve.py` (TC-RFC-001..003) | 2026-09-27 |
| `TermInterpolator` | `quant_cn.calculation.term_interpolator` | 4 | none | VIX = 100 * sqrt([T1 s1^2 (N2 - Nt)/(N2 - N1) + T2 s2^2 (Nt - N1)/(N2 - N1)] * Ny / Nt), with N in the clock's unit (minutes or sessions) and Ny one year in that unit. | 1 | `calculation.VixCalculator` | `tests/calculation/test_term_interpolator.py` (TC-TI-001..002) | 2026-09-27 |
| `TermSelector` | `quant_cn.calculation.term_selector` | 4 | none | Choose the two nearest expiries with at least `min_days` calendar days to expiry. | 1 | `calculation.VixCalculator` | `tests/calculation/test_term_selector.py` (TC-TS-001..002) | 2026-09-27 |
| `VarianceStripCalculator` | `quant_cn.calculation.variance_strip_calculator` | 4 | none | sigma^2 = (2/T) sum(dK/K^2 e^{RT} Q(K)) - (1/T)(F/K0 - 1)^2 over puts below K0, calls above K0 and the call/put average at K0 | 1 | `calculation.VixCalculator` | `tests/calculation/test_variance_strip_calculator.py` (TC-VSC-001..003) | 2026-09-27 |
| `VixCalculator` | `quant_cn.calculation.vix_calculator` | 4 | none | Orchestrate the white-paper steps per trading day: select near/next terms, rate per term, forward and K0, variance strip, interpolation on the chosen clock | 1 | `research_space/notebooks/20260927_vix_calculation.ipynb` | `tests/calculation/test_vix_calculator.py` (TC-VC-001..003) | 2026-09-27 |
| `CompanyCyclePanel` | `quant_cn.calculation.company_cycle_panel` | 4 | none | Place every company's latest quarter in its own cycle, point in time: single quarter and TTM, YoY and QoQ, deducted profit, 10-year median profit and max margin, margin_peak (plan 16 ph1, D-121) | 4 | (none yet) | `tests/calculation/test_company_cycle_panel.py` (TC-CCP-001..010) | 2026-11-09 |
| `QuantCnCli` | `quant_cn.cli` | 8 | none | `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup, project-catalog, query | 1 | `Makefile targets doctor, download, compact, lake-rebuild, lake-backup`, `cli.DocumentCommands` | `tests/test_cli.py` (TC-QCC-001..007) | 2026-09-27 |
| `ResearchCommands` | `quant_cn.cli` | 8 | none | The research-side CLI commands, kept apart so QuantCnCli stays within its size limit: `release-lags` (D-086), `evaluate` (factor campaign reports and trial log, plan 04 phase 5) and `watchlist` (D-120) | 1 | `cli.QuantCnCli` | `tests/test_cli.py` (TC-QCC-008..009, 011) | 2026-09-27 |
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | ABC | Abstract vendor client: one logical query returns all pages as one DataFrame. | 1 | `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | ABC | Abstract record of which (dataset, key) pairs are fully downloaded. | 5 | `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher` | `tests/lake/test_fetch_log.py` (TC-FL-001..003) | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | ABC | Download one dataset as a sequence of keys | 5 | `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`, `data_loading.DateWindowFetcher` | `tests/core/test_base_fetcher.py` (TC-BF-001..007) | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | ABC | Abstract append-only log of runs and per-key events | 3 | `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.PrefectRunner`, `data_loading.DateWindowFetcher` | `tests/lake/test_run_log.py` (TC-RL-001..001) | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | ABC | Abstract unit of pipeline work: list its units, then run and report. | 3 | `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | ABC | Abstract sink for raw fetch results and curated partitions. | 2 | `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `Clock` | `quant_cn.core.clock` | 1 | none | The single source of wall time, monotonic time and sleeping | 4 | `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.FetcherFactory`, `data_loading.PeriodSweepFetcher`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `lake.RebuildAudit`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `data_loading.RequestPacer` | `tests/core/test_clock.py` (TC-CL-001..002) | 2026-09-27 |
| `LakeConfig` | `quant_cn.core.config` | 1 | BaseModel | Where the lake lives and whether it may sit inside the repository. | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-001..001) | 2026-09-27 |
| `TushareConfig` | `quant_cn.core.config` | 1 | BaseModel | Tushare endpoint, paging, retry and rate-limit settings | 0 | `core.Config`, `data_loading.TushareClient` | `tests/core/test_config.py` (TC-C-002..002) | 2026-09-27 |
| `DownloadConfig` | `quant_cn.core.config` | 1 | BaseModel | Which datasets to download, in what order, and from which start dates (D-015b). | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-004..004) | 2026-09-27 |
| `FactorSpec` | `quant_cn.core.config` | 1 | BaseModel | One factor of config/factors.yaml: its name, implementing class and parameters. | 0 | `core.Config`, `factor.FactorFactory` | `tests/core/test_config.py` (TC-C-012..012) | 2026-09-27 |
| `CampaignConfig` | `quant_cn.core.config` | 1 | BaseModel | Settings of one factor campaign (config/factors.yaml `campaign`, plan 04 phase 5). | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-013..013) | 2026-09-27 |
| `UniverseConfig` | `quant_cn.core.config` | 1 | BaseModel | Rules of the tradeable universe per session (FACTOR_TESTING_DESIGN §11, D-054). | 0 | `core.Config`, `pipeline.UniverseStep` | `tests/core/test_config.py` (TC-C-011..011) | 2026-09-27 |
| `FuturesCategory` | `quant_cn.core.config` | 1 | BaseModel | One member-category label that `fut_holding` lists among real brokers (D-079). | 0 | `core.Config`, `lake.DerivedViews` | `tests/core/test_config.py` (TC-C-009..009) | 2026-09-27 |
| `TickerAlias` | `quant_cn.core.config` | 1 | BaseModel | One retired code and the code its company trades on afterwards (D-053, D-089). | 0 | `core.Config`, `lake.TickerAliasMap`, `lake.DerivedViews` | `tests/core/test_config.py` (TC-C-010..010) | 2026-09-27 |
| `Config` | `quant_cn.core.config` | 1 | BaseModel | The typed configuration injected everywhere: YAML defaults, machine overrides, environment. | 3 | `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `cli.ServiceBuilder`, `cli.ResearchCommands`, `cli.DocumentCommands`, `portfolio.WatchlistBuilder` | `tests/core/test_config.py` (TC-C-001..017) | 2026-09-27 |
| `WatchlistEntry` | `quant_cn.core.config` | 1 | BaseModel | One stock the user watches and the price range at which they would buy it (D-120). | 0 | `core.Config`, `portfolio.WatchlistBuilder` | `tests/core/test_config.py` (TC-C-015) | 2026-11-08 |
| `WatchlistSettings` | `quant_cn.core.config` | 1 | BaseModel | Thresholds and windows of the watchlist page (base.yaml `watchlist`, D-120). | 0 | `core.Config`, `portfolio.WatchlistBuilder` | `tests/core/test_config.py` (TC-C-016) | 2026-11-08 |
| `DiscoverySettings` | `quant_cn.core.discovery_settings` | 1 | BaseModel | Thresholds and windows of the discovery pipeline (base.yaml `discovery`, plan 16, D-121) | 0 | `core.Config`, `calculation.CompanyCyclePanel`, `calculation.ImpliedExpectations` | `tests/core/test_config.py` (TC-C-017..018) | 2026-11-09 |
| `ValuesFromDataset` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Enumerate sweep keys from another curated dataset (e.g | 0 | `core.SweepSpec` | `tests/data_loading/test_fetcher_factory.py` (TC-FF-003..003) | 2026-09-27 |
| `SweepSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | How a dataset is swept so each call returns the whole market for one key. | 1 | `core.DatasetSpec` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `CuratedSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Where a dataset lands in `curated/` and which date column drives its yearly partition. | 0 | `core.DatasetSpec` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `DatasetSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Everything the lake and the fetchers need to know about one dataset, as data (D-012). | 2 | `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.CompactStep`, `lake.DerivedViews`, `lake.ProjectCatalog`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `lake.ReleaseLagChecker`, `lake.LakeReader` | `tests/core/test_dataset_spec.py` (TC-DS-001..009) | 2026-09-27 |
| `DateCodec` | `quant_cn.core.date_codec` | 1 | none | Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps. | 6 | `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`, `data_loading.FetcherFactory`, `cli.QuantCnCli`, `lake.PitAligner`, `visualization.PriceChart`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `factor.FactorFactory` | `tests/core/test_date_codec.py` (TC-DC-001..006) | 2026-09-27 |
| `Finding` | `quant_cn.core.docs.base_checker` | 1 | none | One rule violation at a location, printable as `path:line [rule] message`. | 1 | `core.docs.BaseChecker.run`, `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter` | `tests/core/docs/test_base_checker.py` (TC-BCH-001..001) | 2026-09-27 |
| `BaseChecker` | `quant_cn.core.docs.base_checker` | 1 | ABC | Abstract repository check: inspect the tree, return findings (empty = pass). | 1 | `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter` | `tests/core/docs/test_base_checker.py` (TC-BCH-001..001) | 2026-09-27 |
| `MethodInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One function defined directly in a class body. | 2 | `core.docs.ClassInfo`, `core.docs.CodeScanner.read_module`, `core.docs.ModuleInfo` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..001) | 2026-09-27 |
| `ClassInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One top-level class: span, bases, docstring, methods and the names its body references. | 2 | `core.docs.ModuleInfo`, `core.docs.CodeScanner.read_module`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..002) | 2026-09-27 |
| `ModuleInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One scanned Python file. | 0 | `core.docs.CodeScanner.read_module`, `core.docs.ContractChecker`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..001) | 2026-09-27 |
| `CodeScanner` | `quant_cn.core.docs.code_scanner` | 1 | none | Parse Python files with `ast` into ModuleInfo records (no import, no execution). | 1 | `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..003) | 2026-09-27 |
| `CodeTableBuilder` | `quant_cn.core.docs.code_table_builder` | 1 | none | Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the code-side tables of the `project` schema, one DataFrame per table with fixed columns. | 1 | `lake.ProjectCatalog`, `cli.ServiceBuilder` | `tests/core/docs/test_code_table_builder.py` (TC-CTB-001..002) | 2026-09-27 |
| `CodeUnit` | `quant_cn.core.docs.contract_checker` | 1 | none | A class with the module it lives in and its parsed contract. | 0 | `core.docs.ContractChecker` | `tests/core/docs/test_contract_checker.py` (TC-CC-001..001) | 2026-09-27 |
| `ContractChecker` | `quant_cn.core.docs.contract_checker` | 1 | BaseChecker | Check contracts across the tree: class docstrings carry all sections and public methods Purpose + Contract | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_contract_checker.py` (TC-CC-001..005) | 2026-09-27 |
| `ContractLinter` | `quant_cn.core.docs.contract_linter` | 1 | none | Build the four checkers (contracts, index, size, names) for one repository and run the selected groups, returning all findings sorted. | 1 | `scripts/lint_contracts.py`, `tests/test_contracts.py`, `lake.ProjectCatalog`, `cli.ServiceBuilder` | `tests/test_contracts.py` (TC-CTL-001..002) | 2026-09-27 |
| `ConventionReader` | `quant_cn.core.docs.convention_reader` | 1 | none | Extract the allowed method-name verb prefixes from the naming convention's §2.1 table. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_convention_reader.py` (TC-CR-001..002) | 2026-09-27 |
| `DecisionRecord` | `quant_cn.core.docs.decisions_reader` | 1 | none | One decision: its log-table row joined with the Context and Decision bullets of its block. | 0 | `core.docs.DecisionsReader` | `tests/core/docs/test_decisions_reader.py` (TC-DR-001..001) | 2026-09-27 |
| `DecisionsReader` | `quant_cn.core.docs.decisions_reader` | 1 | none | Parse DECISIONS.md: the ID/Date/Title/Status/Where table plus `### D-NNN` detail blocks. | 1 | `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_decisions_reader.py` (TC-DR-001..002) | 2026-09-27 |
| `DocTableBuilder` | `quant_cn.core.docs.doc_table_builder` | 1 | none | Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into the document-side tables of the `project` schema. | 1 | `lake.ProjectCatalog`, `cli.ServiceBuilder` | `tests/core/docs/test_doc_table_builder.py` (TC-DTB-001..002) | 2026-09-27 |
| `UsedByEntry` | `quant_cn.core.docs.docstring_parser` | 1 | none | One line of a `Used by:` section, split into the caller reference and its note. | 0 | `core.docs.DocContract`, `core.docs.DocstringParser.parse` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001) | 2026-09-27 |
| `DocContract` | `quant_cn.core.docs.docstring_parser` | 1 | none | The parsed contract of one class, method or module docstring. | 1 | `core.docs.DocstringParser.parse`, `core.docs.CodeUnit` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001) | 2026-09-27 |
| `DocstringParser` | `quant_cn.core.docs.docstring_parser` | 1 | none | Split a contract docstring into its sections: Purpose, Contract (Input, Output, Raises), Used by, Test cases. | 1 | `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..005) | 2026-09-27 |
| `IndexChecker` | `quant_cn.core.docs.index_checker` | 1 | BaseChecker | Every visible folder has an INDEX.md whose folder and file rows equal what is on disk, and whose Contains cell for a .py file lists exactly its top-level classes (fixtures for conftest.py | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_index_checker.py` (TC-IC-001..004) | 2026-09-27 |
| `IndexEntry` | `quant_cn.core.docs.index_reader` | 1 | none | One row of an INDEX.md table: a subfolder or a file with its purpose and named contents. | 0 | `core.docs.IndexInfo`, `core.docs.IndexReader.read` | `tests/core/docs/test_index_reader.py` (TC-IR-001..001) | 2026-09-27 |
| `IndexInfo` | `quant_cn.core.docs.index_reader` | 1 | none | Parsed INDEX.md: title line, subfolder entries, file entries. | 0 | `core.docs.IndexReader.read`, `core.docs.IndexChecker`, `core.docs.DocTableBuilder` | `tests/core/docs/test_index_reader.py` (TC-IR-001..001) | 2026-09-27 |
| `IndexReader` | `quant_cn.core.docs.index_reader` | 1 | none | Parse the fixed INDEX.md format: `## Folders` (Folder, Purpose) and `## Files` (File, Purpose, Contains) tables. | 1 | `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_index_reader.py` (TC-IR-001..002) | 2026-09-27 |
| `MarkdownTable` | `quant_cn.core.docs.markdown_table` | 1 | none | One pipe table with the heading it sits under. | 1 | `core.docs.MarkdownTableReader.read` | `tests/core/docs/test_markdown_table.py` (TC-MTR-001..001) | 2026-09-27 |
| `MarkdownTableReader` | `quant_cn.core.docs.markdown_table` | 1 | none | Extract every pipe table from markdown text, and backticked names from a cell. | 2 | `core.docs.IndexReader`, `core.docs.RegistryReader`, `core.docs.ConventionReader`, `core.docs.ContractLinter`, `core.docs.DecisionsReader`, `core.docs.PlanReader`, `cli.ServiceBuilder` | `tests/core/docs/test_markdown_table.py` (TC-MTR-001..003) | 2026-09-27 |
| `NameChecker` | `quant_cn.core.docs.name_checker` | 1 | BaseChecker | Enforce names: lowercase paths (governance `UPPER_SNAKE.md` and tool files excepted), verb-first method and function names from the convention's verb table, no banned verbs, test functions named `test_tc_<id>_<desc>`, and module name matching its primary class. | 2 | `core.docs.ContractLinter` | `tests/core/docs/test_name_checker.py` (TC-NC-001..004) | 2026-09-27 |
| `PhaseRecord` | `quant_cn.core.docs.plan_reader` | 1 | none | One row of a plan's Phases table. | 0 | `core.docs.PlanRecord`, `core.docs.PlanReader.read` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..001) | 2026-09-27 |
| `PlanRecord` | `quant_cn.core.docs.plan_reader` | 1 | none | One execution plan: number, title, header fields and phases. | 0 | `core.docs.PlanReader.read` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..001) | 2026-09-27 |
| `PlanReader` | `quant_cn.core.docs.plan_reader` | 1 | none | Parse a plan file: `# NN — Title`, the two-column header table (Status, Decisions, Depends on plans) and the Phases table. | 1 | `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..002) | 2026-09-27 |
| `RegistryInfo` | `quant_cn.core.docs.registry_reader` | 1 | none | The registry's content as sets and maps the linter can compare with code. | 0 | `core.docs.RegistryReader.read`, `core.docs.ContractChecker`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_registry_reader.py` (TC-RR-001..001) | 2026-09-27 |
| `RegistryReader` | `quant_cn.core.docs.registry_reader` | 1 | none | Parse CLASS_REGISTRY.md: section A index, section B detail blocks and their method tables, and the class/schema names of sections C, D, E. | 1 | `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_registry_reader.py` (TC-RR-001..003) | 2026-09-27 |
| `RepoFiles` | `quant_cn.core.docs.repo_files` | 1 | none | The set of repository files a linter should see: `git ls-files --cached --others --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored. | 2 | `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder` | `tests/core/docs/test_repo_files.py` (TC-RF-001..003) | 2026-09-27 |
| `SizeChecker` | `quant_cn.core.docs.size_checker` | 1 | BaseChecker | Fail any .py file over 600 lines, class over 300, function or method over 50 (physical lines, docstrings included), and INDEX.md / SKILL.md / execution plan over 300 lines. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_size_checker.py` (TC-SC-001..002) | 2026-09-27 |
| `Schema` | `quant_cn.core.schema` | 1 | none | Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null. | 4 | `core.DatasetSpec.build_schema`, `lake.LakeReader` | `tests/core/test_schema.py` (TC-S-001..006) | 2026-09-27 |
| `StepReport` | `quant_cn.core.step_report` | 1 | none | Counts and status of one step (usually one dataset's fetch) so runs can be summarised. | 0 | `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `pipeline.FetchStep`, `pipeline.PipelineReport`, `pipeline.CompactStep`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `data_loading.DocumentDownloader` | `tests/core/test_base_fetcher.py` (TC-BF-001..001) | 2026-09-27 |
| `TickerNormalizer` | `quant_cn.core.ticker_normalizer` | 1 | none | Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity. | 2 | (none yet) | `tests/core/test_ticker_normalizer.py` (TC-TN-001..004) | 2026-09-27 |
| `AkshareClient` | `quant_cn.data_loading.akshare_client` | 3 | BaseApiClient | Call one AkShare function per query (`api_name` = function name, `params` = its keyword arguments) and return its frame with dates normalised to YYYYMMDD strings, so the lake's schema and PIT rules apply unchanged | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_akshare_client.py` (TC-AKC-001..002) | 2026-09-27 |
| `BaostockClient` | `quant_cn.data_loading.baostock_client` | 3 | BaseApiClient | Call one BaoStock query per request (`api_name` = method, e.g | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_baostock_client.py` (TC-BSC-001..003) | 2026-09-27 |
| `FetcherFactory` | `quant_cn.data_loading.fetcher_factory` | 3 | none | Build the right fetcher for a DatasetSpec and inject the shared dependencies. | 1 | `pipeline.DownloadPipeline`, `cli.ServiceBuilder` | `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..004) | 2026-09-27 |
| `SingleCallFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets fetched in one (paged) call, key "all": trade_cal, namechange. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-SCF-001..001) | 2026-09-27 |
| `EnumFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily / fund_daily by ts_code, opt_basic by exchange. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-EF-001..001) | 2026-09-27 |
| `DateSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market daily sweeps: trade_date and nav_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit, fund_nav) | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-DSF-001..005) | 2026-09-27 |
| `PeriodSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-PSF-001..001) | 2026-09-27 |
| `DateWindowFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Range-only endpoints swept by calendar window (D-063): one call per month ("YYYYMM" keys) or year ("YYYY" keys) with start_date / end_date clipped to the run range | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-DWF-001..004) | 2026-09-27 |
| `HttpTransport` | `quant_cn.data_loading.http_transport` | 3 | none | Send one HTTP request and return the decoded JSON object or the raw bytes (JSON POST, form POST, GET JSON, GET bytes). | 4 | `data_loading.TushareClient`, `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`, `data_loading.BaseWebClient`, `data_loading.DocumentDownloader` | `tests/data_loading/test_tushare_client.py`, `test_http_transport.py` (TC-TC-001, TC-HT-001) | 2026-09-27 |
| `TushareClient` | `quant_cn.data_loading.tushare_client` | 3 | BaseApiClient | Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows | 1 | `cli.ServiceBuilder` | `tests/data_loading/test_tushare_client.py` (TC-TC-001..009) | 2026-09-27 |
| `FactorInputs` | `quant_cn.factor.base_factor` | 5 | none | The panels a factor may read, loaded once by FactorFactory for all factors of a run | 1 | `factor.BaseFactor`, `factor.FactorFactory`, `factor.library.EarningsYieldFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor` | `tests/factor/test_base_factor.py` (TC-FIN-001..001) | 2026-09-27 |
| `BaseFactor` | `quant_cn.factor.base_factor` | 5 | ABC | Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it needs and how many sessions of price history before the first output date | 3 | `factor.FactorFactory`, `factor.library.*`, `factor.library.EarningsYieldFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor`, `pipeline.FeatureStep` | `tests/factor/test_base_factor.py` (TC-BFA-001..002) | 2026-09-27 |
| `FactorAcceptance` | `quant_cn.factor.factor_acceptance` | 5 | none | Criteria 1-3 of FACTOR_TESTING_DESIGN §6 per factor at one horizon, from the campaign's IC_TEST: (1) NW t of the full-window mean IC >= t_min (HLZ) and BHY-adjusted p <= alpha | 1 | `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder` | `tests/factor/test_factor_acceptance.py` (TC-FA-001..003) | 2026-09-27 |
| `FactorReport` | `quant_cn.factor.factor_evaluator` | 5 | none | The evaluation of one campaign: IC series, every test result, quantile ladders. | 0 | `factor.FactorEvaluator` | `tests/factor/test_factor_evaluator.py` (TC-FEV-001..001) | 2026-09-27 |
| `FactorEvaluator` | `quant_cn.factor.factor_evaluator` | 5 | none | Evaluate every factor of a campaign (FACTOR_TESTING_DESIGN §2, §3, §6): tradeable forward returns from the open of t+1, IC series per horizon, the IcSignificance tests, decay across horizons (half-life), rank autocorrelation (turnover proxy), quantile ladders and long-short statistics on non-overlapping samples, then the campaign-level Holm / BHY / Romano-Wolf adjustment and HLZ flag over all factor x horizon mean-IC tests | 2 | `notebooks`, `pipeline.EvaluationStep`, `cli.ServiceBuilder` | `tests/factor/test_factor_evaluator.py` (TC-FEV-001..003) | 2026-09-27 |
| `FactorFactory` | `quant_cn.factor.factor_factory` | 5 | none | Resolve config/factors.yaml entries to BaseFactor instances (every module under factor/library/ is imported so its classes register themselves | 2 | `notebooks`, `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/factor/test_factor_factory.py` (TC-FAF-001..003) | 2026-09-27 |
| `FactorPreprocessor` | `quant_cn.factor.factor_preprocessor` | 5 | none | The ordered chain applied to every raw factor, each step optional and logged: winsorise (median +- k * 1.4826 * MAD per date) -> standardise (z per date) -> neutralise (per-date OLS residual on Shenwan L1 dummies and log market cap, D-093) -> standardise again, so the processed value is a unit-dispersion, industry- and size-neutral z-score | 2 | `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/factor/test_factor_preprocessor.py` (TC-FPP-001..002) | 2026-09-27 |
| `EarningsYieldFactor` | `quant_cn.factor.library.earnings_yield_factor` | 5 | BaseFactor | Earnings yield EP_TTM = net profit attributable to parent over the trailing twelve months (PIT, D-092) / total market value at the close of t | 1 | (none yet) | `tests/factor/test_fundamental_factors.py` (TC-EYF-001..001) | 2026-09-27 |
| `MomentumFactor` | `quant_cn.factor.library.momentum_factor` | 5 | BaseFactor | MOM_{12-1} = P_adj(t - skip) / P_adj(t - window) - 1 on the backward-adjusted close (ratios are PIT-safe, FACTOR_TESTING_DESIGN §11), skipping the most recent month to avoid the short-term reversal (Jegadeesh & Titman 1993) | 2 | (none yet) | `tests/factor/test_price_factors.py` (TC-MOM-001..001) | 2026-09-27 |
| `ProfitGrowthFactor` | `quant_cn.factor.library.profit_growth_factor` | 5 | BaseFactor | Growth = (NI_TTM(P) - NI_TTM(P - 1 year)) / /NI_TTM(P - 1 year)/ for the latest PIT-visible period P, both TTMs from the versions known at the announcement (the lake's `n_income_attr_p_ttm_yoy`, D-092) | 1 | (none yet) | `tests/factor/test_fundamental_factors.py` (TC-PGF-001..001) | 2026-09-27 |
| `ReversalFactor` | `quant_cn.factor.library.reversal_factor` | 5 | BaseFactor | REV = -(P_adj(t) / P_adj(t - window) - 1): last month's losers tend to rebound, strongly so in China's retail-driven market (Jegadeesh 1990 | 2 | (none yet) | `tests/factor/test_price_factors.py` (TC-REV-001..001) | 2026-09-27 |
| `RoeFactor` | `quant_cn.factor.library.roe_factor` | 5 | BaseFactor | Return on equity ROE_TTM = net profit attributable to parent over the trailing twelve months / equity attributable to parent in the latest PIT-visible balance sheet (both D-092 PIT) | 1 | (none yet) | `tests/factor/test_fundamental_factors.py` (TC-ROE-001..001) | 2026-09-27 |
| `TurnoverFactor` | `quant_cn.factor.library.turnover_factor` | 5 | BaseFactor | TURN = -mean(turnover_rate_f over the last `window` sessions, at least `min_obs` traded): heavily traded stocks underperform, a liquidity / attention effect that is strong in China (Datar, Naik & Radcliffe 1998 | 2 | (none yet) | `tests/factor/test_price_factors.py` (TC-TRN-001..001) | 2026-09-27 |
| `SignalCombiner` | `quant_cn.factor.signal_combiner` | 5 | none | score_{i,t} = sum_f w_f z_{f,i,t} / sum_{f available} /w_f/ over the processed factors a stock has at t (at least `min_factors`), then standardised per date: an equal-risk blend of z-scores that tolerates a missing factor instead of dropping the stock. | 1 | `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/factor/test_signal_combiner.py` (TC-SGC-001..002) | 2026-09-27 |
| `Compactor` | `quant_cn.lake.compactor` | 2 | none | Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, fill `key_defaults` into NULL key columns, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`. | 1 | `cli.QuantCnCli`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `cli.ServiceBuilder` | `tests/lake/test_compactor.py` (TC-CO-001..006) | 2026-09-27 |
| `DerivedViews` | `quant_cn.lake.derived_views` | 2 | none | Create the `derived` schema views built only from curated/: `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor | 2 | `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `pipeline.FeatureStep` | `tests/lake/test_derived_views.py` (TC-DV-001..010) | 2026-09-27 |
| `EffectiveDateResolver` | `quant_cn.lake.effective_date_resolver` | 2 | none | Turn a dataset's `known_on` value into `effective_date`, the first China trading session the row may be used (FACTOR_TESTING_DESIGN §11): as_is          -> that session, or the next one if the day is closed (same-day data) | 2 | (none yet) | `tests/lake/test_effective_date_resolver.py` (TC-EDR-001..006) | 2026-09-27 |
| `ExposureReader` | `quant_cn.lake.exposure_reader` | 2 | none | Per universe member and session: the Shenwan L1 group in effect (derived.industry_l1, l1_grouping = the PIT row or the back-filled first-known L1, flagged | 1 | `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/lake/test_lake_reader.py` (TC-EXR-001..001) | 2026-09-27 |
| `FetchLog` | `quant_cn.lake.fetch_log` | 2 | BaseFetchLog | Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost. | 6 | `cli.QuantCnCli`, `cli.ServiceBuilder` | `tests/lake/test_fetch_log.py` (TC-FL-001..006) | 2026-09-27 |
| `LakeCatalog` | `quant_cn.lake.lake_catalog` | 2 | none | Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta` | 8 | `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `lake.QualityViews`, `lake.LakeReader`, `lake.TickerAliasMap`, `cli.ResearchCommands`, `cli.DocumentCommands` | `tests/lake/test_lake_catalog.py` (TC-LC-001..005) | 2026-09-27 |
| `LakeQuery` | `quant_cn.lake.lake_query` | 2 | none | Run read queries against the catalog views | 5 | `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `cli.ServiceBuilder`, `data_loading.FetcherFactory`, `lake.QualityViews`, `lake.ReleaseLagChecker`, `lake.LakeReader`, `lake.TickerAliasMap`, `pipeline.UniverseStep`, `lake.ExposureReader`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `portfolio.WatchlistBuilder` | `tests/lake/test_lake_query.py` (TC-LQ-001..005) | 2026-09-27 |
| `LakeReader` | `quant_cn.lake.lake_reader` | 2 | none | The read API factors, the universe step and notebooks use (SRC_DESIGN §2.2b, D-089): one curated dataset as a panel, dense or sparse prices, point-in-time fundamentals, reference tables (in-memory frames and view discovery: LakeQuery) | 5 | `cli.ServiceBuilder`, (none yet), `factor.FactorFactory`, `pipeline.EvaluationStep`, `pipeline.FeatureStep` | `tests/lake/test_lake_reader.py` (TC-LRD-001..007) | 2026-09-27 |
| `PanelCache` | `quant_cn.lake.panel_cache` | 2 | none | Keep recently read panels in memory, keyed by (method, arguments), least recently used evicted first once the total size exceeds `max_bytes` | 4 | `lake.LakeReader`, `cli.ServiceBuilder` | `tests/lake/test_panel_cache.py` (TC-PCH-001..003) | 2026-09-27 |
| `ParquetWriter` | `quant_cn.lake.parquet_writer` | 2 | BaseStore | Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file. | 6 | `cli.QuantCnCli`, `cli.ServiceBuilder`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep` | `tests/lake/test_parquet_writer.py` (TC-PW-001..008) | 2026-09-27 |
| `PitAligner` | `quant_cn.lake.pit_aligner` | 2 | none | Align fundamentals to trading days without look-ahead | 2 | `pipeline.CuratePipeline`, `research_space/main.ipynb`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `lake.LakeReader` | `tests/lake/test_pit_aligner.py` (TC-PAD-001..003) | 2026-09-27 |
| `ProjectCatalog` | `quant_cn.lake.project_catalog` | 2 | none | Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings, plus views tree, class_graph, stale and todo | 1 | `cli.ServiceBuilder` | `tests/lake/test_project_catalog.py` (TC-PJC-001..004) | 2026-09-27 |
| `QualityViews` | `quant_cn.lake.quality_views` | 2 | none | Create the `quality` schema: cross-source comparisons that report, never overwrite (D-065) | 1 | `lake.DerivedViews.refresh` | `tests/lake/test_quality_views.py` (TC-QV-001..003) | 2026-09-27 |
| `RebuildAudit` | `quant_cn.lake.rebuild_audit` | 2 | none | Record, on `rebuild`, what changed below raw/ since the last one | 2 | `cli.QuantCnCli` | `tests/lake/test_rebuild_audit.py` (TC-RA-001..002) | 2026-09-27 |
| `WatchlistBuilder` | `quant_cn.portfolio.watchlist_builder` | 5 | none | Join the user's buy targets with the latest lake prices, valuation and broker consensus; compute the gap to the buy price, status and valuation at that price (plan 15 ph7, D-120) | 3 | `cli.ResearchCommands` | `tests/portfolio/test_watchlist_builder.py` (TC-WB-001..009) | 2026-11-08 |
| `ReleaseLagChecker` | `quant_cn.lake.release_lag_checker` | 2 | none | For every dataset with `known_on_rule: period_end_lag` and `release_dates` set, measure the observed lag (release date - period end) in that curated release-date dataset and count releases that came later than the rule | 2 | `cli.ResearchCommands` | `tests/lake/test_release_lag_checker.py` (TC-RLC-001..003) | 2026-09-27 |
| `RunLog` | `quant_cn.lake.run_log` | 2 | BaseRunLog | Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging. | 3 | `cli.QuantCnCli`, `cli.ServiceBuilder`, `cli.ResearchCommands` | `tests/lake/test_run_log.py` (TC-RL-001..002) | 2026-09-27 |
| `TickerAliasMap` | `quant_cn.lake.ticker_alias_map` | 2 | none | Map retired codes to their surviving codes so a company has one history | 4 | `lake.DerivedViews`, `lake.LakeReader`, `cli.ServiceBuilder` | `tests/lake/test_ticker_alias_map.py` (TC-TAM-001..004) | 2026-09-27 |
| `StatementVersionReader` | `quant_cn.lake.statement_version_reader` | 2 | none | Statement values per (company, period, field) as known on a date: latest known_on <= as_of, retired codes mapped (plan 16 ph1) | 1 | (none yet) | `tests/lake/test_statement_version_reader.py` (TC-SVR-001..004) | 2026-11-09 |
| `TradingCalendar` | `quant_cn.lake.trading_calendar` | 2 | none | Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake | 5 | `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.ServiceBuilder`, `lake.EffectiveDateResolver`, `lake.LakeReader`, `factor.FactorFactory` | `tests/lake/test_trading_calendar.py` (TC-TCA-001..004) | 2026-09-27 |
| `CompactStep` | `quant_cn.pipeline.curate_pipeline` | 6 | BaseStep | Adapt Compactor to a pipeline step: one unit per dataset. | 3 | `pipeline.CuratePipeline` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..001) | 2026-09-27 |
| `DeriveStep` | `quant_cn.pipeline.curate_pipeline` | 6 | BaseStep | Build the derived views and the PIT states view, then record a digest per derived view. | 5 | `pipeline.CuratePipeline`, `pipeline.FeatureStep`, `cli.ServiceBuilder` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..004) | 2026-09-27 |
| `CuratePipeline` | `quant_cn.pipeline.curate_pipeline` | 6 | none | Rebuild everything below raw/: compact every dataset, create derived views and PIT states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json. | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..003) | 2026-09-27 |
| `FetchStep` | `quant_cn.pipeline.download_pipeline` | 6 | BaseStep | Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the calendar fetched earlier in the run is visible), catalog view refreshed after the run. | 3 | `pipeline.DownloadPipeline.run` | `tests/pipeline/test_download_pipeline.py` (TC-DP-002..002) | 2026-09-27 |
| `DownloadPipeline` | `quant_cn.pipeline.download_pipeline` | 6 | none | Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_download_pipeline.py` (TC-DP-001..007) | 2026-09-27 |
| `EvaluationStep` | `quant_cn.pipeline.evaluation_step` | 6 | BaseStep | Evaluate every factor in derived.features (FactorEvaluator, one factor at a time to bound memory, forward returns from the open of t+1 on dense prices), apply the campaign-level adjustment once over all factor x horizon tests, and write derived/reports/<campaign>/ ic_series, ic_test and quantiles | 3 | `cli.ServiceBuilder` | `tests/pipeline/test_evaluation_step.py` (TC-ES-001..002) | 2026-09-27 |
| `FeatureStep` | `quant_cn.pipeline.feature_step` | 6 | BaseStep | Build derived/features, one file per year from the campaign start: the six library factors (FactorFactory, PIT inputs from LakeReader), restricted to universe members, preprocessed (winsorise -> standardise -> neutralise on Shenwan L1 + log market cap, D-093) and the combined "score" (SignalCombiner), as FACTOR_PANEL | 3 | `cli.ServiceBuilder` | `tests/pipeline/test_feature_step.py` (TC-FS-001..002) | 2026-09-27 |
| `PrefectRunner` | `quant_cn.pipeline.prefect_runner` | 6 | BaseRunner | Same contract as LocalRunner, executed as a Prefect flow named "quant_cn <kind>" whose run name is the RunLog run id | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_prefect_runner.py` (TC-PFR-001..003) | 2026-09-27 |
| `PipelineReport` | `quant_cn.pipeline.runner` | 6 | none | Result of one pipeline run: its id, overall status and one StepReport per step. | 2 | `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.BaseRunner`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 6 | ABC | Extension point for how steps are executed (local now, Prefect later, D-022) | 1 | `pipeline.LocalRunner`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner`, `cli.ServiceBuilder` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `LocalRunner` | `quant_cn.pipeline.runner` | 6 | BaseRunner | Run steps serially in this process with a rich progress bar per step | 1 | `cli.ServiceBuilder` | `tests/pipeline/test_runner.py` (TC-LR-001..003) | 2026-09-27 |
| `UniverseStep` | `quant_cn.pipeline.universe_step` | 6 | BaseStep | Build UNIVERSE_PANEL: one row per stock listed on each session (list_date <= t < delist_date | 3 | `cli.ServiceBuilder` | `tests/core/docs/test_contract_checker.py`, `tests/pipeline/test_universe_step.py` (TC-US-001..004) | 2026-09-27 |
| `ServiceBuilder` | `quant_cn.service_builder` | 8 | none | Wire services for the CLI commands (the composition root's constructors): download and curate pipelines with the chosen runner, and the project catalog. | 7 | `cli.QuantCnCli`, `cli.ResearchCommands` | `tests/test_cli.py` (TC-QCC-002..003) | 2026-09-27 |
| `BlockBootstrap` | `quant_cn.statistic.block_bootstrap` | 4 | none | Resample a time series (or several aligned series with the same draws) in blocks so serial correlation survives: stationary bootstrap with geometric block lengths (Politis & Romano 1994) or circular block bootstrap with fixed blocks (Politis & Romano 1992) | 4 | `statistic.IcSignificance`, `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_block_bootstrap.py` (TC-BB-001..004) | 2026-09-27 |
| `HacVariance` | `quant_cn.statistic.hac_variance` | 4 | none | Heteroskedasticity- and autocorrelation-consistent variance of a sample mean with the Bartlett kernel (Newey & West 1987 | 4 | `statistic.IcSignificance`, `cli.ServiceBuilder` | `tests/statistic/test_hac_variance.py` (TC-HAC-001..004) | 2026-09-27 |
| `IcCalculator` | `quant_cn.statistic.ic_calculator` | 4 | none | Per-date information coefficient between factor values and forward returns across the universe: IC_t = corr_rank(f_{i,t}, r_{i,t->t+h}) (Spearman | 2 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_ic_calculator.py` (TC-ICC-001..004) | 2026-09-27 |
| `IcSignificance` | `quant_cn.statistic.ic_significance` | 4 | none | The §2 tests for one factor at one horizon: Newey-West t on mean IC (Newey & West 1987, 1994, prewhitened per D-090), stationary block-bootstrap CI of mean IC and ICIR (Politis & Romano 1994), Fisher-z / Stouffer screen, sign consistency per sub-period, single break in mean (Bai & Perron 1998 | 4 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_ic_significance.py` (TC-ICS-001..005) | 2026-09-27 |
| `MultipleTestingAdjuster` | `quant_cn.statistic.multiple_testing_adjuster` | 4 | none | Adjust the p-values of many factor tests run in one campaign: Holm step-down FWER (Holm 1979), Benjamini-Hochberg FDR (1995), Benjamini-Hochberg-Yekutieli FDR under arbitrary dependence (2001), Romano-Wolf bootstrap step-down FWER (Romano & Wolf 2005, 2016), and the Harvey-Liu-Zhu (2016) /t/ >= 3.0 hurdle | 5 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_multiple_testing_adjuster.py` (TC-MTA-001..005) | 2026-09-27 |
| `Neutralizer` | `quant_cn.statistic.neutralizer` | 4 | none | Remove what industry membership and numeric exposures (e.g | 1 | `factor.FactorPreprocessor`, `cli.ServiceBuilder` | `tests/statistic/test_neutralizer.py` (TC-NEU-001..002) | 2026-09-27 |
| `QuantileReturns` | `quant_cn.statistic.quantile_returns` | 4 | none | Sort names into n quantiles of the factor within each date and horizon, and report each quantile's equal-weighted mean forward return plus the long-short spread (top minus bottom, stored as quantile 0): the monotone "ladder" that complements the IC. | 1 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_quantile_returns.py` (TC-QR-001..002) | 2026-09-27 |
| `ReturnStats` | `quant_cn.statistic.return_stats` | 4 | none | Summarise a series of period returns: annualised mean and volatility, Sharpe (per period and annualised with sqrt(244 / h)), maximum drawdown of the compounded path, hit rate, skewness and non-excess kurtosis (the PSR / DSR inputs of Bailey & López de Prado 2012). | 1 | `factor.FactorEvaluator`, `cli.ServiceBuilder` | `tests/statistic/test_return_stats.py` (TC-RS-001..002) | 2026-09-27 |
| `Standardizer` | `quant_cn.statistic.standardizer` | 4 | none | Put factor values on a common scale within each date: z = (x - m) / s with m the equal-weighted mean (or a weighted mean, e.g | 1 | `factor.FactorPreprocessor`, `factor.SignalCombiner`, `cli.ServiceBuilder` | `tests/statistic/test_standardizer.py` (TC-STD-001..002) | 2026-09-27 |
| `TrialLog` | `quant_cn.statistic.trial_log` | 4 | none | Record every factor / parameter / horizon variant evaluated in a campaign, including the failures, because the deflated Sharpe ratio (Bailey & López de Prado 2014) and the multiple-testing adjusters need the number and dispersion of all trials, not just the winners | 5 | `factor.FactorEvaluator`, `pipeline.EvaluationStep` | `tests/statistic/test_trial_log.py` (TC-TL-001..004) | 2026-09-27 |
| `Winsorizer` | `quant_cn.statistic.winsorizer` | 4 | none | Clip extreme factor values within each date so a few outliers do not dominate ranks, z-scores or regressions: median +- k * 1.4826 * MAD (robust default) or the q / 1 - q cross-sectional quantiles. | 1 | `factor.FactorPreprocessor`, `cli.ServiceBuilder` | `tests/statistic/test_winsorizer.py` (TC-WZ-001..002) | 2026-09-27 |
| `BaseChart` | `quant_cn.visualization.base_chart` | 7 | ABC | Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages) | 4 | `visualization.PriceChart`, `visualization.FactorChart` | `tests/visualization/test_charts.py` (TC-BCA-001..002) | 2026-09-27 |
| `ChartTheme` | `quant_cn.visualization.chart_theme` | 7 | none | The colour and font tokens every chart reads, so charts are written against roles, never raw hex | 1 | `visualization.BaseChart`, `visualization.PriceChart`, `visualization.FactorChart` | `tests/visualization/test_charts.py` (TC-CT-001..001) | 2026-09-27 |
| `FactorChart` | `quant_cn.visualization.factor_chart` | 7 | BaseChart | The four views of a factor campaign (plan 04 phase 6), one single-series chart each so identity never rests on colour: "ic_series" (IC_SERIES) the rolling mean IC of one factor and horizon with a band of +/- 1.96 sd / sqrt(window / h), the effective number of non-overlapping observations | 1 | `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder` | `tests/visualization/test_factor_chart.py` (TC-FC-001..004) | 2026-09-27 |
| `PriceChart` | `quant_cn.visualization.price_chart` | 7 | BaseChart | Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one ticker | 1 | `research_space/main.ipynb` | `tests/visualization/test_charts.py` (TC-PC-001..003) | 2026-09-27 |
| `DocumentRule` | `quant_cn.core.document_source` | 1 | BaseModel | One title rule: a title matching `include` and not `exclude` (regular expressions) is a document of `doc_type` | 0 | `core.DocumentSource`, `data_loading.DocumentClassifier` | `tests/core/test_document_source.py` (TC-DSR-001..001) | 2026-11-07 |
| `DocumentSource` | `quant_cn.core.document_source` | 1 | BaseModel | One document source of config/documents.yaml: the curated metadata dataset listing the documents, its key columns, the PDF URL and file-name templates (`{column}` placeholders), the folder under `documents/`, and how a row gets its doc type (a fixed `doc_type` or title `rules`, first match wins) | 0 | `core.Config`, `data_loading.DocumentClassifier`, `data_loading.DocumentDownloader` | `tests/core/test_document_source.py` (TC-DSR-001..002) | 2026-11-07 |
| `DocumentViews` | `quant_cn.lake.document_views` | 2 | none | Expose the document manifest in the catalog. | 1 | `lake.LakeCatalog.refresh_views`, `cli.DocumentCommands` | `tests/lake/test_document_views.py` (TC-DOV-001..001) | 2026-11-07 |
| `RequestPacer` | `quant_cn.data_loading.request_pacer` | 3 | none | Run one request callable at a time-spaced rate with retries: request starts are at least `min_interval_s` apart across all threads sharing the pacer, and a call raising OSError, ValueError or KeyError is retried after `retry_sleep_s` up to `retries` times | 2 | `data_loading.BaseWebClient`, `data_loading.DocumentDownloader` | `tests/data_loading/test_document_downloader.py` (TC-RP-001..002) | 2026-11-07 |
| `BaseWebClient` | `quant_cn.data_loading.base_web_client` | 3 | BaseApiClient | Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). | 1 | `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient` | `tests/data_loading/test_web_clients.py` (TC-BWC-001..002) | 2026-11-07 |
| `CninfoClient` | `quant_cn.data_loading.cninfo_client` | 3 | BaseWebClient | List CNINFO announcements for the whole A-share market (`column=szse` covers SZ, SH and BJ) over a date range, optionally one category (e.g. | 2 | `cli.ServiceBuilder` | `tests/data_loading/test_web_clients.py` (TC-CNC-001..003) | 2026-11-07 |
| `EastmoneyReportClient` | `quant_cn.data_loading.eastmoney_report_client` | 3 | BaseWebClient | List Eastmoney (东方财富) broker research reports published in a date range for one report kind (`q_type` "0" stock, "1" industry, "2" strategy), following `pageNo` until `TotalPage`. | 2 | `cli.ServiceBuilder` | `tests/data_loading/test_web_clients.py` (TC-EMR-001..002) | 2026-11-07 |
| `DocumentClassifier` | `quant_cn.data_loading.document_classifier` | 3 | none | Give each listed document its type: the source's fixed `doc_type`, or the first title rule whose `include` matches and whose `exclude` does not (e.g. | 1 | `data_loading.DocumentDownloader` | `tests/data_loading/test_document_downloader.py` (TC-DCL-001..002) | 2026-11-07 |
| `DocumentDownloader` | `quant_cn.data_loading.document_downloader` | 3 | none | Download the PDFs listed in a document source's curated metadata (config/documents.yaml) into `documents/<folder>/<doc_type>/<YYYY>/<MM>/<file>` (D-101). | 3 | `cli.DocumentCommands` | `tests/data_loading/test_document_downloader.py` (TC-DD-001..004) | 2026-11-07 |
| `DocumentCommands` | `quant_cn.cli` | 8 | none | The document-side CLI command `download-docs` (plan 12 phase 2, D-101): for each source, print candidate counts per doc type (`--dry-run`) or download the PDFs not yet in the manifest and print the outcome | 1 | `cli.QuantCnCli` | `tests/test_cli.py` (TC-QCC-010..010) | 2026-11-07 |
| `ReportPages` | `quant_cn.quant_cn.industry_graph.pdf_text_extractor` | 4 | none | The text of one report PDF, page by page, plus its outline (bookmarks) when present. | 1 | `industry_graph.PdfTextExtractor`, `industry_graph.SectionDetector`, `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..001) | 2026-11-07 |
| `PdfTextExtractor` | `quant_cn.quant_cn.industry_graph.pdf_text_extractor` | 4 | none | Read the native text layer of a PDF page by page (no OCR; D-102) and remove the running header and footer: a line with at least four letters or CJK characters that, with digits ignored, appears on at least `header_share` of the pages (e.g. | 2 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..003) | 2026-11-07 |
| `Section` | `quant_cn.quant_cn.industry_graph.section_detector` | 4 | none | One located section: its key, the heading-matched start page and the page before the next section (or the chapter end), 1-based, inclusive. | 0 | `industry_graph.SectionDetector`, `industry_graph.ParsedReport` | `tests/industry_graph/test_report_parsing.py` (TC-SD-001..001) | 2026-11-07 |
| `SectionDetector` | `quant_cn.quant_cn.industry_graph.section_detector` | 4 | none | Locate the MD&A chapter (管理层讨论与分析, 第三节 in the 2021 standard; 第二节/第四节 in older or exchange-specific layouts; 第二章 董事会报告 for A+H; BSE 业务概要 / 第五节 重大事件) and the chain sections inside it by heading text, not by number. | 3 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-SD-001..005) | 2026-11-07 |
| `CounterpartyRow` | `quant_cn.quant_cn.industry_graph.counterparty_table_parser` | 4 | none | One ranked customer or supplier of a top-5 table. | 1 | `industry_graph.CounterpartyTable`, `industry_graph.CounterpartyTableParser` | `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..001) | 2026-11-07 |
| `CounterpartyTable` | `quant_cn.quant_cn.industry_graph.counterparty_table_parser` | 4 | none | The top-5 customers or suppliers of one report: stated totals and the ranked rows (empty when only the totals sentence is disclosed, as on the SSE main board). | 1 | `industry_graph.CounterpartyTableParser`, `industry_graph.ParsedReport` | `tests/industry_graph/test_report_parsing.py` (TC-CTP-004..004) | 2026-11-07 |
| `CounterpartyTableParser` | `quant_cn.quant_cn.industry_graph.counterparty_table_parser` | 4 | none | Parse the "主要销售客户和主要供应商情况" block into a customer and a supplier CounterpartyTable. | 1 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..010) | 2026-11-07 |
| `ParsedReport` | `quant_cn.quant_cn.industry_graph.annual_report_parser` | 4 | none | What the rule-based pass extracts from one annual report. | 1 | `industry_graph.AnnualReportParser` | `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..001) | 2026-11-07 |
| `AnnualReportParser` | `quant_cn.quant_cn.industry_graph.annual_report_parser` | 4 | none | Run the rule-based pass of plan 12 phase 3 on one annual report: read the pages (PdfTextExtractor), locate the MD&A chapter and chain sections (SectionDetector), and parse the top-5 customer and supplier tables (CounterpartyTableParser). | 2 | `research_space` | `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..003) | 2026-11-07 |
| `LlmReply` | `quant_cn.quant_cn.core.base_llm_client` | 1 | none | One LLM answer as parsed JSON, with the model and token usage, and whether it came from the response cache (a cached reply costs nothing and makes rebuilds deterministic). | 0 | `core.BaseLlmClient`, `data_loading.DeepSeekClient` | `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..001) | 2026-11-07 |
| `BaseLlmClient` | `quant_cn.quant_cn.core.base_llm_client` | 1 | ABC | Abstract chat-completion client that returns a JSON object: one system prompt, one user message, an optional model override. | 1 | `data_loading.DeepSeekClient`, `industry_graph.ApplicationExtractor` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-11-07 |
| `LlmConfig` | `quant_cn.quant_cn.core.config` | 1 | BaseModel | The LLM endpoint used for extraction (D-098): OpenAI-compatible chat completions URL, default model, limits, and the API key, which comes from env DEEPSEEK_API_KEY only. | 0 | `core.Config`, `data_loading.DeepSeekClient` | `tests/core/test_config.py` (TC-C-014..014) | 2026-11-07 |
| `DeepSeekClient` | `quant_cn.quant_cn.data_loading.deep_seek_client` | 3 | BaseLlmClient | Call the DeepSeek (OpenAI-compatible) chat-completions endpoint with JSON output and temperature 0 and model reasoning off unless LlmConfig.thinking, paced and retried by RequestPacer. | 4 | `research_space` | `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..003) | 2026-11-07 |
| `Evidence` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | none | A verbatim quote and the page it was found on (after the quote check). | 0 | `industry_graph.ApplicationResult` | `tests/industry_graph/test_application_extractor.py` (TC-AE-002..002) | 2026-11-07 |
| `ApplicationResult` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | none | What the model found in one report, after validation: per revenue line the downstream applications (taxonomy node or proposed name, main/secondary, evidence) and customer types; named counterparties with role and evidence; and the items dropped because their quote was not in the text. | 0 | `industry_graph.ApplicationExtractor` | `tests/industry_graph/test_application_extractor.py` (TC-AE-001..001) | 2026-11-07 |
| `ApplicationExtractor` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | none | Send the business / industry pages of one report, its revenue lines and the candidate downstream taxonomy nodes to the LLM, and keep only answers whose verbatim quote is found in the supplied pages (whitespace ignored). | 1 | `research_space` | `tests/industry_graph/test_application_extractor.py` (TC-AE-001..003) | 2026-11-07 |
| `ApplicationItem` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | One downstream application of a revenue line as the LLM returned it. | 0 | `industry_graph.LineItem` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `LineItem` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | One revenue line with its applications and customer types as returned. | 0 | `industry_graph.ApplicationReply` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `CounterpartyItem` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | One company named in the text, with its role, as returned. | 0 | `industry_graph.ApplicationReply` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `ApplicationReply` | `quant_cn.quant_cn.industry_graph.application_extractor` | 4 | BaseModel | The whole LLM reply of one report, validated before the quote check. | 0 | `industry_graph.ApplicationExtractor` | `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003) | 2026-11-07 |
| `QuoteChecker` | `quant_cn.quant_cn.industry_graph.quote_checker` | 4 | none | Hold the pages sent to an LLM and accept a returned quote only if it occurs verbatim (whitespace ignored) on one of them. | 2 | `industry_graph.ApplicationExtractor`, `industry_graph.ValuationExtractor` | `tests/industry_graph/test_valuation_extractor.py` (TC-QC-001..002) | 2026-11-07 |
| `ValuationItem` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | BaseModel | Base of the reply shapes: unknown keys ignored, so a richer reply still validates. | 0 | `industry_graph.ValuationReply` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003) | 2026-11-07 |
| `ValuationReply` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | ValuationItem | The LLM reply for one broker report, before the quote check: rating, target price, methods (multiple, implied or target, base year), forecasts, comparables, assumptions. | 0 | `industry_graph.ValuationExtractor` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003) | 2026-11-07 |
| `ValuationResult` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | none | One report's valuation after validation: only quote-checked target price, methods and assumptions; methods carry `multiple_kind` (D-109) and a base year; comparables carry a ts_code when it could be resolved. | 0 | `industry_graph.ValuationExtractor` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..001) | 2026-11-07 |
| `ValuationExtractor` | `quant_cn.quant_cn.industry_graph.valuation_extractor` | 4 | none | Extract how a broker values a company (plan 13, D-105, D-109). | 2 | `research_space` | `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..003) | 2026-11-07 |
| `QuarterlyNoteItem` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | BaseModel | One fact the LLM found in the notes, before the quote check. | 0 | `industry_graph.QuarterlyNoteReply` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003) | 2026-11-07 |
| `QuarterlyNoteReply` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | BaseModel | The LLM reply for one quarterly report. | 0 | `industry_graph.QuarterlyNoteExtractor` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003) | 2026-11-07 |
| `QuarterlyNoteResult` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | none | The quote-checked facts of one quarterly report. | 0 | `industry_graph.QuarterlyNoteExtractor` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-002..002) | 2026-11-07 |
| `QuarterlyNoteExtractor` | `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` | 4 | none | Q1 and Q3 reports carry no business chapter; their only narrative is the "主要会计数据、 财务指标发生变动的情况及原因" table and the "其他提醒事项" note. | 3 | `lake` | `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-001..003) | 2026-11-07 |
| `TaxonomyNode` | `quant_cn.quant_cn.industry_graph.product_taxonomy` | 4 | none | One node of the taxonomy as the matcher and views need it. | 1 | `industry_graph.ProductTaxonomy`, `industry_graph.ProductMatcher` | `tests/industry_graph/test_product_matcher.py` (TC-PT-001..001) | 2026-11-07 |
| `ProductTaxonomy` | `quant_cn.quant_cn.industry_graph.product_taxonomy` | 4 | none | Load config/industry_chain/*.yaml once: nodes (names and aliases always strings, even when YAML reads "1,4-丁二醇" style values as numbers), the merged-id map, and the Shenwan L3 → segment map (`sw_l3_map`). | 4 | `industry_graph.ProductMatcher`, `research_space` | `tests/industry_graph/test_product_matcher.py` (TC-PT-001..003) | 2026-11-07 |
| `ProductMatch` | `quant_cn.quant_cn.industry_graph.product_matcher` | 4 | none | One taxonomy node a revenue line maps to, with how it was found. | 0 | `industry_graph.ProductMatcher` | `tests/industry_graph/test_product_matcher.py` (TC-PM-001..001) | 2026-11-07 |
| `ProductMatcher` | `quant_cn.quant_cn.industry_graph.product_matcher` | 4 | none | Map a company's revenue line to taxonomy nodes without the LLM. | 2 | `research_space` | `tests/industry_graph/test_product_matcher.py` (TC-PM-001..004) | 2026-11-07 |
| `ReportDigest` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | none | One broker report reduced to what the synthesis needs: the quote-checked fields of a ValuationExtractor result (plan 13), tagged with a short id the model must cite. | 1 | `industry_graph.BrokerViewSynthesizer` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001) | 2026-11-07 |
| `ViewPoint` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | BaseModel | One synthesized point with the report refs it rests on. | 0 | `industry_graph.BrokerViewReply` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-002..002) | 2026-11-07 |
| `BrokerViewReply` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | BaseModel | The LLM reply before the citation check. | 0 | `industry_graph.BrokerViewSynthesizer` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-003..003) | 2026-11-07 |
| `BrokerView` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | none | The synthesized view after the citation check. | 0 | `industry_graph.BrokerViewSynthesizer` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001) | 2026-11-07 |
| `BrokerViewSynthesizer` | `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` | 4 | none | Synthesize the broker view of one product, Shenwan L3 industry or company from many report digests (user, 2026-11-08: the broker part must be the pattern across reports, not a list). | 1 | `lake` | `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..003) | 2026-11-07 |
| `ModeClaim` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | BaseModel | One quoted answer: a value (variant id, pricing mode, pass-through) with its evidence. | 0 | `industry_graph.BusinessModeReply` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003) | 2026-11-07 |
| `PriceAction` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | BaseModel | A stated price move: direction, what, magnitude, evidence. | 0 | `industry_graph.BusinessModeReply` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-002..002) | 2026-11-07 |
| `BusinessModeReply` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | BaseModel | The LLM reply for one report before validation. | 0 | `industry_graph.BusinessModeExtractor` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003) | 2026-11-07 |
| `BusinessModeResult` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | none | The quote-checked reading: each claim is a dict {value, reason, evidence} or None. | 0 | `industry_graph.BusinessModeExtractor` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..001) | 2026-11-07 |
| `BusinessModeExtractor` | `quant_cn.quant_cn.industry_graph.business_mode_extractor` | 4 | none | Read the business-section pages of one annual report for the business-model fields that only the text can give (BUSINESS_MODEL_DESIGN §4.5 T1, §4b.7): which candidate variant of the company's archetype fits (or a proposed new one), the pricing mode, the cost pass-through and the stated price actions. | 1 | `lake` | `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..003) | 2026-11-07 |
| `Reason` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | BaseModel | One reason for the verdict with the evidence keys it rests on. | 0 | `industry_graph.AdjudicationReply` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-002..002) | 2026-11-07 |
| `AdjudicationReply` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | BaseModel | The LLM reply before validation. | 0 | `industry_graph.PricingAdjudicator` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-003..003) | 2026-11-07 |
| `Adjudication` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | none | The validated verdict. | 0 | `industry_graph.PricingAdjudicator` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003) | 2026-11-07 |
| `PricingAdjudicator` | `quant_cn.quant_cn.industry_graph.pricing_adjudicator` | 4 | none | For a company whose rule-based pricing-power label is insufficient or whose archetype check is inconsistent (BUSINESS_MODEL_DESIGN §4.5, §4b.7), give the model every measured signal, the annual-report claims and the broker-view summary, each under a key, and ask for one label, a confidence, whether the default archetype holds (or which allowed archetype fits) and the reasons. | 1 | `lake` | `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003) | 2026-11-07 |
| `MoatClaim` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | BaseModel | One claimed advantage: its moat type, a short statement, the figure the company gives (if any) and the evidence. | 0 | `industry_graph.MoatReply`, `industry_graph.MoatExtractor` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-002..002) | 2026-11-07 |
| `MoatReply` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | BaseModel | The LLM reply before validation. | 0 | `industry_graph.MoatExtractor` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-003..003) | 2026-11-07 |
| `MoatResult` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | none | The quote-checked claims of one report. | 0 | `industry_graph.MoatExtractor` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..001) | 2026-11-07 |
| `MoatExtractor` | `quant_cn.quant_cn.industry_graph.moat_extractor` | 4 | none | Read the 核心竞争力分析 pages of one annual report and list the advantages the company claims, each classified as one of MOAT_TYPES (cost, switching costs, intangibles, network effects, efficient scale) with the figure it cites. | 1 | `lake` | `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..003) | 2026-11-07 |
| `CurveSummary` | `quant_cn.quant_cn.calculation.futures_curve` | 4 | none | The shape of one contract family's curve on one date: front, most-held, 6- and 12-month and last prices, and the slope from the most-held month to 12 months after it (or to the last later month when the curve is shorter). | 0 | `calculation.FuturesCurve` | `tests/calculation/test_futures_curve.py` (TC-FCV-002..002) | 2026-11-07 |
| `FuturesCurve` | `quant_cn.quant_cn.calculation.futures_curve` | 4 | none | Back-month futures curve per contract family (e.g. | 5 | `plan` | `tests/calculation/test_futures_curve.py` (TC-FCV-001..006) | 2026-11-07 |
| `ImpliedExpectations` | `quant_cn.quant_cn.calculation.implied_expectations` | 4 | none | Turn a market cap into what it already pays for (D-121: "priced in", not "cheap"). | 5 | `plan` | `tests/calculation/test_implied_expectations.py` (TC-IE-001..007) | 2026-11-07 |

## B. Class details (one block per class; methods carry their own purpose)

Template. Copy verbatim; keep headings so `lint_contracts.py` can parse them.

### `PascalName` — `quant_cn.package.module` (L?)
- **Purpose:** one or two lines, identical in meaning to the docstring.
- **Base:** `BaseX` | none. **Depends on (injected):** `Config`, `BaseY`.
- **Used by:** `package.Class.method`, `research_space/main.ipynb`.
- **Tests:** `tests/<layer>/test_<module>.py` (TC-XX-001..NNN).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__(config, dep)` | wire dependencies | `Config`, `BaseY` -> instance | `ConfigError` | callers of the class | — |
| `method_a(x)` | what it does, one line | `list[str]` -> `DataFrame[SchemaZ]` | `DataSourceError` | `pipeline.DownloadPipeline.step_daily` | TC-XX-001, 003 |

Rules: every public method gets a row; private helpers (`_name`) are listed only if longer than 20
lines, so a reader knows they exist. `Input -> Output` uses type names or a registered `Schema` name,
never column lists (those live in section E).

### `Black76Model` — `quant_cn.calculation.black76_model` (L4)
- **Purpose:** Price European options on a forward (Black-76, discounted at the continuous rate) and invert a price to implied volatility; used for ATM-IV checks and known-answer chains.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `research_space/notebooks/20260927_vix_calculation.ipynb`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_black76_model.py` (TC-BM-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_price` | Black-76 price. | float, float, float, float, float, Side -> float | — | as class | see class |
| `compute_implied_vol` | Volatility that reproduces `price` (bisection on [1e-4, 5]). | float, float, float, float, float, Side -> float | `ValueError` | as class | see class |
| `compute_gamma` | Black-76 gamma with respect to the forward (same for calls and puts). | float, float, float, float, float -> float | — | as class | see class |

### `ExpiryClock` — `quant_cn.calculation.expiry_clock` (L4)
- **Purpose:** Convert (trade_date, expiry) to the time units the VIX formulas use. "calendar" is the CBOE white paper: minutes, 30-day target, 365-day year. "trading" counts exchange sessions after the trade date up to expiry: 21-session target, 244-session year, so holidays inside a term add no time (the Mid-Autumn / National Day roll artefact disappears).
- **Base:** none. **Depends on (injected):** ClockMode, Sequence[str].
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_expiry_clock.py` (TC-EC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ClockMode, Sequence[str] -> None | `ValueError` | callers of the class | — |
| `get_units` | Time to expiry in the clock's unit (minutes or sessions). | str, str, int -> float | `ValueError` | as class | see class |
| `get_target` | The constant-maturity target in the clock's unit. | — -> float | — | as class | see class |
| `get_year` | One year in the clock's unit. | — -> float | — | as class | see class |

### `ForwardPriceEstimator` — `quant_cn.calculation.forward_price_estimator` (L4)
- **Purpose:** Per term: F = K* + e^{RT}(C - P) at the strike K* with the smallest /C - P/, and K0 the largest strike at or below F.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.VixCalculator`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_forward_price_estimator.py` (TC-FPE-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | (F, K0) for one term. | pd.DataFrame, float, float -> tuple[float, float] | `ValueError` | as class | see class |

### `FuturesPositioning` — `quant_cn.calculation.futures_positioning` (L4)
- **Purpose:** Per trading day for one CFFEX index-futures product (IF, IH, IC, IM): total open interest and its change, the main contract's price change, the OI x price regime (new shorts, long liquidation, short covering, new longs), top-20 broker gross long / short / net summed over the product's contracts, and the main contract's basis to the index, raw and annualised to its third-Friday expiry. Top-20 figures are gross broker aggregates, not client intent.
- **Base:** none. **Depends on (injected):** str.
- **Used by:** `research_space/notebooks/20260929_positioning_flows.ipynb`.
- **Tests:** `tests/calculation/test_futures_positioning.py` (TC-FP-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | `ValueError` | callers of the class | — |
| `compute` | One row per trading day for the product. | pd.DataFrame, pd.DataFrame, pd.Series -> pd.DataFrame | `KeyError` | as class | see class |
| `list_brokers` | Brokers' gross long, short and net over the product's contracts on one day. | pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `get_expiry` | CFFEX index futures expire on the third Friday of the contract month. | str -> dt.date | `ValueError` | as class | see class |

### `GammaExposureCalculator` — `quant_cn.calculation.gamma_exposure_calculator` (L4)
- **Purpose:** Estimate the gamma dealers carry per option and strike, in CNY of underlying they must trade for a 1% move: GEX = sign * Gamma_F * OI * multiplier * F^2 * 1%, with Gamma from Black-76 at each option's own implied volatility. `sign` is an ASSUMPTION about who is short: the default (+1 calls, -1 puts) means dealers are long calls and short puts (customers write calls and buy puts). Negative total GEX = dealers sell into falls (moves amplify).
- **Base:** none. **Depends on (injected):** RiskFreeCurve, OptionChainBuilder, ForwardPriceEstimator, Black76Model, Mapping[str, float], int.
- **Used by:** `research_space/notebooks/20260929_positioning_flows.ipynb`.
- **Tests:** `tests/calculation/test_gamma_exposure_calculator.py` (TC-GEC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskFreeCurve, OptionChainBuilder, ForwardPriceEstimator, Black76Model, Mapping[str, float], int -> None | `ValueError` | callers of the class | — |
| `compute` | Exposure of every option of one day with 1 <= days <= max_days. | pd.DataFrame, str, float -> pd.DataFrame | `ValueError` | as class | see class |
| `compute_profile` | Total dealer GEX if every term's forward moved to each level (IVs held fixed). | pd.DataFrame, Sequence[float] -> pd.DataFrame | — | as class | see class |
| `find_flip` | Level where total GEX changes sign (linear interpolation), the "gamma flip". | pd.DataFrame -> float \| None | — | as class | see class |
| `_build_row` (private) | internal helper over 20 lines | dict[str, Any], str, int, float, float, float, float -> list[dict[str, object]] | — | internal | — |

### `MarginLadderEstimator` — `quant_cn.calculation.margin_ladder_estimator` (L4)
- **Purpose:** Estimate where margin-financed positions face forced selling. Per stock, financing debt is split into first-in-first-out vintages: each day's financed buying (rzmre) opens a vintage at that day's close; repayments (rzche) retire the oldest first; the balance before the window is one "seeded" vintage at the first close. A vintage is force-sold when collateral/debt falls below `maintenance_ratio`; with own capital = initial_margin_ratio x debt at entry, that happens at price entry x maintenance_ratio / (1 + initial_margin_ratio). Pooled per-stock data and cross-collateral make this an estimate of concentration, not prices.
- **Base:** none. **Depends on (injected):** float, float.
- **Used by:** `research_space/notebooks/20260929_positioning_flows.ipynb`.
- **Tests:** `tests/calculation/test_margin_ladder_estimator.py` (TC-MLE-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float, float -> None | `ValueError` | callers of the class | — |
| `compute_ladder` | Outstanding financing vintages per stock on `as_of` with liquidation prices. | pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `compute_curve` | Financing debt whose liquidation price is reached if every stock falls by each drawdown. | pd.DataFrame, Sequence[float] -> pd.DataFrame | — | as class | see class |
| `_build_vintages` (private) | internal helper over 20 lines | pd.DataFrame -> list[tuple[str, float, float, bool]] | — | internal | — |

### `OptionChainBuilder` — `quant_cn.calculation.option_chain_builder` (L4)
- **Purpose:** Join the option master (opt_basic) with daily prices (opt_daily) into one tidy chain per underlying, and turn one expiry of it into a strike x (call, put) quote table.
- **Base:** none. **Depends on (injected):** bool.
- **Used by:** `calculation.VixCalculator`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_option_chain_builder.py` (TC-OCB-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | bool -> None | — | callers of the class | — |
| `build_chain` | The chain of one underlying over the dates present in `daily`. | pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | `KeyError` | as class | see class |
| `build_quotes` | Strike x side table of prices and volumes for one expiry on one day. | pd.DataFrame -> tuple[pd.DataFrame, bool] | `KeyError` | as class | see class |

### `RiskFreeCurve` — `quant_cn.calculation.risk_free_curve` (L4)
- **Purpose:** Continuously compounded risk-free rate for a tenor in calendar days, from the latest SHIBOR fixing on or before the date, linearly interpolated between tenors and clamped outside them.
- **Base:** none. **Depends on (injected):** pd.DataFrame.
- **Used by:** `calculation.VixCalculator`, `calculation.GammaExposureCalculator`.
- **Tests:** `tests/calculation/test_risk_free_curve.py` (TC-RFC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | pd.DataFrame -> None | `ValueError` | callers of the class | — |
| `get_rate` | Continuous annual rate for `days` calendar days as of `trade_date`. | str, int -> float | `ValueError` | as class | see class |

### `TermInterpolator` — `quant_cn.calculation.term_interpolator` (L4)
- **Purpose:** VIX = 100 * sqrt([T1 s1^2 (N2 - Nt)/(N2 - N1) + T2 s2^2 (Nt - N1)/(N2 - N1)] * Ny / Nt), with N in the clock's unit (minutes or sessions) and Ny one year in that unit.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_term_interpolator.py` (TC-TI-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | The interpolated (or extrapolated) index level. | float, float, float, float, float, float -> float | `ValueError` | as class | see class |

### `TermSelector` — `quant_cn.calculation.term_selector` (L4)
- **Purpose:** Choose the two nearest expiries with at least `min_days` calendar days to expiry.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_term_selector.py` (TC-TS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `list_terms` | (near, next) maturity dates for one day's chain. | pd.DataFrame -> tuple[str, str] | `ValueError` | as class | see class |

### `VarianceStripCalculator` — `quant_cn.calculation.variance_strip_calculator` (L4)
- **Purpose:** sigma^2 = (2/T) sum(dK/K^2 e^{RT} Q(K)) - (1/T)(F/K0 - 1)^2 over puts below K0, calls above K0 and the call/put average at K0; walking away from K0 stops after two consecutive "zero" strikes (zero price, or with price_or_volume also zero volume: no bid/ask, D-048).
- **Base:** none. **Depends on (injected):** ZeroRule.
- **Used by:** `calculation.VixCalculator`.
- **Tests:** `tests/calculation/test_variance_strip_calculator.py` (TC-VSC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ZeroRule -> None | — | callers of the class | — |
| `compute` | Variance and number of strikes used for one term. | pd.DataFrame, float, float, float, float -> tuple[float, int] | `KeyError` | as class | see class |

### `CompanyCyclePanel` — `quant_cn.calculation.company_cycle_panel` (L4)
- **Purpose:** For every company, as known on a date, place its latest quarter in its own cycle: single-quarter and TTM revenue, GM, profit and deducted profit with YoY and QoQ, ROE and turnover, 10-year median annual profit and max annual net margin, ttm_vs_med and margin_peak (plan 16 ph1, D-121). Pure: versions come in as a frame from `lake.StatementVersionReader`.
- **Base:** none. **Depends on (injected):** DateCodec, DiscoverySettings.
- **Used by:** (none yet; pipeline.DiscoveryStep plan 16 ph6).
- **Tests:** `tests/calculation/test_company_cycle_panel.py` (TC-CCP-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DateCodec, DiscoverySettings -> None | — | callers of the class | — |
| `list_fields` | fundamentals_long fields the panel needs | () -> list[str] | — | callers | TC-CCP-009 |
| `compute_start` | earliest period end needed for as_of | str -> str | `ValueError` | callers | TC-CCP-009 |
| `list_quarters` | single-quarter history per company (last `count`) | pd.DataFrame, str, int -> pd.DataFrame | `ValueError` | research checks; plan 16 ph3 IdeaScreener (sensitivity input to `ImpliedExpectations.compute_sensitivity`) | TC-CCP-010 |
| `build` | the cycle panel as known on as_of | pd.DataFrame, str -> pd.DataFrame | `ValueError` | callers | TC-CCP-001..009 |

### `VixCalculator` — `quant_cn.calculation.vix_calculator` (L4)
- **Purpose:** Orchestrate the white-paper steps per trading day: select near/next terms, rate per term, forward and K0, variance strip, interpolation on the chosen clock; one VIX_PANEL row per (trade_date, underlying). A day that cannot be computed gets vix NaN and a "failed: <reason>" quality_flag instead of stopping the run.
- **Base:** none. **Depends on (injected):** RiskFreeCurve, OptionChainBuilder, TermSelector, ForwardPriceEstimator, VarianceStripCalculator, TermInterpolator, ExpiryClock.
- **Used by:** `research_space/notebooks/20260927_vix_calculation.ipynb`.
- **Tests:** `tests/calculation/test_vix_calculator.py` (TC-VC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | RiskFreeCurve, OptionChainBuilder, TermSelector, ForwardPriceEstimator, VarianceStripCalculator, TermInterpolator, ExpiryClock -> None | — | callers of the class | — |
| `compute` | The index for every trading day in `chain`. | pd.DataFrame, str -> pd.DataFrame | `SchemaError` | as class | see class |
| `_compute_day` (private) | internal helper over 20 lines | pd.DataFrame, str, str -> dict[str, object] | — | internal | — |

### `QuantCnCli` — `quant_cn.cli` (L8)
- **Purpose:** `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup, project-catalog, query. Builds every service from Config (the only place objects are wired) and prints summaries.
- **Base:** none. **Depends on (injected):** Config | None, Console | None.
- **Used by:** `Makefile targets doctor, download, compact, lake-rebuild, lake-backup`, `cli.DocumentCommands`.
- **Tests:** `tests/test_cli.py` (TC-QCC-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config \| None, Console \| None -> None | — | callers of the class | — |
| `run` | Parse arguments and dispatch to a command. | Sequence[str] \| None -> int | `SystemExit` | as class | see class |
| `_build_parser` (private) | internal helper over 20 lines | — -> argparse.ArgumentParser | — | internal | — |
| `_run_curate` (private) | internal helper over 20 lines | Config, argparse.Namespace -> int | — | internal | — |

### `ResearchCommands` — `quant_cn.cli` (L8)
- **Purpose:** The research-side CLI commands, kept apart so QuantCnCli stays within its size limit: `release-lags` (D-086), `evaluate` (factor campaign reports and trial log, plan 04 phase 5) and `watchlist` (D-120). QuantCnCli parses the arguments and dispatches here.
- **Base:** none. **Depends on (injected):** Console.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/test_cli.py` (TC-QCC-008..009, 011).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Console -> None | — | callers of the class | — |
| `build_parser` | Add the `release-lags`, `watchlist` and `evaluate` subcommands to the CLI parser. | argparse._SubParsersAction -> None | — | `cli.QuantCnCli._build_parser` | see class |

### `BaseApiClient` — `quant_cn.core.base_api_client` (L1)
- **Purpose:** Abstract vendor client: one logical query returns all pages as one DataFrame.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `query` | Run one query and return every row across pages. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |

### `BaseFetchLog` — `quant_cn.core.base_fetch_log` (L1)
- **Purpose:** Abstract record of which (dataset, key) pairs are fully downloaded.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/lake/test_fetch_log.py` (TC-FL-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_done_keys` | All keys recorded as done for a dataset. | str -> set[str] | `LakeError` | as class | see class |
| `mark_done` | Record a finished key, replacing any earlier record for it. | str, str, int, Path \| None -> None | `LakeError` | as class | see class |
| `save` | Make recorded keys durable (e.g. write the parquet mirror). | — -> Path \| None | `LakeError` | as class | see class |
| `is_done` | True if the key is recorded as done. | str, str -> bool | `LakeError` | as class | see class |
| `list_pending` | The subset of `keys` not yet done, in input order. | str, Sequence[str] -> list[str] | `LakeError` | as class | see class |

### `BaseFetcher` — `quant_cn.core.base_fetcher` (L1)
- **Purpose:** Download one dataset as a sequence of keys; subclasses define the keys and the per-key parameters of one sweep pattern, never one endpoint.
- **Base:** ABC. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock.
- **Used by:** `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock -> None | `TypeError` | callers of the class | — |
| `list_keys` | All fetch keys for [start, end], ascending. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
| `build_params` | API parameters for one key. | str, str, str -> dict[str, str] | — | as class | see class |
| `list_due_keys` | Keys that must be fetched: all if forced or overwrite, else pending plus the newest `refetch_recent` keys. | Sequence[str], bool -> list[str] | `LakeError` | as class | see class |
| `fetch_one` | Query the endpoint for one key. | str, str, str -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |
| `run` | Fetch every key that needs fetching, writing and logging each before the next. | str, str, str, Sequence[str] \| None, bool, ProgressHook \| None -> StepReport | `DataSourceError`, `PermissionDeniedError`, `SchemaError`, `LakeError` | as class | see class |
| `_fetch_key` (private) | internal helper over 20 lines | str, str, str, str, StepReport -> str | — | internal | — |

### `BaseRunLog` — `quant_cn.core.base_run_log` (L1)
- **Purpose:** Abstract append-only log of runs and per-key events; the source of truth for "what happened".
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.PrefectRunner`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `open_run` | Open a run and return its id. | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one event (fetched / skipped / empty / failed / blocked). | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Close a run with its final status. | str, str, str -> None | `LakeError` | as class | see class |

### `BaseStep` — `quant_cn.core.base_step` (L1)
- **Purpose:** Abstract unit of pipeline work: list its units, then run and report.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `name` | Step name shown in progress and reports. | — -> str | — | as class | see class |
| `list_units` | Compute the work units (e.g. keys) just before running. | — -> list[str] | `QuantCnError` | as class | see class |
| `run` | Do the work listed by `list_units`. | str, ProgressHook \| None -> StepReport | `QuantCnError` | as class | see class |

### `BaseStore` — `quant_cn.core.base_store` (L1)
- **Purpose:** Abstract sink for raw fetch results and curated partitions.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.DateWindowFetcher`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `write_raw` | Persist one fetch key's rows atomically. | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition atomically after validating its schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |

### `Clock` — `quant_cn.core.clock` (L1)
- **Purpose:** The single source of wall time, monotonic time and sleeping; tests inject a fake subclass.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.FetcherFactory`, `data_loading.PeriodSweepFetcher`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `lake.RebuildAudit`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `data_loading.RequestPacer`.
- **Tests:** `tests/core/test_clock.py` (TC-CL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_now` | Current local wall time. | — -> dt.datetime | — | as class | see class |
| `get_today` | Today's date as a Tushare `YYYYMMDD` string. | — -> str | — | as class | see class |
| `get_monotonic` | Monotonic seconds for measuring durations. | — -> float | — | as class | see class |
| `sleep` | Block for `seconds`; fakes record the call instead. | float -> None | — | as class | see class |

### `LakeConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Where the lake lives and whether it may sit inside the repository.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`.
- **Tests:** `tests/core/test_config.py` (TC-C-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TushareConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Tushare endpoint, paging, retry and rate-limit settings; the token comes from env only.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `data_loading.TushareClient`.
- **Tests:** `tests/core/test_config.py` (TC-C-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DownloadConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Which datasets to download, in what order, and from which start dates (D-015b).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`.
- **Tests:** `tests/core/test_config.py` (TC-C-004..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FactorSpec` — `quant_cn.core.config` (L1)
- **Purpose:** One factor of config/factors.yaml: its name, implementing class and parameters.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `factor.FactorFactory`.
- **Tests:** `tests/core/test_config.py` (TC-C-012..012).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `CampaignConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Settings of one factor campaign (config/factors.yaml `campaign`, plan 04 phase 5).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`.
- **Tests:** `tests/core/test_config.py` (TC-C-013..013).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `UniverseConfig` — `quant_cn.core.config` (L1)
- **Purpose:** Rules of the tradeable universe per session (FACTOR_TESTING_DESIGN §11, D-054).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `pipeline.UniverseStep`.
- **Tests:** `tests/core/test_config.py` (TC-C-011..011).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FuturesCategory` — `quant_cn.core.config` (L1)
- **Purpose:** One member-category label that `fut_holding` lists among real brokers (D-079).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `lake.DerivedViews`.
- **Tests:** `tests/core/test_config.py` (TC-C-009..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TickerAlias` — `quant_cn.core.config` (L1)
- **Purpose:** One retired code and the code its company trades on afterwards (D-053, D-089).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `lake.TickerAliasMap`, `lake.DerivedViews`.
- **Tests:** `tests/core/test_config.py` (TC-C-010..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `WatchlistEntry` — `quant_cn.core.config` (L1)
- **Purpose:** One stock the user watches and the price range at which they would buy it (D-120); loaded from git-ignored `config/local.watchlist.yaml`.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `portfolio.WatchlistBuilder`.
- **Tests:** `tests/core/test_config.py` (TC-C-015).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `WatchlistSettings` — `quant_cn.core.config` (L1)
- **Purpose:** Thresholds and windows of the watchlist page: near_pct, history_days, consensus_days (base.yaml `watchlist`, D-120).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `portfolio.WatchlistBuilder`.
- **Tests:** `tests/core/test_config.py` (TC-C-016).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DiscoverySettings` — `quant_cn.core.discovery_settings` (L1)
- **Purpose:** Thresholds and windows of the discovery pipeline: history_years, min_years (base.yaml `discovery`, plan 16, D-121).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `calculation.CompanyCyclePanel`.
- **Tests:** `tests/core/test_config.py` (TC-C-017).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `Config` — `quant_cn.core.config` (L1)
- **Purpose:** The typed configuration injected everywhere: YAML defaults, machine overrides, environment.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `cli.ServiceBuilder`, `cli.ResearchCommands`, `cli.DocumentCommands`, `portfolio.WatchlistBuilder`.
- **Tests:** `tests/core/test_config.py` (TC-C-001..017).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | Build the configuration from `config/base.yaml`, `config/datasets.yaml`, optional `config/local.yaml`, the repo `.env` and the process environment. | Path \| None, Mapping[str, str] \| None -> Config | `ConfigError` | as class | see class |
| `get_dataset` | Look up one dataset spec by name. | str -> DatasetSpec | `ConfigError` | as class | see class |
| `get_start` | Download start date for a dataset: its own `start`, else long-history start if listed, else the default start. | str -> str | `ConfigError` | as class | see class |

### `ValuesFromDataset` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Enumerate sweep keys from another curated dataset (e.g. every ETF code in fund_basic).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.SweepSpec`.
- **Tests:** `tests/data_loading/test_fetcher_factory.py` (TC-FF-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `SweepSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** How a dataset is swept so each call returns the whole market for one key.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DatasetSpec`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `param` | API parameter name carrying the key (None for single-call datasets). | — -> str \| None | — | as class | see class |

### `CuratedSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Where a dataset lands in `curated/` and which date column drives its yearly partition.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DatasetSpec`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DatasetSpec` — `quant_cn.core.dataset_spec` (L1)
- **Purpose:** Everything the lake and the fetchers need to know about one dataset, as data (D-012).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.CompactStep`, `lake.DerivedViews`, `lake.ProjectCatalog`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `lake.ReleaseLagChecker`, `lake.LakeReader`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_raw_filename` | Hive-style raw file name for one fetch key. | str -> str | — | as class | see class |
| `build_schema` | The dataset's Schema (fields, text fields, primary key). | — -> Schema | `SchemaError` | as class | see class |
| `_check_columns` (private) | internal helper over 20 lines | — -> DatasetSpec | — | internal | — |

### `DateCodec` — `quant_cn.core.date_codec` (L1)
- **Purpose:** Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`, `data_loading.FetcherFactory`, `cli.QuantCnCli`, `lake.PitAligner`, `visualization.PriceChart`, `cli.ServiceBuilder`, `data_loading.DateWindowFetcher`, `lake.EffectiveDateResolver`, `factor.FactorFactory`, `lake.StatementVersionReader`, `calculation.CompanyCyclePanel`.
- **Tests:** `tests/core/test_date_codec.py` (TC-DC-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `validate` | Return `value` unchanged if it is a valid `YYYYMMDD` date string. | str -> str | `ValueError` | as class | see class |
| `to_date` | Parse a `YYYYMMDD` string. | str -> dt.date | `ValueError` | as class | see class |
| `to_str` | Format a date as `YYYYMMDD`. | dt.date -> str | — | as class | see class |
| `list_quarter_ends` | Report periods (Mar 31, Jun 30, Sep 30, Dec 31) within [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `list_weekdays` | Monday-to-Friday dates within [start, end], for announcement-date sweeps. | str, str -> list[str] | `ValueError` | as class | see class |
| `list_days` | Every calendar day within [start, end], for event sweeps that publish on weekends too. | str, str -> list[str] | `ValueError` | as class | see class |

### `Finding` — `quant_cn.core.docs.base_checker` (L1)
- **Purpose:** One rule violation at a location, printable as `path:line [rule] message`.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.BaseChecker.run`, `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_base_checker.py` (TC-BCH-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `to_text` | One-line human form. | — -> str | — | as class | see class |

### `BaseChecker` — `quant_cn.core.docs.base_checker` (L1)
- **Purpose:** Abstract repository check: inspect the tree, return findings (empty = pass).
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_base_checker.py` (TC-BCH-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Run the check over the repository. | — -> list[Finding] | `OSError`, `SyntaxError` | as class | see class |

### `MethodInfo` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** One function defined directly in a class body.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ClassInfo`, `core.docs.CodeScanner.read_module`, `core.docs.ModuleInfo`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `n_lines` | Physical lines including docstring and blanks. | — -> int | — | as class | see class |
| `is_public` | True for names without a leading underscore. | — -> bool | — | as class | see class |

### `ClassInfo` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** One top-level class: span, bases, docstring, methods and the names its body references.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ModuleInfo`, `core.docs.CodeScanner.read_module`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `n_lines` | Physical lines of the class. | — -> int | — | as class | see class |
| `list_public_methods` | Methods and properties without a leading underscore, in source order. | — -> list[MethodInfo] | — | as class | see class |

### `ModuleInfo` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** One scanned Python file.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.CodeScanner.read_module`, `core.docs.ContractChecker`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `CodeScanner` — `quant_cn.core.docs.code_scanner` (L1)
- **Purpose:** Parse Python files with `ast` into ModuleInfo records (no import, no execution).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_module` | Scan one file. | Path, Path -> ModuleInfo | `SyntaxError`, `OSError` | as class | see class |

### `CodeTableBuilder` — `quant_cn.core.docs.code_table_builder` (L1)
- **Purpose:** Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the code-side tables of the `project` schema, one DataFrame per table with fixed columns.
- **Base:** none. **Depends on (injected):** Path, CodeScanner, DocstringParser, RegistryReader.
- **Used by:** `lake.ProjectCatalog`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_code_table_builder.py` (TC-CTB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, DocstringParser, RegistryReader -> None | — | callers of the class | — |
| `build_tables` | Build all five code tables. | — -> dict[str, pd.DataFrame] | `SyntaxError`, `OSError` | as class | see class |
| `_add_class` (private) | internal helper over 20 lines | dict[str, list[list[object]]], str, ModuleInfo, RegistryInfo -> None | — | internal | — |
| `_add_methods` (private) | internal helper over 20 lines | dict[str, list[list[object]]], RegistryInfo -> None | — | internal | — |

### `CodeUnit` — `quant_cn.core.docs.contract_checker` (L1)
- **Purpose:** A class with the module it lives in and its parsed contract.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`.
- **Tests:** `tests/core/docs/test_contract_checker.py` (TC-CC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ContractChecker` — `quant_cn.core.docs.contract_checker` (L1)
- **Purpose:** Check contracts across the tree: class docstrings carry all sections and public methods Purpose + Contract; docstring TC IDs and `test_tc_*` functions match one-to-one; each src class's `Used by` equals the src classes that reference it; every src class has its registry rows and a method table equal to its public methods; class names are unique; no module-level functions in src outside core/utils.
- **Base:** BaseChecker. **Depends on (injected):** Path, CodeScanner, DocstringParser, RegistryReader.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_contract_checker.py` (TC-CC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, DocstringParser, RegistryReader -> None | — | callers of the class | — |
| `run` | Run every contract rule. | — -> list[Finding] | `SyntaxError`, `OSError` | as class | see class |
| `_check_tests` (private) | internal helper over 20 lines | list[tuple[str, ModuleInfo]], list[CodeUnit], list[tuple[str, ModuleInfo]] -> list[Finding] | — | internal | — |
| `_check_used_by` (private) | internal helper over 20 lines | list[CodeUnit], list[CodeUnit] -> list[Finding] | — | internal | — |
| `_check_registry` (private) | internal helper over 20 lines | list[tuple[str, ModuleInfo]], list[CodeUnit], RegistryInfo -> list[Finding] | — | internal | — |
| `_check_registry_class` (private) | internal helper over 20 lines | CodeUnit, RegistryInfo -> list[Finding] | — | internal | — |

### `ContractLinter` — `quant_cn.core.docs.contract_linter` (L1)
- **Purpose:** Build the four checkers (contracts, index, size, names) for one repository and run the selected groups, returning all findings sorted.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `scripts/lint_contracts.py`, `tests/test_contracts.py`, `lake.ProjectCatalog`, `cli.ServiceBuilder`.
- **Tests:** `tests/test_contracts.py` (TC-CTL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `run` | Run the selected checker groups. | Iterable[str] -> list[Finding] | `ValueError`, `RuntimeError`, `SyntaxError` | as class | see class |

### `ConventionReader` — `quant_cn.core.docs.convention_reader` (L1)
- **Purpose:** Extract the allowed method-name verb prefixes from the naming convention's §2.1 table.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_convention_reader.py` (TC-CR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read_verbs` | Verb prefixes (e.g. "get_") and bare verbs (e.g. "run") in table order. | Path -> list[str] | `ValueError`, `OSError` | as class | see class |

### `DecisionRecord` — `quant_cn.core.docs.decisions_reader` (L1)
- **Purpose:** One decision: its log-table row joined with the Context and Decision bullets of its block.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.DecisionsReader`.
- **Tests:** `tests/core/docs/test_decisions_reader.py` (TC-DR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DecisionsReader` — `quant_cn.core.docs.decisions_reader` (L1)
- **Purpose:** Parse DECISIONS.md: the ID/Date/Title/Status/Where table plus `### D-NNN` detail blocks.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_decisions_reader.py` (TC-DR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | All decisions in table order. | Path -> list[DecisionRecord] | `OSError` | as class | see class |

### `DocTableBuilder` — `quant_cn.core.docs.doc_table_builder` (L1)
- **Purpose:** Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into the document-side tables of the `project` schema.
- **Base:** none. **Depends on (injected):** Path, RepoFiles, IndexReader, DecisionsReader, PlanReader.
- **Used by:** `lake.ProjectCatalog`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_doc_table_builder.py` (TC-DTB-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, RepoFiles, IndexReader, DecisionsReader, PlanReader -> None | — | callers of the class | — |
| `build_tables` | Build all five document tables. | — -> dict[str, pd.DataFrame] | `RuntimeError`, `OSError` | as class | see class |
| `_build_tree` (private) | internal helper over 20 lines | — -> dict[str, pd.DataFrame] | — | internal | — |
| `_build_plans` (private) | internal helper over 20 lines | — -> dict[str, pd.DataFrame] | — | internal | — |

### `UsedByEntry` — `quant_cn.core.docs.docstring_parser` (L1)
- **Purpose:** One line of a `Used by:` section, split into the caller reference and its note.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.DocContract`, `core.docs.DocstringParser.parse`.
- **Tests:** `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DocContract` — `quant_cn.core.docs.docstring_parser` (L1)
- **Purpose:** The parsed contract of one class, method or module docstring.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.DocstringParser.parse`, `core.docs.CodeUnit`.
- **Tests:** `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `has` | True if every named section is present. | — -> bool | — | as class | see class |

### `DocstringParser` — `quant_cn.core.docs.docstring_parser` (L1)
- **Purpose:** Split a contract docstring into its sections: Purpose, Contract (Input, Output, Raises), Used by, Test cases.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `parse` | Parse one docstring. | str \| None -> DocContract | — | as class | see class |

### `IndexChecker` — `quant_cn.core.docs.index_checker` (L1)
- **Purpose:** Every visible folder has an INDEX.md whose folder and file rows equal what is on disk, and whose Contains cell for a .py file lists exactly its top-level classes (fixtures for conftest.py; public constants for modules without classes).
- **Base:** BaseChecker. **Depends on (injected):** Path, RepoFiles, IndexReader, CodeScanner.
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_index_checker.py` (TC-IC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, RepoFiles, IndexReader, CodeScanner -> None | — | callers of the class | — |
| `run` | Check every folder's index. | — -> list[Finding] | `RuntimeError`, `SyntaxError` | as class | see class |
| `_check_folder` (private) | internal helper over 20 lines | Path, IndexInfo, list[Path], list[Path] -> list[Finding] | — | internal | — |

### `IndexEntry` — `quant_cn.core.docs.index_reader` (L1)
- **Purpose:** One row of an INDEX.md table: a subfolder or a file with its purpose and named contents.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.IndexInfo`, `core.docs.IndexReader.read`.
- **Tests:** `tests/core/docs/test_index_reader.py` (TC-IR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `IndexInfo` — `quant_cn.core.docs.index_reader` (L1)
- **Purpose:** Parsed INDEX.md: title line, subfolder entries, file entries.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.IndexReader.read`, `core.docs.IndexChecker`, `core.docs.DocTableBuilder`.
- **Tests:** `tests/core/docs/test_index_reader.py` (TC-IR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `IndexReader` — `quant_cn.core.docs.index_reader` (L1)
- **Purpose:** Parse the fixed INDEX.md format: `## Folders` (Folder, Purpose) and `## Files` (File, Purpose, Contains) tables.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_index_reader.py` (TC-IR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse one INDEX.md. | Path -> IndexInfo | `OSError` | as class | see class |

### `MarkdownTable` — `quant_cn.core.docs.markdown_table` (L1)
- **Purpose:** One pipe table with the heading it sits under.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.MarkdownTableReader.read`.
- **Tests:** `tests/core/docs/test_markdown_table.py` (TC-MTR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_column` | All cells of one column. | str -> list[str] | `KeyError` | as class | see class |

### `MarkdownTableReader` — `quant_cn.core.docs.markdown_table` (L1)
- **Purpose:** Extract every pipe table from markdown text, and backticked names from a cell.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.IndexReader`, `core.docs.RegistryReader`, `core.docs.ConventionReader`, `core.docs.ContractLinter`, `core.docs.DecisionsReader`, `core.docs.PlanReader`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_markdown_table.py` (TC-MTR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read` | All tables in document order. | str -> list[MarkdownTable] | — | as class | see class |
| `list_ticked` | Names written in backticks inside a cell. | str -> list[str] | — | as class | see class |

### `NameChecker` — `quant_cn.core.docs.name_checker` (L1)
- **Purpose:** Enforce names: lowercase paths (governance `UPPER_SNAKE.md` and tool files excepted), verb-first method and function names from the convention's verb table, no banned verbs, test functions named `test_tc_<id>_<desc>`, and module name matching its primary class.
- **Base:** BaseChecker. **Depends on (injected):** Path, CodeScanner, list[Path], Sequence[str].
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_name_checker.py` (TC-NC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, list[Path], Sequence[str] -> None | — | callers of the class | — |
| `run` | Check every visible path and every code file. | — -> list[Finding] | `SyntaxError`, `OSError` | as class | see class |
| `is_verb_name` | True if `name` (leading underscores ignored) starts with an allowed, unbanned verb. | str -> bool | — | as class | see class |

### `PhaseRecord` — `quant_cn.core.docs.plan_reader` (L1)
- **Purpose:** One row of a plan's Phases table.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.PlanRecord`, `core.docs.PlanReader.read`.
- **Tests:** `tests/core/docs/test_plan_reader.py` (TC-PR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PlanRecord` — `quant_cn.core.docs.plan_reader` (L1)
- **Purpose:** One execution plan: number, title, header fields and phases.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.PlanReader.read`.
- **Tests:** `tests/core/docs/test_plan_reader.py` (TC-PR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PlanReader` — `quant_cn.core.docs.plan_reader` (L1)
- **Purpose:** Parse a plan file: `# NN — Title`, the two-column header table (Status, Decisions, Depends on plans) and the Phases table.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_plan_reader.py` (TC-PR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse one plan file. | Path -> PlanRecord \| None | `OSError` | as class | see class |

### `RegistryInfo` — `quant_cn.core.docs.registry_reader` (L1)
- **Purpose:** The registry's content as sets and maps the linter can compare with code.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.docs.RegistryReader.read`, `core.docs.ContractChecker`, `core.docs.CodeTableBuilder`.
- **Tests:** `tests/core/docs/test_registry_reader.py` (TC-RR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `RegistryReader` — `quant_cn.core.docs.registry_reader` (L1)
- **Purpose:** Parse CLASS_REGISTRY.md: section A index, section B detail blocks and their method tables, and the class/schema names of sections C, D, E.
- **Base:** none. **Depends on (injected):** MarkdownTableReader.
- **Used by:** `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_registry_reader.py` (TC-RR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse the registry file. | Path -> RegistryInfo | `OSError` | as class | see class |

### `RepoFiles` — `quant_cn.core.docs.repo_files` (L1)
- **Purpose:** The set of repository files a linter should see: `git ls-files --cached --others --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_repo_files.py` (TC-RF-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `list_files` | Relative paths of visible files that exist on disk, spelled as on disk, sorted. | — -> list[Path] | `RuntimeError` | as class | see class |
| `list_folders` | Every folder that holds at least one visible file, including the root (Path(".")). | — -> list[Path] | `RuntimeError` | as class | see class |

### `SizeChecker` — `quant_cn.core.docs.size_checker` (L1)
- **Purpose:** Fail any .py file over 600 lines, class over 300, function or method over 50 (physical lines, docstrings included), and INDEX.md / SKILL.md / execution plan over 300 lines.
- **Base:** BaseChecker. **Depends on (injected):** Path, CodeScanner, list[Path].
- **Used by:** `core.docs.ContractLinter`.
- **Tests:** `tests/core/docs/test_size_checker.py` (TC-SC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, CodeScanner, list[Path] -> None | — | callers of the class | — |
| `run` | Check every code file and governance doc. | — -> list[Finding] | `SyntaxError`, `OSError` | as class | see class |

### `Schema` — `quant_cn.core.schema` (L1)
- **Purpose:** Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null.
- **Base:** none. **Depends on (injected):** str, Sequence[str], Collection[str], Sequence[str].
- **Used by:** `core.DatasetSpec.build_schema`, `lake.LakeReader`.
- **Tests:** `tests/core/test_schema.py` (TC-S-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, Sequence[str], Collection[str], Sequence[str] -> None | `SchemaError` | callers of the class | — |
| `get_dtype` | Declared dtype name of `column`. | str -> str | — | as class | see class |
| `normalize` | Return a copy of `df` cast to the declared dtypes. | pd.DataFrame, bool -> pd.DataFrame | `SchemaError` | as class | see class |
| `validate` | Check `df` satisfies the schema exactly. | pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `build_empty` | A zero-row frame with the declared columns and dtypes. | — -> pd.DataFrame | — | as class | see class |

### `StepReport` — `quant_cn.core.step_report` (L1)
- **Purpose:** Counts and status of one step (usually one dataset's fetch) so runs can be summarised.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `pipeline.FetchStep`, `pipeline.PipelineReport`, `pipeline.CompactStep`, `pipeline.DeriveStep`, `pipeline.PrefectRunner`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `TickerNormalizer` — `quant_cn.core.ticker_normalizer` (L1)
- **Purpose:** Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/core/test_ticker_normalizer.py` (TC-TN-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `normalize` | Convert `code` to `ts_code`. | str -> str | `ValueError` | as class | see class |
| `is_valid` | True if `code` is already a well-formed `ts_code`. | str -> bool | — | as class | see class |

### `AkshareClient` — `quant_cn.data_loading.akshare_client` (L3)
- **Purpose:** Call one AkShare function per query (`api_name` = function name, `params` = its keyword arguments) and return its frame with dates normalised to YYYYMMDD strings, so the lake's schema and PIT rules apply unchanged. AkShare scrapes public pages (exchanges, ChinaBond, Jin10, Sina): network failures are retried; the library is imported on first use because it lives in the optional extra "sources" (D-022, D-065).
- **Base:** BaseApiClient. **Depends on (injected):** Clock, int, float, ModuleType | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_akshare_client.py` (TC-AKC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, int, float, ModuleType \| None -> None | — | callers of the class | — |
| `query` | Run one AkShare function and normalise its dates. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `BaostockClient` — `quant_cn.data_loading.baostock_client` (L3)
- **Purpose:** Call one BaoStock query per request (`api_name` = method, e.g. query_history_k_data_plus) and return a frame in lake conventions: `ts_code` param converted to BaoStock's code ("600000.SH" -> "sh.600000") and back in the result, YYYYMMDD dates in and out, numeric strings as floats. Logs in once on first use; BaoStock is in the optional extra "sources" and is imported lazily. Verification only: its datasets never replace Tushare's (D-065).
- **Base:** BaseApiClient. **Depends on (injected):** Clock, int, float, ModuleType | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_baostock_client.py` (TC-BSC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, int, float, ModuleType \| None -> None | — | callers of the class | — |
| `query` | Run one BaoStock query for one security. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `FetcherFactory` — `quant_cn.data_loading.fetcher_factory` (L3)
- **Purpose:** Build the right fetcher for a DatasetSpec and inject the shared dependencies.
- **Base:** none. **Depends on (injected):** Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec, Mapping[str, BaseApiClient] | None, LakeQuery | None.
- **Used by:** `pipeline.DownloadPipeline`, `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec, Mapping[str, BaseApiClient] \| None, LakeQuery \| None -> None | — | callers of the class | — |
| `build` | Instantiate the fetcher for `spec.sweep.kind`. | DatasetSpec -> BaseFetcher | `ConfigError` | as class | see class |

### `SingleCallFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Datasets fetched in one (paged) call, key "all": trade_cal, namechange.
- **Base:** BaseFetcher. **Depends on (injected):** —.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-SCF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_keys` | The single key. | str, str -> list[str] | — | as class | see class |
| `build_params` | Constant parameters, plus the run's date range when configured. | str, str, str -> dict[str, str] | — | as class | see class |

### `EnumFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily / fund_daily by ts_code, opt_basic by exchange.
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str].
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-EF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, Sequence[str] -> None | — | callers of the class | — |
| `list_keys` | The enumerated values. | str, str -> list[str] | — | as class | see class |
| `build_params` | Key parameter plus constants and optional date range. | str, str, str -> dict[str, str] | — | as class | see class |

### `DateSweepFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Whole-market daily sweeps: trade_date and nav_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit, fund_nav); ann_date keys are weekdays (event datasets). An empty key within the last RECENT_SESSIONS trading sessions is logged `empty_recent` and retried next run instead of being marked done (D-078).
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-DSF-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `list_keys` | Trading days (trade_date, nav_date) or weekdays (ann_date) in [start, end]. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
| `build_params` | {param: key} plus constants. | str, str, str -> dict[str, str] | — | as class | see class |

### `PeriodSweepFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end.
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-PSF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec -> None | — | callers of the class | — |
| `list_keys` | Quarter ends in [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `build_params` | {"period": key} plus constants. | str, str, str -> dict[str, str] | — | as class | see class |

### `DateWindowFetcher` — `quant_cn.data_loading.fetchers` (L3)
- **Purpose:** Range-only endpoints swept by calendar window (D-063): one call per month ("YYYYMM" keys) or year ("YYYY" keys) with start_date / end_date clipped to the run range. Used where offset paging is broken or capped (share_float; index_weight past 100k rows) or the API takes ranges only (FRED series, fund_nav ranges). With `sweep.value_param` and values, each window is fetched once per value: keys "<window>_<value>", window-major so the newest `refetch_recent` keys are the latest window of every value (D-069).
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec, list[str] | None.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-DWF-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, DateCodec, list[str] \| None -> None | — | callers of the class | — |
| `list_keys` | Window keys covering [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `build_params` | start_date / end_date of the window, clipped to the run range (+ the swept value). | str, str, str -> dict[str, str] | — | as class | see class |

### `HttpTransport` — `quant_cn.data_loading.http_transport` (L3)
- **Purpose:** Send one HTTP request and return the decoded JSON object or the raw bytes: a JSON POST (Tushare), a form POST (CNINFO, D-096), a GET returning JSON (Eastmoney report lists) and a GET returning bytes (PDF downloads). Browser-like User-Agent on every call.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`, `data_loading.BaseWebClient`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `fetch_json` | POST `payload` as JSON to `url`. | str, Mapping[str, Any], float -> dict[str, Any] | `OSError`, `ValueError` | as class | see class |
| `fetch_form_json` | POST `form` url-encoded to `url` and decode the JSON reply. | str, Mapping[str, str], float -> dict[str, Any] | `OSError`, `ValueError` | `data_loading.CninfoClient` | TC-CNC-001 |
| `fetch_get_json` | GET `url` and decode the JSON reply. | str, float -> dict[str, Any] | `OSError`, `ValueError` | `data_loading.EastmoneyReportClient` | TC-EMR-001 |
| `fetch_bytes` | GET `url` and return the body (a PDF download). | str, float -> bytes | `OSError` | `data_loading.DocumentDownloader` | TC-DD-002 |

### `TushareClient` — `quant_cn.data_loading.tushare_client` (L3)
- **Purpose:** Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows; rate-limit replies wait and retry without spending retries; permission replies fail fast as PermissionDeniedError; other failures retry up to `retries`.
- **Base:** BaseApiClient. **Depends on (injected):** TushareConfig, Clock, HttpTransport | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | TushareConfig, Clock, HttpTransport \| None -> None | — | callers of the class | — |
| `query` | Fetch every page of one query. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `ConfigError`, `PermissionDeniedError`, `DataSourceError` | as class | see class |
| `_fetch_page` (private) | internal helper over 20 lines | str, Mapping[str, object], Sequence[str] -> dict[str, Any] | — | internal | — |

### `FactorInputs` — `quant_cn.factor.base_factor` (L5)
- **Purpose:** The panels a factor may read, loaded once by FactorFactory for all factors of a run. Everything is already point in time: fundamentals come only as FUNDAMENTALS_PIT (effective the session after announcement, TTM from PIT-visible versions, D-092), prices and daily_basic are dated by their session (known at its close).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `factor.BaseFactor`, `factor.FactorFactory`, `factor.library.EarningsYieldFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor`.
- **Tests:** `tests/factor/test_base_factor.py` (TC-FIN-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_field` | One fundamentals field as (trade_date, ts_code, <name>). | str -> pd.DataFrame | — | as class | see class |

### `BaseFactor` — `quant_cn.factor.base_factor` (L5)
- **Purpose:** Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it needs and how many sessions of price history before the first output date; `compute` turns FactorInputs into FACTOR_PANEL rows for [start, end]. Contract (FACTOR_TESTING_DESIGN §11): the value at t uses only data known by the close of t; fundamentals only through FUNDAMENTALS_PIT. Subclasses register themselves by class name for FactorFactory.
- **Base:** ABC. **Depends on (injected):** str.
- **Used by:** `factor.FactorFactory`, `factor.library.*`, `factor.library.EarningsYieldFactor`, `factor.library.MomentumFactor`, `factor.library.ProfitGrowthFactor`, `factor.library.ReversalFactor`, `factor.library.RoeFactor`, `factor.library.TurnoverFactor`, `pipeline.FeatureStep`.
- **Tests:** `tests/factor/test_base_factor.py` (TC-BFA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | `TypeError` | callers of the class | — |
| `lookback` | Sessions of history needed before the first output date (0 = none). | — -> int | — | as class | see class |
| `compute` | FACTOR_PANEL rows of this factor for [start, end]. | FactorInputs, str, str -> pd.DataFrame | `SchemaError` | as class | see class |
| `compute_raw` | The raw factor value per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `FactorAcceptance` — `quant_cn.factor.factor_acceptance` (L5)
- **Purpose:** Criteria 1-3 of FACTOR_TESTING_DESIGN §6 per factor at one horizon, from the campaign's IC_TEST: (1) NW t of the full-window mean IC >= t_min (HLZ) and BHY-adjusted p <= alpha; (2) every sub-period mean IC has the full-window sign with sign-oriented t >= t_sub; (3) the bootstrap CI of ICIR excludes 0. Criterion 4 (DSR, PBO, out-of-sample) needs a traded variant and belongs to plan 06, so `verdict` is "pass" (criteria 1-3 met) or "fail"; the horizon profile (peak, half-life, accumulation ratio; D-095) is attached as notes, never a criterion.
- **Base:** none. **Depends on (injected):** int, float, float, float, Sequence[str].
- **Used by:** `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder`.
- **Tests:** `tests/factor/test_factor_acceptance.py` (TC-FA-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, float, float, float, Sequence[str] -> None | `ValueError` | callers of the class | — |
| `compute` | One verdict row per factor. | pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `_build_row` (private) | internal helper over 20 lines | pd.DataFrame, pd.DataFrame, str -> dict[str, object] | — | internal | — |

### `FactorReport` — `quant_cn.factor.factor_evaluator` (L5)
- **Purpose:** The evaluation of one campaign: IC series, every test result, quantile ladders.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `factor.FactorEvaluator`.
- **Tests:** `tests/factor/test_factor_evaluator.py` (TC-FEV-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FactorEvaluator` — `quant_cn.factor.factor_evaluator` (L5)
- **Purpose:** Evaluate every factor of a campaign (FACTOR_TESTING_DESIGN §2, §3, §6): tradeable forward returns from the open of t+1, IC series per horizon, the IcSignificance tests, decay across horizons (half-life), rank autocorrelation (turnover proxy), quantile ladders and long-short statistics on non-overlapping samples, then the campaign-level Holm / BHY / Romano-Wolf adjustment and HLZ flag over all factor x horizon mean-IC tests. Records each variant in the TrialLog (identical variants are not recorded twice).
- **Base:** none. **Depends on (injected):** IcCalculator, IcSignificance, MultipleTestingAdjuster, QuantileReturns, ReturnStats, BlockBootstrap, Sequence[int].
- **Used by:** `notebooks`, `pipeline.EvaluationStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_factor_evaluator.py` (TC-FEV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | IcCalculator, IcSignificance, MultipleTestingAdjuster, QuantileReturns, ReturnStats, BlockBootstrap, Sequence[int] -> None | `ValueError` | callers of the class | — |
| `compute` | The campaign report. | pd.DataFrame, pd.DataFrame, TrialLog \| None, Mapping[str, Mapping[str, object]] \| None, bool -> FactorReport | `SchemaError` | as class | see class |
| `build_campaign` | Campaign-level adjustment over every factor x horizon mean-IC test. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |
| `_build_factor_rows` (private) | internal helper over 20 lines | pd.DataFrame, pd.DataFrame, str -> pd.DataFrame | — | internal | — |

### `FactorFactory` — `quant_cn.factor.factor_factory` (L5)
- **Purpose:** Resolve config/factors.yaml entries to BaseFactor instances (every module under factor/library/ is imported so its classes register themselves; adding a factor needs one module, one registry block and one YAML line) and load, once, the panels the chosen factors declare: dense prices from `lookback` sessions before the start, PIT fundamentals for the union of fields, daily_basic columns.
- **Base:** none. **Depends on (injected):** Sequence[FactorSpec], TradingCalendar, DateCodec.
- **Used by:** `notebooks`, `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_factor_factory.py` (TC-FAF-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Sequence[FactorSpec], TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `build_all` | One instance per configured factor. | — -> list[BaseFactor] | `ConfigError` | as class | see class |
| `build_inputs` | The panels the factors need for outputs in [start, end]. | LakeReader, Sequence[BaseFactor], str, str -> FactorInputs | `LakeError` | as class | see class |

### `FactorPreprocessor` — `quant_cn.factor.factor_preprocessor` (L5)
- **Purpose:** The ordered chain applied to every raw factor, each step optional and logged: winsorise (median +- k * 1.4826 * MAD per date) -> standardise (z per date) -> neutralise (per-date OLS residual on Shenwan L1 dummies and log market cap, D-093) -> standardise again, so the processed value is a unit-dispersion, industry- and size-neutral z-score. `value_raw` is kept; `value` holds the result. Rows without exposures are dropped when neutralising.
- **Base:** none. **Depends on (injected):** Winsorizer | None, Standardizer | None, Neutralizer | None.
- **Used by:** `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_factor_preprocessor.py` (TC-FPP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Winsorizer \| None, Standardizer \| None, Neutralizer \| None -> None | — | callers of the class | — |
| `compute` | Processed FACTOR_PANEL. | pd.DataFrame, pd.DataFrame \| None -> pd.DataFrame | `ValueError`, `SchemaError` | as class | see class |
| `build_log` | What the last compute did. | — -> pd.DataFrame | — | as class | see class |
| `_compute_neutral` (private) | internal helper over 20 lines | pd.DataFrame, pd.DataFrame \| None -> pd.DataFrame | — | internal | — |

### `EarningsYieldFactor` — `quant_cn.factor.library.earnings_yield_factor` (L5)
- **Purpose:** Earnings yield EP_TTM = net profit attributable to parent over the trailing twelve months (PIT, D-092) / total market value at the close of t. Value factor (Basu 1977; Fama & French 1992), EP rather than PE so loss-makers rank low instead of flipping sign.
- **Base:** BaseFactor. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_fundamental_factors.py` (TC-EYF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_raw` | EP per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `MomentumFactor` — `quant_cn.factor.library.momentum_factor` (L5)
- **Purpose:** MOM_{12-1} = P_adj(t - skip) / P_adj(t - window) - 1 on the backward-adjusted close (ratios are PIT-safe, FACTOR_TESTING_DESIGN §11), skipping the most recent month to avoid the short-term reversal (Jegadeesh & Titman 1993). Suspended sessions carry the last close.
- **Base:** BaseFactor. **Depends on (injected):** str, int, int.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_price_factors.py` (TC-MOM-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int, int -> None | `ValueError` | callers of the class | — |
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | 12-1 momentum per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `ProfitGrowthFactor` — `quant_cn.factor.library.profit_growth_factor` (L5)
- **Purpose:** Growth = (NI_TTM(P) - NI_TTM(P - 1 year)) / /NI_TTM(P - 1 year)/ for the latest PIT-visible period P, both TTMs from the versions known at the announcement (the lake's `n_income_attr_p_ttm_yoy`, D-092). Growth / earnings-momentum factor (Jegadeesh & Livnat 2006). Needs eight quarters of history, so it starts about two years after the statements.
- **Base:** BaseFactor. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_fundamental_factors.py` (TC-PGF-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_raw` | TTM profit growth per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `ReversalFactor` — `quant_cn.factor.library.reversal_factor` (L5)
- **Purpose:** REV = -(P_adj(t) / P_adj(t - window) - 1): last month's losers tend to rebound, strongly so in China's retail-driven market (Jegadeesh 1990; Lehmann 1990). Sign flipped so higher values are expected to earn more. Suspended sessions carry the last close.
- **Base:** BaseFactor. **Depends on (injected):** str, int.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_price_factors.py` (TC-REV-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int -> None | `ValueError` | callers of the class | — |
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | Reversal per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `RoeFactor` — `quant_cn.factor.library.roe_factor` (L5)
- **Purpose:** Return on equity ROE_TTM = net profit attributable to parent over the trailing twelve months / equity attributable to parent in the latest PIT-visible balance sheet (both D-092 PIT). Profitability / quality factor (Novy-Marx 2013; Fama & French 2015 RMW).
- **Base:** BaseFactor. **Depends on (injected):** —.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_fundamental_factors.py` (TC-ROE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute_raw` | ROE per stock and session. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `TurnoverFactor` — `quant_cn.factor.library.turnover_factor` (L5)
- **Purpose:** TURN = -mean(turnover_rate_f over the last `window` sessions, at least `min_obs` traded): heavily traded stocks underperform, a liquidity / attention effect that is strong in China (Datar, Naik & Radcliffe 1998; Liu, Stambaugh & Yuan 2019). Suspended sessions are missing, not zero.
- **Base:** BaseFactor. **Depends on (injected):** str, int, int.
- **Used by:** (none yet).
- **Tests:** `tests/factor/test_price_factors.py` (TC-TRN-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str, int, int -> None | `ValueError` | callers of the class | — |
| `lookback` | Sessions of history needed. | — -> int | — | as class | see class |
| `compute_raw` | Turnover per stock and session on the dense session grid. | FactorInputs -> pd.DataFrame | — | as class | see class |

### `SignalCombiner` — `quant_cn.factor.signal_combiner` (L5)
- **Purpose:** score_{i,t} = sum_f w_f z_{f,i,t} / sum_{f available} /w_f/ over the processed factors a stock has at t (at least `min_factors`), then standardised per date: an equal-risk blend of z-scores that tolerates a missing factor instead of dropping the stock.
- **Base:** none. **Depends on (injected):** Mapping[str, float], Standardizer, int.
- **Used by:** `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/factor/test_signal_combiner.py` (TC-SGC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Mapping[str, float], Standardizer, int -> None | `ValueError` | callers of the class | — |
| `compute` | Score rows from processed factor rows. | pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |

### `Compactor` — `quant_cn.lake.compactor` (L2)
- **Purpose:** Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, fill `key_defaults` into NULL key columns, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, BaseStore, Clock.
- **Used by:** `cli.QuantCnCli`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_compactor.py` (TC-CO-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, BaseStore, Clock -> None | — | callers of the class | — |
| `rebuild` | Replace the curated partitions of `spec` (all years, or only `years`). | DatasetSpec, set[int] \| None -> StepReport | `SchemaError`, `LakeError` | as class | see class |

### `DerivedViews` — `quant_cn.lake.derived_views` (L2)
- **Purpose:** Create the `derived` schema views built only from curated/: `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor; PRICE_PANEL columns; retired alias codes absent from stock_basic dropped); `derived.fundamentals_long` = `derived.fundamentals_base` (every statement dataset under curated/fundamentals/ unpivoted to one row per numeric field and announced version, report_type = '1') plus `derived.fundamentals_ttm` (`<flow>_ttm` and `<field>_ttm_yoy` rows from the latest versions known at each announcement, D-092); `derived.fut_holding_brokers` (contract rows of fut_holding without member-category totals, exchange "ZCE" -> "CZCE"; D-079); `derived.fut_daily_one_sided` (fut_daily with vol, amount, oi, oi_chg halved for SHFE/DCE/CZCE/INE before 2020-01-02, flagged two_sided_adjusted; D-079); `derived.industry_l1` (Shenwan L1 validity intervals per stock, PIT rows plus back-filled rows flagged industry_backfilled; l1_pit = rows not back-filled, l1_grouping = any; D-071); `derived.margin_targets` (SZSE official list + SSE proxy from margin_detail, source column; D-084); `derived.universe` / `derived.features` over the UniverseStep / FeatureStep year files (refresh_tables); `derived.ticker_alias` through TickerAliasMap (D-089); then the `quality` schema through QualityViews.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], Sequence[FuturesCategory], Sequence[TickerAlias].
- **Used by:** `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `pipeline.FeatureStep`.
- **Tests:** `tests/lake/test_derived_views.py` (TC-DV-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], Sequence[FuturesCategory], Sequence[TickerAlias] -> None | — | callers of the class | — |
| `refresh` | (Re)create every derived view whose curated inputs exist; drop the others. | — -> list[str] | `LakeError` | as class | see class |
| `refresh_tables` | (Re)create the views over materialised tables (UniverseStep, FeatureStep outputs). | — -> list[str] | `LakeError` | as class | see class |
| `_build_plan` (private) | internal helper over 20 lines | — -> list[tuple[str, list[str], str]] | — | internal | — |

### `EffectiveDateResolver` — `quant_cn.lake.effective_date_resolver` (L2)
- **Purpose:** Turn a dataset's `known_on` value into `effective_date`, the first China trading session the row may be used (FACTOR_TESTING_DESIGN §11): as_is          -> that session, or the next one if the day is closed (same-day data); next_session   -> the lag_sessions-th session strictly after (default 1: FRED, analyst reports; 2: survey visits, disclosed 1-2 days after the visit); period_end_lag -> period end (a YYYYMM month or YYYYMMDD date) + release_lag_days, then the first session on or after (monthly macro without an announce date); period_start_lag -> month (or date) start + release_lag_days, first session on or after (monthly lists published at the start of the month they apply to).
- **Base:** none. **Depends on (injected):** TradingCalendar, DateCodec.
- **Used by:** (none yet).
- **Tests:** `tests/lake/test_effective_date_resolver.py` (TC-EDR-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `get_effective_date` | Effective session for one known-on value under the dataset's rule. | str, DatasetSpec -> str | `ValueError`, `LakeError` | as class | see class |
| `compute` | Copy of `frame` with an `effective_date` column. | pd.DataFrame, DatasetSpec -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |

### `ExposureReader` — `quant_cn.lake.exposure_reader` (L2)
- **Purpose:** Per universe member and session: the Shenwan L1 group in effect (derived.industry_l1, l1_grouping = the PIT row or the back-filled first-known L1, flagged; D-071, D-093) and log market cap (ln of total_mv in CNY, from daily_basic at the close of t). The inputs of FactorPreprocessor's neutralisation.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_lake_reader.py` (TC-EXR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `read_exposures` | Exposures of universe members in [start, end]. | str, str -> pd.DataFrame | `LakeError` | as class | see class |

### `FetchLog` — `quant_cn.lake.fetch_log` (L2)
- **Purpose:** Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost.
- **Base:** BaseFetchLog. **Depends on (injected):** LakeCatalog.
- **Used by:** `cli.QuantCnCli`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_fetch_log.py` (TC-FL-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | `LakeError` | callers of the class | — |
| `mirror_path` | Location of the durable parquet copy. | — -> Path | — | as class | see class |
| `read_done_keys` | Keys recorded for `dataset`. | str -> set[str] | `LakeError` | as class | see class |
| `mark_done` | Upsert one finished key. | str, str, int, Path \| None -> None | `LakeError` | as class | see class |
| `save` | Atomically rewrite `meta/fetch_log.parquet` from the table. | — -> Path | `LakeError` | as class | see class |
| `rebuild_from_mirror` | Rebuild the table from the parquet mirror, then add raw files the mirror does not know. | — -> int | `LakeError` | as class | see class |
| `remove_orphans` | Drop done-rows whose raw file no longer exists (D-073): keys of a replaced sweep layout or raw files moved out of the lake. Empty keys (n_rows = 0, no file by design) and datasets no longer configured are kept. Saves the mirror when anything was removed. | — -> dict[str, list[str]] | `LakeError` | as class | see class |

### `LakeCatalog` — `quant_cn.lake.lake_catalog` (L2)
- **Purpose:** Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta`; one view per dataset and zone; `meta.dataset_meta`; generated INDEX.md files. The DuckDB file is disposable: `rebuild()` recreates it from the parquet files.
- **Base:** none. **Depends on (injected):** Path, Mapping[str, DatasetSpec], bool.
- **Used by:** `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`, `cli.ServiceBuilder`, `lake.QualityViews`, `lake.LakeReader`, `lake.TickerAliasMap`, `cli.ResearchCommands`, `cli.DocumentCommands`.
- **Tests:** `tests/lake/test_lake_catalog.py` (TC-LC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, Mapping[str, DatasetSpec], bool -> None | `LakeError` | callers of the class | — |
| `catalog_path` | Location of the DuckDB catalog file. | — -> Path | — | as class | see class |
| `connection` | The shared DuckDB connection, opened lazily with zones, schemas and dataset_meta. | — -> duckdb.DuckDBPyConnection | `LakeError` | as class | see class |
| `list_raw_files` | Raw parquet files of a dataset, sorted by name. | DatasetSpec -> list[Path] | — | as class | see class |
| `refresh_view` | (Re)create `raw.<name>` and `curated.<name>` views for whatever files exist. | DatasetSpec -> None | `LakeError` | as class | see class |
| `refresh_views` | refresh_view for every configured dataset. | — -> None | `LakeError` | as class | see class |
| `rebuild` | Delete the DuckDB file and recreate schemas, dataset_meta and all views from parquet. Tables owned by FetchLog/RunLog are restored by their own classes. | — -> None | `LakeError` | as class | see class |
| `write_indexes` | Generate INDEX.md in the lake root and each zone: datasets, file counts, last update. | — -> list[Path] | `LakeError` | as class | see class |
| `close` | Close the DuckDB connection if open. | — -> None | — | as class | see class |
| `_write_dataset_meta` (private) | internal helper over 20 lines | duckdb.DuckDBPyConnection -> None | — | internal | — |

### `LakeQuery` — `quant_cn.lake.lake_query` (L2)
- **Purpose:** Run read queries against the catalog views; the only way code above the lake reads data.
- **Base:** none. **Depends on (injected):** LakeCatalog.
- **Used by:** `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `cli.ServiceBuilder`, `data_loading.FetcherFactory`, `lake.QualityViews`, `lake.ReleaseLagChecker`, `lake.LakeReader`, `lake.TickerAliasMap`, `pipeline.UniverseStep`, `lake.ExposureReader`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`, `cli.ResearchCommands`, `cli.DocumentCommands`, `data_loading.DocumentDownloader`, `lake.StatementVersionReader`.
- **Tests:** `tests/lake/test_lake_query.py` (TC-LQ-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | — | callers of the class | — |
| `sql` | Execute a query and return the result as a DataFrame. | str, Sequence[object] \| None -> pd.DataFrame | `LakeError` | as class | see class |
| `has_view` | True if `schema.view` exists in the catalog. | str -> bool | `LakeError` | as class | see class |
| `read_prices` | Adjusted daily prices from `derived.prices_adj` for a date range. | str, str, Sequence[str] \| None -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |
| `register_frame` | Expose an in-memory frame as a view so SQL can join it with lake views. | str, pd.DataFrame -> str | `ValueError`, `LakeError` | as class | see class |
| `list_views` | Every lake view as "schema.view", plus registered frames by bare name. | — -> list[str] | `LakeError` | as class | see class |

### `LakeReader` — `quant_cn.lake.lake_reader` (L2)
- **Purpose:** The read API factors, the universe step and notebooks use (SRC_DESIGN §2.2b, D-089): one curated dataset as a panel, dense or sparse prices, point-in-time fundamentals, reference tables (in-memory frames and view discovery: LakeQuery). Retired codes are mapped to their surviving codes on every per-stock read (TickerAliasMap, new code wins); every output is validated with its schema; an optional PanelCache serves repeated reads. LakeQuery stays the raw SQL layer underneath.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], PitAligner, TickerAliasMap, TradingCalendar, PanelCache | None.
- **Used by:** `cli.ServiceBuilder`, (none yet), `factor.FactorFactory`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`.
- **Tests:** `tests/lake/test_lake_reader.py` (TC-LRD-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Mapping[str, DatasetSpec], PitAligner, TickerAliasMap, TradingCalendar, PanelCache \| None -> None | — | callers of the class | — |
| `read_panel` | One curated dataset over a date range as a long panel, sorted by primary key. | str, str, str, Sequence[str] \| None, Sequence[str] \| None -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |
| `read_prices` | Daily prices (raw and backward-adjusted close) for a date range. | str, str, Sequence[str] \| None, bool -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |
| `read_fundamentals_pit` | Point-in-time fundamentals per session (PitAligner), statements filed under a retired code attached to the surviving code (the new code's value wins on the same day). | Sequence[str] \| None, str, str, Sequence[str] \| None -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |
| `read_universe` | The tradeable universe per session (UniverseStep output). | str, str, bool -> pd.DataFrame | `LakeError` | as class | see class |
| `read_reference` | A whole reference table (curated under reference/: stock_basic, namechange, trade_cal, index_daily, index_classify, fund_basic, fut_basic, ...). | str -> pd.DataFrame | `LakeError` | as class | see class |
| `_load_panel` (private) | internal helper over 20 lines | DatasetSpec, str, str, str, Sequence[str] \| None, list[str] -> pd.DataFrame | — | internal | — |

### `PanelCache` — `quant_cn.lake.panel_cache` (L2)
- **Purpose:** Keep recently read panels in memory, keyed by (method, arguments), least recently used evicted first once the total size exceeds `max_bytes`. Frames are stored and returned as shallow copies: with pandas copy-on-write, a caller modifying its frame never changes the cached one. On by default in notebooks, off in pipelines (LakeReader decides).
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `lake.LakeReader`, `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_panel_cache.py` (TC-PCH-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | `ValueError` | callers of the class | — |
| `size_bytes` | Bytes held by cached frames. | — -> int | — | as class | see class |
| `find` | The cached frame for `key`, marking it most recently used. | Hashable -> pd.DataFrame \| None | — | as class | see class |
| `add` | Cache `frame` under `key`, evicting least recently used entries to stay under the cap. | Hashable, pd.DataFrame -> None | — | as class | see class |
| `remove_all` | Empty the cache (e.g. after a curate run changed the lake). | — -> None | — | as class | see class |

### `ParquetWriter` — `quant_cn.lake.parquet_writer` (L2)
- **Purpose:** Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file.
- **Base:** BaseStore. **Depends on (injected):** Path.
- **Used by:** `cli.QuantCnCli`, `cli.ServiceBuilder`, `pipeline.UniverseStep`, `pipeline.EvaluationStep`, `pipeline.FeatureStep`.
- **Tests:** `tests/lake/test_parquet_writer.py` (TC-PW-001..008).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `get_raw_path` | Target path of one raw fetch key. | DatasetSpec, str -> Path | — | as class | see class |
| `get_curated_path` | Target path of one curated partition. | DatasetSpec, int \| None -> Path | — | as class | see class |
| `write_raw` | Persist one fetch key's rows, dtypes coerced by the dataset schema (dates stay strings); an existing file is kept as `<file>.prev` until `rebuild` confirms it (D-083). | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition after validating it against the dataset schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |
| `write_derived` | Persist one year of a materialised derived table (e.g. the universe). | str, int, pd.DataFrame -> Path | `LakeError` | as class | see class |
| `write_table` | Persist a whole small table (reports under derived/, logs under meta/). | str, str, pd.DataFrame -> Path | `ValueError`, `LakeError` | as class | see class |

### `PitAligner` — `quant_cn.lake.pit_aligner` (L2)
- **Purpose:** Align fundamentals to trading days without look-ahead. A version announced on `known_on` (f_ann_date / ann_date) becomes effective on the first trading day strictly after it; on each day the visible value of a field is the latest report period effective so far, in its latest effective restatement. Older-period restatements never replace a newer period. Built as the DuckDB view `derived.fundamentals_states` (one row per change) and read with an ASOF JOIN from trading days.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, DateCodec.
- **Used by:** `pipeline.CuratePipeline`, `research_space/main.ipynb`, `pipeline.DeriveStep`, `cli.ServiceBuilder`, `lake.LakeReader`.
- **Tests:** `tests/lake/test_pit_aligner.py` (TC-PAD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, DateCodec -> None | — | callers of the class | — |
| `refresh` | (Re)create `derived.fundamentals_states` from derived.fundamentals_long and the curated trading calendar. | — -> str | `LakeError` | as class | see class |
| `read_aligned` | Point-in-time values for every trading day in [start, end] and every (ticker, field) that has become visible by that day. | str, str, Sequence[str] \| None, Sequence[str] \| None -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |

### `ProjectCatalog` — `quant_cn.lake.project_catalog` (L2)
- **Purpose:** Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings, plus views tree, class_graph, stale and todo. Markdown and code stay the source of truth; the schema is dropped and rebuilt, never edited.
- **Base:** none. **Depends on (injected):** LakeCatalog, CodeTableBuilder, DocTableBuilder, Mapping[str, DatasetSpec], ContractLinter, Clock.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/lake/test_project_catalog.py` (TC-PJC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, CodeTableBuilder, DocTableBuilder, Mapping[str, DatasetSpec], ContractLinter, Clock -> None | — | callers of the class | — |
| `rebuild` | Drop and recreate every table and view of schema `project` in one transaction. | bool -> dict[str, int] | `LakeError`, `RuntimeError` | as class | see class |

### `QualityViews` — `quant_cn.lake.quality_views` (L2)
- **Purpose:** Create the `quality` schema: cross-source comparisons that report, never overwrite (D-065). `quality.margin_targets_agreement` (SSE eligibility proxy vs margin_secs, D-084); `quality.price_mismatches` / `quality.price_crosscheck` (Tushare daily close vs BaoStock, relative tolerance 1e-6, per row / per day, D-085); `quality.adj_crosscheck` (adjustment step at each BaoStock dividend date vs Tushare adj_factor).
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery.
- **Used by:** `lake.DerivedViews.refresh`.
- **Tests:** `tests/lake/test_quality_views.py` (TC-QV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery -> None | — | callers of the class | — |
| `refresh` | (Re)create every quality view whose inputs exist; drop the others. | — -> list[str] | `LakeError` | as class | see class |

### `RebuildAudit` — `quant_cn.lake.rebuild_audit` (L2)
- **Purpose:** Record, on `rebuild`, what changed below raw/ since the last one. Fetch-log rows whose raw file is gone go to meta/manifest/fetch_log_orphans.json (D-073). Raw files rewritten by a refetch keep their previous version as `<file>.prev` (ParquetWriter); `record_rewrites` lists each with old and new row counts in meta/manifest/raw_rewrites.json and then deletes the `.prev` copies, so every forced refetch is auditable (D-083).
- **Base:** none. **Depends on (injected):** Path, Clock.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_rebuild_audit.py` (TC-RA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, Clock -> None | — | callers of the class | — |
| `record_orphans` | Write the fetch-log orphans removed by this rebuild. | dict[str, list[str]] -> Path | `LakeError` | as class | see class |
| `record_rewrites` | Record every rewritten raw file (old vs new rows) and delete the kept `.prev` copies. | — -> list[dict[str, object]] | `LakeError` | as class | see class |

### `WatchlistBuilder` — `quant_cn.portfolio.watchlist_builder` (L5)
- **Purpose:** Join the user's buy targets (`Config.watchlist`) with the latest unadjusted close, daily_basic valuation, 52-week range, weekly closes and the report_rc consensus; compute gap to the buy price, status (in / near / far) and PE and dividend yield at the buy price; write `watchlist.json` for the chain app (plan 15 ph7, D-120).
- **Base:** none. **Depends on (injected):** `Config`, `LakeQuery`, `DateCodec`.
- **Used by:** `cli.ResearchCommands` (`watchlist` command).
- **Tests:** `tests/portfolio/test_watchlist_builder.py` (TC-WB-001..009).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build` | the watchlist document as of the latest day in curated.daily | () -> dict {as_of, near_pct, entries, missing} | LakeError | `write` | TC-WB-001..007, 009 |
| `write` | build and write `watchlist.json` into the app data dir | out_dir: Path -> Path | LakeError | `cli.ResearchCommands._run_watchlist` | TC-WB-008 |
| `compute_status` | classify a price against the top of its buy range | price, buy_high, near_pct -> "in" / "near" / "far" | — | `build` | TC-WB-002 |

### `ReleaseLagChecker` — `quant_cn.lake.release_lag_checker` (L2)
- **Purpose:** For every dataset with `known_on_rule: period_end_lag` and `release_dates` set, measure the observed lag (release date - period end) in that curated release-date dataset and count releases that came later than the rule. A rule earlier than any observed release is look-ahead; D-086 raises it to the observed maximum and `make check` warns if it recurs. The period of a release is the last month end before it, or its own month end when the release falls on/after day 25 (month-end PMI releases).
- **Base:** none. **Depends on (injected):** LakeQuery, Mapping[str, DatasetSpec], str.
- **Used by:** `cli.ResearchCommands`.
- **Tests:** `tests/lake/test_release_lag_checker.py` (TC-RLC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, Mapping[str, DatasetSpec], str -> None | — | callers of the class | — |
| `compute` | One row per checked dataset. | — -> pd.DataFrame | `LakeError` | as class | see class |
| `build_lines` | Human-readable lines of a compute() result. | pd.DataFrame -> list[str] | — | as class | see class |

### `RunLog` — `quant_cn.lake.run_log` (L2)
- **Purpose:** Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging.
- **Base:** BaseRunLog. **Depends on (injected):** LakeCatalog, Clock.
- **Used by:** `cli.QuantCnCli`, `cli.ServiceBuilder`, `cli.ResearchCommands`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, Clock -> None | `LakeError` | callers of the class | — |
| `open_run` | Insert the run row (dataset and key NULL, status "running"). | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one key event. | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Set status, message and finished_at on the run row. | str, str, str -> None | `LakeError` | as class | see class |

### `StatementVersionReader` — `quant_cn.lake.statement_version_reader` (L2)
- **Purpose:** Read every company's statement values as known on one date: per (company, period, field) the version with the latest known_on <= as_of (D-092 versions), retired codes mapped to surviving codes (plan 16 ph1).
- **Base:** none. **Depends on (injected):** LakeQuery, TickerAliasMap, DateCodec.
- **Used by:** (none yet; pipeline.DiscoveryStep plan 16 ph6).
- **Tests:** `tests/lake/test_statement_version_reader.py` (TC-SVR-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, TickerAliasMap, DateCodec -> None | — | callers of the class | — |
| `read_versions` | statement values per (company, period, field) known on as_of | Sequence[str], str, str -> pd.DataFrame | `LakeError` | callers | TC-SVR-001..004 |

### `TickerAliasMap` — `quant_cn.lake.ticker_alias_map` (L2)
- **Purpose:** Map retired codes to their surviving codes so a company has one history. Tushare keeps a retired code's rows and back-fills the same history under the new code, but some datasets (stk_limit, moneyflow, margin_detail) exist only under the old code before the change. `refresh` builds `derived.ticker_alias`: pairs detected from the data (a code missing from stock_basic whose closes equal a listed code's on >= 20 shared dates, >= 99% equal) plus the config pairs; every candidate keeps its match statistics, and an old code matching more than one listed code is kept but not accepted. `normalize_codes` renames accepted old codes and, where both codes have a row for the same key, keeps the new code's row.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Sequence[TickerAlias].
- **Used by:** `lake.DerivedViews`, `lake.LakeReader`, `cli.ServiceBuilder`, `lake.StatementVersionReader`.
- **Tests:** `tests/lake/test_ticker_alias_map.py` (TC-TAM-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Sequence[TickerAlias] -> None | — | callers of the class | — |
| `refresh` | (Re)create `derived.ticker_alias`. | — -> str \| None | `LakeError` | as class | see class |
| `get_pairs` | Accepted old -> new pairs (read once per refresh). | — -> dict[str, str] | `LakeError` | as class | see class |
| `normalize_codes` | Rename accepted old codes to new codes; on a duplicate key the new code's row wins. | pd.DataFrame, Sequence[str] -> pd.DataFrame | `LakeError` | as class | see class |
| `list_codes` | `codes` plus the old codes of any requested new code, so a filter sees both. | Sequence[str] -> list[str] | `LakeError` | as class | see class |

### `TradingCalendar` — `quant_cn.lake.trading_calendar` (L2)
- **Purpose:** Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake; loads lazily so it works after trade_cal is fetched in the same run.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.ServiceBuilder`, `lake.EffectiveDateResolver`, `lake.LakeReader`, `factor.FactorFactory`.
- **Tests:** `tests/lake/test_trading_calendar.py` (TC-TCA-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `refresh` | Drop the cached calendar so the next call re-reads trade_cal. | — -> None | — | as class | see class |
| `list_sessions` | Trading days within [start, end]. | str, str -> list[str] | `LakeError` | as class | see class |
| `is_open` | True if `date` is a trading day. | str -> bool | `LakeError` | as class | see class |
| `get_next` | First trading day strictly after `date`. | str -> str | `LakeError` | as class | see class |
| `get_prev` | Last trading day strictly before `date`. | str -> str | `LakeError` | as class | see class |

### `CompactStep` — `quant_cn.pipeline.curate_pipeline` (L6)
- **Purpose:** Adapt Compactor to a pipeline step: one unit per dataset.
- **Base:** BaseStep. **Depends on (injected):** Compactor, Sequence[DatasetSpec].
- **Used by:** `pipeline.CuratePipeline`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Compactor, Sequence[DatasetSpec] -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Datasets to compact. | — -> list[str] | — | as class | see class |
| `run` | Rebuild curated partitions for every dataset. | str, ProgressHook \| None -> StepReport | `SchemaError`, `LakeError` | as class | see class |

### `DeriveStep` — `quant_cn.pipeline.curate_pipeline` (L6)
- **Purpose:** Build the derived views and the PIT states view, then record a digest per derived view.
- **Base:** BaseStep. **Depends on (injected):** DerivedViews, PitAligner, LakeQuery, Path.
- **Used by:** `pipeline.CuratePipeline`, `pipeline.FeatureStep`, `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DerivedViews, PitAligner, LakeQuery, Path -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | One unit: the derived layer. | — -> list[str] | — | as class | see class |
| `run` | Refresh derived views (and PIT states when fundamentals exist), write digests. | str, ProgressHook \| None -> StepReport | `LakeError` | as class | see class |
| `build_digests` | md5 over every row of each view, rows ordered by their text form; equal digests mean byte-identical derived data. | Sequence[str] -> dict[str, str] | `LakeError` | as class | see class |
| `refresh_digests` | Recompute the digests of views built after this step (derived.features) and merge them into meta/manifest/derived_digests.json. | Sequence[str] -> dict[str, str] | `LakeError` | as class | see class |

### `CuratePipeline` — `quant_cn.pipeline.curate_pipeline` (L6)
- **Purpose:** Rebuild everything below raw/: compact every dataset, create derived views and PIT states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json.
- **Base:** none. **Depends on (injected):** Config, Compactor, DerivedViews, PitAligner, LakeQuery, LakeCatalog, BaseRunner, BaseStep | None, DeriveStep | None, BaseStep | None.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, Compactor, DerivedViews, PitAligner, LakeQuery, LakeCatalog, BaseRunner, BaseStep \| None, DeriveStep \| None, BaseStep \| None -> None | — | callers of the class | — |
| `run` | Compact the datasets (default all), then derive and index. | Sequence[str] \| None -> PipelineReport | `ConfigError`, `SchemaError`, `LakeError` | as class | see class |

### `FetchStep` — `quant_cn.pipeline.download_pipeline` (L6)
- **Purpose:** Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the calendar fetched earlier in the run is visible), catalog view refreshed after the run.
- **Base:** BaseStep. **Depends on (injected):** BaseFetcher, LakeCatalog, str, str, bool.
- **Used by:** `pipeline.DownloadPipeline.run`.
- **Tests:** `tests/pipeline/test_download_pipeline.py` (TC-DP-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseFetcher, LakeCatalog, str, str, bool -> None | — | callers of the class | — |
| `name` | The dataset name. | — -> str | — | as class | see class |
| `list_units` | Compute the dataset's keys for the range. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Fetch the prepared keys, then refresh the dataset's catalog views. | str, ProgressHook \| None -> StepReport | `DataSourceError`, `PermissionDeniedError`, `SchemaError`, `LakeError` | as class | see class |

### `DownloadPipeline` — `quant_cn.pipeline.download_pipeline` (L6)
- **Purpose:** Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes; `dry_run` lists pending keys without calling the API.
- **Base:** none. **Depends on (injected):** Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_download_pipeline.py` (TC-DP-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec -> None | — | callers of the class | — |
| `run` | Download the requested datasets (default: config.download.order). | Sequence[str] \| None, str \| None, str \| None, bool, bool -> PipelineReport | `ConfigError`, `ValueError`, `DataSourceError` | as class | see class |

### `EvaluationStep` — `quant_cn.pipeline.evaluation_step` (L6)
- **Purpose:** Evaluate every factor in derived.features (FactorEvaluator, one factor at a time to bound memory, forward returns from the open of t+1 on dense prices), apply the campaign-level adjustment once over all factor x horizon tests, and write derived/reports/<campaign>/ ic_series, ic_test and quantiles; the campaign's TrialLog (meta/trials/<campaign>.parquet) is resumed and saved, so re-running the same variants does not inflate N.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, LakeReader, FactorEvaluator, ParquetWriter, str, Mapping[str, Mapping[str, object]], str.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_evaluation_step.py` (TC-ES-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, LakeReader, FactorEvaluator, ParquetWriter, str, Mapping[str, Mapping[str, object]], str -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Factors to evaluate. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Evaluate, adjust, write reports and the trial log. | str, ProgressHook \| None -> StepReport | `LakeError`, `SchemaError` | as class | see class |

### `FeatureStep` — `quant_cn.pipeline.feature_step` (L6)
- **Purpose:** Build derived/features, one file per year from the campaign start: the six library factors (FactorFactory, PIT inputs from LakeReader), restricted to universe members, preprocessed (winsorise -> standardise -> neutralise on Shenwan L1 + log market cap, D-093) and the combined "score" (SignalCombiner), as FACTOR_PANEL. Runs inside curate after the derived views; then refreshes derived.features and merges its digest so `make lake-rebuild` proves the features byte-identical.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, LakeReader, FactorFactory, ExposureReader, FactorPreprocessor, SignalCombiner, ParquetWriter, DerivedViews, DeriveStep, str.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_feature_step.py` (TC-FS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, LakeReader, FactorFactory, ExposureReader, FactorPreprocessor, SignalCombiner, ParquetWriter, DerivedViews, DeriveStep, str -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Years from the campaign start to the last universe session. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Build and write every year, then refresh the view and its digest. | str, ProgressHook \| None -> StepReport | `LakeError`, `SchemaError`, `ConfigError` | as class | see class |

### `PrefectRunner` — `quant_cn.pipeline.prefect_runner` (L6)
- **Purpose:** Same contract as LocalRunner, executed as a Prefect flow named "quant_cn <kind>" whose run name is the RunLog run id; every step is a Prefect task with a progress artifact over its units (keys). RunLog stays the source of truth (D-022); steps and fetchers never import Prefect. A permission failure marks the step blocked and continues; any other project error fails the flow, closes the run as failed and re-raises.
- **Base:** BaseRunner. **Depends on (injected):** BaseRunLog, int.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_prefect_runner.py` (TC-PFR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRunLog, int -> None | — | callers of the class | — |
| `run` | See BaseRunner.run; the flow appears in the Prefect UI while it runs. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `PipelineReport` — `quant_cn.pipeline.runner` (L6)
- **Purpose:** Result of one pipeline run: its id, overall status and one StepReport per step.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.BaseRunner`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_blocked` | Names of steps blocked by missing permissions. | — -> list[str] | — | as class | see class |
| `to_frame` | One row per step for display or logging. | — -> pd.DataFrame | — | as class | see class |

### `BaseRunner` — `quant_cn.pipeline.runner` (L6)
- **Purpose:** Extension point for how steps are executed (local now, Prefect later, D-022); steps never import the runner's backend.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`, `pipeline.PrefectRunner`, `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Execute steps in order under one run id. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `LocalRunner` — `quant_cn.pipeline.runner` (L6)
- **Purpose:** Run steps serially in this process with a rich progress bar per step; a permission failure marks the step blocked and continues; any other project error closes the run as failed and re-raises (finished keys stay done).
- **Base:** BaseRunner. **Depends on (injected):** BaseRunLog, Console | None, bool.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRunLog, Console \| None, bool -> None | — | callers of the class | — |
| `run` | See BaseRunner.run. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `UniverseStep` — `quant_cn.pipeline.universe_step` (L6)
- **Purpose:** Build UNIVERSE_PANEL: one row per stock listed on each session (list_date <= t < delist_date; retired alias codes are absent from stock_basic, D-053), in_universe = 1 when no rule excludes it, and every failing rule kept in `reason` (comma-joined): exchange (not in config, BJ by default, D-054), st (name in effect at t contains ST or starts with PT, from namechange start dates), delisting (name contains 退, 退市整理期), new_listing (fewer than min_sessions sessions since the first session on/after list_date), suspended (no daily bar at t). Delisted stocks stay in history (no survivorship). Point in time: the name at t is the namechange row with the latest start_date <= t (FACTOR_TESTING_DESIGN §11). One unit per calendar year, written to derived/universe/year=YYYY.
- **Base:** BaseStep. **Depends on (injected):** LakeQuery, ParquetWriter, UniverseConfig.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/core/docs/test_contract_checker.py`, `tests/pipeline/test_universe_step.py` (TC-US-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery, ParquetWriter, UniverseConfig -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | Years to build: from rules.start to the last daily session. | — -> list[str] | `LakeError` | as class | see class |
| `run` | Build and write every year. | str, ProgressHook \| None -> StepReport | `LakeError`, `SchemaError` | as class | see class |

### `ServiceBuilder` — `quant_cn.service_builder` (L8)
- **Purpose:** Wire services for the CLI commands (the composition root's constructors): download and curate pipelines with the chosen runner, and the project catalog.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `cli.QuantCnCli`, `cli.ResearchCommands`.
- **Tests:** `tests/test_cli.py` (TC-QCC-002..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `build_download_pipeline` | DownloadPipeline wired to the lake, Tushare client and chosen runner. | Config, LakeCatalog, bool, str -> DownloadPipeline | — | as class | see class |
| `build_curate_pipeline` | CuratePipeline wired to compactor, derived views, PIT aligner and chosen runner. | Config, LakeCatalog, bool, str -> CuratePipeline | — | as class | see class |
| `build_features` | FeatureStep wired from config/factors.yaml (factors and campaign settings). | Config, LakeCatalog, LakeQuery, DerivedViews, DeriveStep -> FeatureStep | — | as class | see class |
| `build_runner` | LocalRunner, or PrefectRunner for name "prefect" (optional extra "flows", D-022). | RunLog, str, bool -> BaseRunner | `ModuleNotFoundError` | as class | see class |
| `build_reader` | The lake read API (D-089): PIT aligner, alias map, calendar and an optional cache. | Config, LakeCatalog, bool -> LakeReader | — | as class | see class |
| `build_evaluation` | EvaluationStep for the configured campaign (2,000 seeded block-bootstrap resamples). | Config, LakeCatalog -> EvaluationStep | — | as class | see class |
| `build_project_catalog` | ProjectCatalog over the repository with the contract linter. | Config, LakeCatalog -> ProjectCatalog | — | as class | see class |

### `BlockBootstrap` — `quant_cn.statistic.block_bootstrap` (L4)
- **Purpose:** Resample a time series (or several aligned series with the same draws) in blocks so serial correlation survives: stationary bootstrap with geometric block lengths (Politis & Romano 1994) or circular block bootstrap with fixed blocks (Politis & Romano 1992); both wrap around. Seeded, so reports reproduce byte for byte.
- **Base:** none. **Depends on (injected):** int, int, Method.
- **Used by:** `statistic.IcSignificance`, `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_block_bootstrap.py` (TC-BB-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int, int, Method -> None | `ValueError` | callers of the class | — |
| `compute_block` | Expected block length for a horizon. | int -> int | — | as class | see class |
| `build_indices` | B resampled index vectors of length T. | int, int -> np.ndarray | — | as class | see class |
| `compute_distribution` | The statistic recomputed on every resample. | Values, Callable[[np.ndarray], float], int -> np.ndarray | `ValueError` | as class | see class |
| `compute_interval` | Percentile confidence interval and bootstrap p-value of H0: statistic = 0. | Values, Callable[[np.ndarray], float], int, float -> dict[str, float] | `ValueError` | as class | see class |

### `HacVariance` — `quant_cn.statistic.hac_variance` (L4)
- **Purpose:** Heteroskedasticity- and autocorrelation-consistent variance of a sample mean with the Bartlett kernel (Newey & West 1987; lag rule of Newey & West 1994), for series whose observations overlap (IC_t at horizon h is serially correlated by construction). By default the series is AR(1)-prewhitened before the kernel and recoloured after (Andrews & Monahan 1992): with the plain rule-of-thumb lag, 95% intervals covered only 89.8% on AR(1) phi = 0.6 and 88.4% on an overlapping 20-session MA(19), against 95.1% and 99.0% prewhitened (D-090). Used for the NW t on mean IC and by every HAC test.
- **Base:** none. **Depends on (injected):** int | None, bool.
- **Used by:** `statistic.IcSignificance`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_hac_variance.py` (TC-HAC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int \| None, bool -> None | `ValueError` | callers of the class | — |
| `compute_lag` | Bartlett truncation lag. | int, int -> int | — | as class | see class |
| `compute_long_run_variance` | Bartlett-kernel long-run variance of a series. | Values, int -> float | `ValueError` | as class | see class |
| `compute_hac_variance` | Long-run variance used for inference: prewhitened (default) or plain Bartlett. | Values, int -> float | `ValueError` | as class | see class |
| `compute_t` | Newey-West t statistic of the mean. | Values, int -> dict[str, float] | `ValueError` | as class | see class |

### `IcCalculator` — `quant_cn.statistic.ic_calculator` (L4)
- **Purpose:** Per-date information coefficient between factor values and forward returns across the universe: IC_t = corr_rank(f_{i,t}, r_{i,t->t+h}) (Spearman; Pearson on the values as a variant). Forward returns are tradeable (FACTOR_TESTING_DESIGN §10, §11): the factor known at the close of t is traded at the next open, r = P_adj close(t+h) / P_adj open(t+1) - 1; close-to-close is available for comparison only.
- **Base:** none. **Depends on (injected):** Method, int.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_ic_calculator.py` (TC-ICC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Method, int -> None | `ValueError` | callers of the class | — |
| `build_forward_returns` | Forward returns per stock, session and horizon from dense adjusted prices. | pd.DataFrame, Sequence[int], Entry -> pd.DataFrame | `SchemaError`, `ValueError` | as class | see class |
| `compute` | IC_t per date, factor and horizon. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |

### `IcSignificance` — `quant_cn.statistic.ic_significance` (L4)
- **Purpose:** The §2 tests for one factor at one horizon: Newey-West t on mean IC (Newey & West 1987, 1994, prewhitened per D-090), stationary block-bootstrap CI of mean IC and ICIR (Politis & Romano 1994), Fisher-z / Stouffer screen, sign consistency per sub-period, single break in mean (Bai & Perron 1998; sup-F critical values of Andrews 1993), plus Pesaran-Timmermann directional accuracy (1992, 2009) and an exponential decay fit across horizons.
- **Base:** none. **Depends on (injected):** HacVariance, BlockBootstrap, Mapping[str, tuple[str, str]].
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_ic_significance.py` (TC-ICS-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | HacVariance, BlockBootstrap, Mapping[str, tuple[str, str]] -> None | — | callers of the class | — |
| `compute` | IC_TEST rows for one factor and horizon. | pd.DataFrame -> pd.DataFrame | `SchemaError`, `ValueError` | as class | see class |
| `compute_break` | Single structural break in mean IC. | pd.DataFrame, int -> dict[str, object] | `ValueError` | as class | see class |
| `compute_pesaran_timmermann` | Directional accuracy of sign(signal) for sign(outcome) beyond chance. | Values, Values -> dict[str, float] | `ValueError` | as class | see class |
| `compute_decay` | Horizon profile of mean IC (D-095): peak horizon, exponential decay beyond the peak, accumulation ratio. | Mapping[int, float] -> dict[str, float] | `ValueError` | as class | see class |
| `_build_full_rows` (private) | internal helper over 20 lines | pd.DataFrame, str, int, int -> list[dict[str, object]] | — | internal | — |
| `_build_row` (private) | internal helper over 20 lines | str, int, str, str, float, float \| None, float \| None, float \| None, tuple[float, float] \| None -> dict[str, object] | — | internal | — |

### `MultipleTestingAdjuster` — `quant_cn.statistic.multiple_testing_adjuster` (L4)
- **Purpose:** Adjust the p-values of many factor tests run in one campaign: Holm step-down FWER (Holm 1979), Benjamini-Hochberg FDR (1995), Benjamini-Hochberg-Yekutieli FDR under arbitrary dependence (2001), Romano-Wolf bootstrap step-down FWER (Romano & Wolf 2005, 2016), and the Harvey-Liu-Zhu (2016) /t/ >= 3.0 hurdle. Pure arithmetic on arrays.
- **Base:** none. **Depends on (injected):** float.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_multiple_testing_adjuster.py` (TC-MTA-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float -> None | — | callers of the class | — |
| `compute_holm` | Holm step-down adjusted p-values (family-wise error). | Values -> np.ndarray | — | as class | see class |
| `compute_bh` | Benjamini-Hochberg adjusted p-values (false discovery rate). | Values, float -> np.ndarray | — | as class | see class |
| `compute_bhy` | Benjamini-Hochberg-Yekutieli adjusted p-values (FDR under arbitrary dependence). | Values -> np.ndarray | — | as class | see class |
| `compute_romano_wolf` | Romano-Wolf step-down adjusted p-values from bootstrap null statistics. | Values, np.ndarray -> np.ndarray | `ValueError` | as class | see class |
| `build_adjusted` | Fill adjusted p-values and the HLZ flag on one metric (and window) across factors. | pd.DataFrame, str, str \| None, np.ndarray \| None -> pd.DataFrame | `SchemaError`, `ValueError` | as class | see class |

### `Neutralizer` — `quant_cn.statistic.neutralizer` (L4)
- **Purpose:** Remove what industry membership and numeric exposures (e.g. log market cap) explain in a factor, date by date: the residual of OLS x_i = a + sum_g d_{ig} b_g + sum_k z_{ik} c_k + e_i, so the factor's IC is not an industry or size bet in disguise.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `factor.FactorPreprocessor`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_neutralizer.py` (TC-NEU-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `compute` | Replace `column` by its per-date OLS residual. | pd.DataFrame, str, Sequence[str], Sequence[str], str -> pd.DataFrame | `KeyError` | as class | see class |

### `QuantileReturns` — `quant_cn.statistic.quantile_returns` (L4)
- **Purpose:** Sort names into n quantiles of the factor within each date and horizon, and report each quantile's equal-weighted mean forward return plus the long-short spread (top minus bottom, stored as quantile 0): the monotone "ladder" that complements the IC.
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_quantile_returns.py` (TC-QR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | `ValueError` | callers of the class | — |
| `compute` | Mean forward return per quantile, date, factor and horizon. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `SchemaError` | as class | see class |

### `ReturnStats` — `quant_cn.statistic.return_stats` (L4)
- **Purpose:** Summarise a series of period returns: annualised mean and volatility, Sharpe (per period and annualised with sqrt(244 / h)), maximum drawdown of the compounded path, hit rate, skewness and non-excess kurtosis (the PSR / DSR inputs of Bailey & López de Prado 2012).
- **Base:** none. **Depends on (injected):** int.
- **Used by:** `factor.FactorEvaluator`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_return_stats.py` (TC-RS-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | int -> None | — | callers of the class | — |
| `compute` | Statistics of non-overlapping returns of length h sessions. | Values, int -> dict[str, float] | `ValueError` | as class | see class |

### `Standardizer` — `quant_cn.statistic.standardizer` (L4)
- **Purpose:** Put factor values on a common scale within each date: z = (x - m) / s with m the equal-weighted mean (or a weighted mean, e.g. cap weights as in Barra-style exposures) and s the equal-weighted standard deviation, so the cross-section has unit dispersion.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `factor.FactorPreprocessor`, `factor.SignalCombiner`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_standardizer.py` (TC-STD-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `compute` | z-score one column within each group. | pd.DataFrame, str, str, str \| None -> pd.DataFrame | `KeyError` | as class | see class |

### `TrialLog` — `quant_cn.statistic.trial_log` (L4)
- **Purpose:** Record every factor / parameter / horizon variant evaluated in a campaign, including the failures, because the deflated Sharpe ratio (Bailey & López de Prado 2014) and the multiple-testing adjusters need the number and dispersion of all trials, not just the winners. Append-only: trials get sequential ids and can never be edited or removed. No I/O: the caller persists `build_frame()` and resumes with `from_frame()`.
- **Base:** none. **Depends on (injected):** str.
- **Used by:** `factor.FactorEvaluator`, `pipeline.EvaluationStep`.
- **Tests:** `tests/statistic/test_trial_log.py` (TC-TL-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | str -> None | `ValueError` | callers of the class | — |
| `n_trials` | Number of trials recorded (N for the deflated Sharpe ratio). | — -> int | — | as class | see class |
| `add_trial` | Append one evaluated variant. | str, Mapping[str, object], int, float \| None, float \| None -> str | `TypeError` | as class | see class |
| `find_trial` | The id of an already recorded identical variant (re-running a campaign does not inflate N). | str, Mapping[str, object], int -> str \| None | `TypeError` | as class | see class |
| `build_frame` | The log as a TRIAL_LOG frame (a copy). | — -> pd.DataFrame | — | as class | see class |
| `from_frame` | Resume a campaign's log from a saved TRIAL_LOG frame. | str, pd.DataFrame -> TrialLog | `ValueError`, `SchemaError` | as class | see class |

### `Winsorizer` — `quant_cn.statistic.winsorizer` (L4)
- **Purpose:** Clip extreme factor values within each date so a few outliers do not dominate ranks, z-scores or regressions: median +- k * 1.4826 * MAD (robust default) or the q / 1 - q cross-sectional quantiles.
- **Base:** none. **Depends on (injected):** Method, float, float.
- **Used by:** `factor.FactorPreprocessor`, `cli.ServiceBuilder`.
- **Tests:** `tests/statistic/test_winsorizer.py` (TC-WZ-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Method, float, float -> None | `ValueError` | callers of the class | — |
| `compute` | Winsorise one column within each group. | pd.DataFrame, str, str -> pd.DataFrame | `KeyError` | as class | see class |

### `BaseChart` — `quant_cn.visualization.base_chart` (L7)
- **Purpose:** Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages); the base applies theme, size, hover and export.
- **Base:** ABC. **Depends on (injected):** ChartTheme, int, int.
- **Used by:** `visualization.PriceChart`, `visualization.FactorChart`.
- **Tests:** `tests/visualization/test_charts.py` (TC-BCA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, int, int -> None | `TypeError` | callers of the class | — |
| `build_figure` | Build the unthemed figure from the input frame. | pd.DataFrame -> go.Figure | `ValueError`, `SchemaError` | as class | see class |
| `render` | Build the figure and apply the theme: surfaces, ink, recessive grid, unified hover. | pd.DataFrame -> go.Figure | `ValueError`, `SchemaError` | as class | see class |
| `to_html` | The themed chart as an HTML fragment (plotly.js from its CDN). | pd.DataFrame -> str | `ValueError`, `SchemaError` | as class | see class |
| `write_html` | Save the themed chart as a standalone HTML page. | pd.DataFrame, Path -> Path | `ValueError`, `SchemaError`, `OSError` | as class | see class |

### `ChartTheme` — `quant_cn.visualization.chart_theme` (L7)
- **Purpose:** The colour and font tokens every chart reads, so charts are written against roles, never raw hex. Values follow the dataviz reference palette; `up`/`down` are its red and green slots (A-share convention: red up, green down), validated per mode; the light pair sits in the CVD 6-8 band, so up candles are hollow as the secondary encoding.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.BaseChart`, `visualization.PriceChart`, `visualization.FactorChart`.
- **Tests:** `tests/visualization/test_charts.py` (TC-CT-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `from_mode` | The theme for a display mode. | Mode -> ChartTheme | `ValueError` | as class | see class |

### `FactorChart` — `quant_cn.visualization.factor_chart` (L7)
- **Purpose:** The four views of a factor campaign (plan 04 phase 6), one single-series chart each so identity never rests on colour: "ic_series" (IC_SERIES) the rolling mean IC of one factor and horizon with a band of +/- 1.96 sd / sqrt(window / h), the effective number of non-overlapping observations; "icir" (IC_TEST) full-window ICIR per factor at one horizon with its bootstrap CI; "quantiles" (QUANTILE_RETURNS) mean forward return per quantile of one factor and horizon, long-short mean in the title; "horizon" (IC_TEST) full-window mean IC of one factor by horizon with its CI, peak horizon and half-life in the title (D-095).
- **Base:** BaseChart. **Depends on (injected):** ChartTheme, Kind, str | None, int, int, DateCodec | None, int, int.
- **Used by:** `research_space/notebooks/20260930_factor_campaign_01.ipynb`, `plan 06 ReportBuilder`.
- **Tests:** `tests/visualization/test_factor_chart.py` (TC-FC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, Kind, str \| None, int, int, DateCodec \| None, int, int -> None | `ValueError` | callers of the class | — |
| `build_figure` | The figure for `kind`. | pd.DataFrame -> go.Figure | `SchemaError`, `ValueError` | as class | see class |
| `_build_ic_series` (private) | internal helper over 20 lines | pd.DataFrame -> go.Figure | — | internal | — |
| `_build_horizon` (private) | internal helper over 20 lines | pd.DataFrame -> go.Figure | — | internal | — |

### `PriceChart` — `quant_cn.visualization.price_chart` (L7)
- **Purpose:** Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one ticker. Two stacked panels with their own y-axes (never a dual axis); x is a category axis of trading days so non-trading days leave no gaps. Up candles hollow, down candles filled.
- **Base:** BaseChart. **Depends on (injected):** ChartTheme, str, DateCodec, bool, int, int.
- **Used by:** `research_space/main.ipynb`.
- **Tests:** `tests/visualization/test_charts.py` (TC-PC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, str, DateCodec, bool, int, int -> None | — | callers of the class | — |
| `build_figure` | Candles and volume for `ts_code`. | pd.DataFrame -> go.Figure | `SchemaError`, `ValueError` | as class | see class |

### `DocumentRule` — `quant_cn.core.document_source` (L1)
- **Purpose:** One title rule: a title matching `include` and not `exclude` (regular expressions) is a document of `doc_type`.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.DocumentSource`, `data_loading.DocumentClassifier`.
- **Tests:** `tests/core/test_document_source.py` (TC-DSR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DocumentSource` — `quant_cn.core.document_source` (L1)
- **Purpose:** One document source of config/documents.yaml: the curated metadata dataset listing the documents, its key columns, the PDF URL and file-name templates (`{column}` placeholders), the folder under `documents/`, and how a row gets its doc type (a fixed `doc_type` or title `rules`, first match wins).
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `data_loading.DocumentClassifier`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/core/test_document_source.py` (TC-DSR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DocumentViews` — `quant_cn.lake.document_views` (L2)
- **Purpose:** Expose the document manifest in the catalog. `meta.document_attempts` holds every manifest row (one per download attempt). `meta.documents` holds the latest attempt per doc_id, so `WHERE status = 'ok'` lists the PDFs present under `documents/`.
- **Base:** none. **Depends on (injected):** Path, duckdb.DuckDBPyConnection.
- **Used by:** `lake.LakeCatalog.refresh_views`, `cli.DocumentCommands`.
- **Tests:** `tests/lake/test_document_views.py` (TC-DOV-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, duckdb.DuckDBPyConnection -> None | — | callers of the class | — |
| `refresh` | (Re)create both views, or drop them when no manifest file exists. | — -> None | `LakeError` | as class | see class |

### `RequestPacer` — `quant_cn.data_loading.request_pacer` (L3)
- **Purpose:** Run one request callable at a time-spaced rate with retries: request starts are at least `min_interval_s` apart across all threads sharing the pacer, and a call raising OSError, ValueError or KeyError is retried after `retry_sleep_s` up to `retries` times.
- **Base:** none. **Depends on (injected):** Clock, str, float, int, float.
- **Used by:** `data_loading.BaseWebClient`, `data_loading.DocumentDownloader`.
- **Tests:** `tests/data_loading/test_document_downloader.py` (TC-RP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, str, float, int, float -> None | — | callers of the class | — |
| `run` | Wait for this request's turn, run `call`, retry on transport errors. | str, Callable[[], T] -> T | `DataSourceError` | as class | see class |
| `record_throttle` | Record that the site throttled us: no request (from any thread) starts for `cooldown_s` seconds from now. | float -> None | — | as class | TC-RP-003 |

### `BaseWebClient` — `quant_cn.data_loading.base_web_client` (L3)
- **Purpose:** Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). It holds the transport, the timeout and a RequestPacer. Every request is spaced by `min_interval_s` and transport failures are retried after `retry_sleep_s`, so a long sweep survives short outages without hammering the site.
- **Base:** BaseApiClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float, float.
- **Used by:** `data_loading.CninfoClient`, `data_loading.EastmoneyReportClient`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-BWC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float, float -> None | — | callers of the class | — |
| `get_vendor_name` | Short vendor name used in error messages. | — -> str | — | as class | see class |

### `CninfoClient` — `quant_cn.data_loading.cninfo_client` (L3)
- **Purpose:** List CNINFO announcements for the whole A-share market (`column=szse` covers SZ, SH and BJ) over a date range, optionally one category (e.g. "category_ndbg_szsh" annual reports), following `pageNum` until `totalpages`. Rows are de-duplicated on (ann_id, sec_code) because the list can shift while a busy day is paged; `<em>` highlight tags are removed from titles; `announcementTime` (epoch ms) becomes `ann_time` "YYYYMMDD HH:MM:SS" and `ann_date` YYYYMMDD in Beijing time.
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-CNC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `get_vendor_name` | Vendor name for messages. | — -> str | — | as class | see class |
| `query` | Every announcement in the date range (and category), all pages. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `EastmoneyReportClient` — `quant_cn.data_loading.eastmoney_report_client` (L3)
- **Purpose:** List Eastmoney (东方财富) broker research reports published in a date range for one report kind (`q_type` "0" stock, "1" industry, "2" strategy), following `pageNo` until `TotalPage`. The PDF of a row is https://pdf.dfcfw.com/pdf/H3_<info_code>_1.pdf. `publishDate` carries no time of day, so `publish_date` is YYYYMMDD and the lake rule makes it usable from the next session.
- **Base:** BaseWebClient. **Depends on (injected):** Clock, HttpTransport | None, float, int, float.
- **Used by:** `cli.ServiceBuilder`.
- **Tests:** `tests/data_loading/test_web_clients.py` (TC-EMR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Clock, HttpTransport \| None, float, int, float -> None | — | callers of the class | — |
| `get_vendor_name` | Vendor name for messages. | — -> str | — | as class | see class |
| `query` | Every report of one kind published in [start_date, end_date]. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError` | as class | see class |

### `DocumentClassifier` — `quant_cn.data_loading.document_classifier` (L3)
- **Purpose:** Give each listed document its type: the source's fixed `doc_type`, or the first title rule whose `include` matches and whose `exclude` does not (e.g. "2025年年度报告" → annual; "2025年年度报告摘要" → none; "2025年半年度报告" → semiannual because that rule comes first).
- **Base:** none. **Depends on (injected):** DocumentSource.
- **Used by:** `data_loading.DocumentDownloader`.
- **Tests:** `tests/data_loading/test_document_downloader.py` (TC-DCL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DocumentSource -> None | — | callers of the class | — |
| `compute_doc_types` | Document type per title. | pd.Series -> pd.Series | — | as class | see class |

### `DocumentDownloader` — `quant_cn.data_loading.document_downloader` (L3)
- **Purpose:** Download the PDFs listed in a document source's curated metadata (config/documents.yaml) into `documents/<folder>/<doc_type>/<YYYY>/<MM>/<file>` (D-101). Rows are typed by DocumentClassifier, optionally limited to A-share codes (`curated.stock_basic.symbol`), de-duplicated on the document id, and skipped when the manifest already holds an `ok` attempt whose file exists. Each file is written atomically (tmp + rename) after its body is checked to start with %PDF-; one manifest row per attempt (sha256, bytes, status ok | not_pdf | failed) is appended to `meta/document_manifest/part-*.parquet` every `flush_every` documents, so an interrupted run resumes where it stopped.
- **Base:** none. **Depends on (injected):** Path, LakeQuery, Mapping[str, DocumentSource], Clock, HttpTransport | None, int, float, int, float, int.
- **Used by:** `cli.DocumentCommands`.
- **Tests:** `tests/data_loading/test_document_downloader.py` (TC-DD-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path, LakeQuery, Mapping[str, DocumentSource], Clock, HttpTransport \| None, int \| None, int, float, int -> None | — | callers of the class | — |
| `list_candidates` | Every wanted document of a source, typed and with its URL and target path. | str, Sequence[str] \| None, str \| None, str \| None -> pd.DataFrame | `ConfigError`, `LakeError` | as class | see class |
| `list_todo` | Candidates without an `ok` manifest attempt whose file exists: the work of `run`. | str, Sequence[str] \| None, str \| None, str \| None -> pd.DataFrame | `ConfigError`, `LakeError` | as class | see class |
| `run` | Download the documents of `todo` (from list_todo); no catalog access. | pd.DataFrame, int \| None, Progress \| None -> StepReport | `LakeError` | as class | see class |

### `DocumentCommands` — `quant_cn.cli` (L8)
- **Purpose:** The document-side CLI command `download-docs` (plan 12 phase 2, D-101): for each source, print candidate counts per doc type (`--dry-run`) or download the PDFs not yet in the manifest and print the outcome.
- **Base:** none. **Depends on (injected):** Console.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/test_cli.py` (TC-QCC-010..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Console -> None | — | callers of the class | — |
| `build_parser` | Add the `download-docs` subcommand and its options to the CLI parser. | argparse._SubParsersAction -> None | — | as class | see class |

### `ReportPages` — `quant_cn.quant_cn.industry_graph.pdf_text_extractor` (L4)
- **Purpose:** The text of one report PDF, page by page, plus its outline (bookmarks) when present.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.PdfTextExtractor`, `industry_graph.SectionDetector`, `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `n_chars` | Characters over all pages (for section-share statistics). | — -> int | — | as class | see class |

### `PdfTextExtractor` — `quant_cn.quant_cn.industry_graph.pdf_text_extractor` (L4)
- **Purpose:** Read the native text layer of a PDF page by page (no OCR; D-102) and remove the running header and footer: a line with at least four letters or CJK characters that, with digits ignored, appears on at least `header_share` of the pages (e.g. "牧原食品股份有限公司2025 年年度报告全文"), and bare page numbers ("31", "36 / 251"). Tables that cross a page break then read as one block, which the top-5 table parser needs (a header inside the table split rows in the hog-sector prototype).
- **Base:** none. **Depends on (injected):** float.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-PTE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | float -> None | — | callers of the class | — |
| `read_pages` | Text and outline of one PDF, headers and footers removed. | Path -> ReportPages | `DataSourceError` | as class | see class |
| `normalize_pages` | Remove running headers/footers and page-number lines from raw page texts. | list[str] -> list[str] | — | as class | see class |

### `Section` — `quant_cn.quant_cn.industry_graph.section_detector` (L4)
- **Purpose:** One located section: its key, the heading-matched start page and the page before the next section (or the chapter end), 1-based, inclusive.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.SectionDetector`, `industry_graph.ParsedReport`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-SD-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `SectionDetector` — `quant_cn.quant_cn.industry_graph.section_detector` (L4)
- **Purpose:** Locate the MD&A chapter (管理层讨论与分析, 第三节 in the 2021 standard; 第二节/第四节 in older or exchange-specific layouts) and the chain sections inside it by heading text, not by number, so SSE, SZSE and BSE layouts all work. A chapter heading must stand on its own line (body text often cites "第三节管理层讨论与分析"). A table-of-contents page (dot leaders, or three or more 第X节 headings) never counts as a chapter start. Only these pages go to later steps (D-102); in the prototype the chapter was 12-19% of a report's text.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-SD-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `find_chapter` | First and last page (1-based, inclusive) of the MD&A chapter. | ReportPages -> tuple[int, int] \| None | — | as class | see class |
| `list_sections` | The MD&A chapter and every chain section found in it. | ReportPages -> list[Section] | — | as class | see class |
| `find_heading_page` | First non-TOC page (1-based) anywhere in the report that carries a section's heading, for reports whose MD&A chapter is missing or named differently. | ReportPages, str -> int \| None | KeyError | `industry_graph.AnnualReportParser` | TC-SD-005 |

### `CounterpartyRow` — `quant_cn.quant_cn.industry_graph.counterparty_table_parser` (L4)
- **Purpose:** One ranked customer or supplier of a top-5 table.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.CounterpartyTable`, `industry_graph.CounterpartyTableParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_anonymous` | True when the report hides the name ("客户一", "供应商A", "第三名"). | — -> bool | — | as class | see class |

### `CounterpartyTable` — `quant_cn.quant_cn.industry_graph.counterparty_table_parser` (L4)
- **Purpose:** The top-5 customers or suppliers of one report: stated totals and the ranked rows (empty when only the totals sentence is disclosed, as on the SSE main board).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.CounterpartyTableParser`, `industry_graph.ParsedReport`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-CTP-004..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `is_consistent` | Rows complete and their shares add up to the stated total. | — -> bool | — | as class | see class |

### `CounterpartyTableParser` — `quant_cn.quant_cn.industry_graph.counterparty_table_parser` (L4)
- **Purpose:** Parse the "主要销售客户和主要供应商情况" block into a customer and a supplier CounterpartyTable. Three layouts are covered (prototype on 10 FY2025 reports): SZSE (totals as label + value, table in 元 or 千元 with % signs), STAR (totals sentence in 万元, table in 万元 without % and with a related-party column), SSE main board (totals sentence only, no table). Amounts are converted to CNY. Text is expected without running headers (PdfTextExtractor), so a table crossing a page break reads as one block.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-CTP-001..010).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `parse_tables` | Customer and supplier tables from the block text. | str -> tuple[CounterpartyTable, CounterpartyTable] | — | as class | see class |

### `ParsedReport` — `quant_cn.quant_cn.industry_graph.annual_report_parser` (L4)
- **Purpose:** What the rule-based pass extracts from one annual report.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.AnnualReportParser`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_section` | The section with this key, if located. | str -> Section \| None | — | as class | see class |

### `AnnualReportParser` — `quant_cn.quant_cn.industry_graph.annual_report_parser` (L4)
- **Purpose:** Run the rule-based pass of plan 12 phase 3 on one annual report: read the pages (PdfTextExtractor), locate the MD&A chapter and chain sections (SectionDetector), and parse the top-5 customer and supplier tables (CounterpartyTableParser). Nothing here calls an LLM; the located section pages are what phase 4 sends to DeepSeek.
- **Base:** none. **Depends on (injected):** PdfTextExtractor, SectionDetector, CounterpartyTableParser.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_report_parsing.py` (TC-ARP-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | PdfTextExtractor, SectionDetector, CounterpartyTableParser -> None | — | callers of the class | — |
| `parse_report` | Read and parse one PDF. | Path -> ParsedReport | `DataSourceError` | as class | see class |
| `parse_pages` | Parse already-read pages (lets callers reuse or synthesise ReportPages). | Path, ReportPages -> ParsedReport | — | as class | see class |

### `LlmReply` — `quant_cn.quant_cn.core.base_llm_client` (L1)
- **Purpose:** One LLM answer as parsed JSON, with the model and token usage, and whether it came from the response cache (a cached reply costs nothing and makes rebuilds deterministic).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.BaseLlmClient`, `data_loading.DeepSeekClient`.
- **Tests:** `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BaseLlmClient` — `quant_cn.quant_cn.core.base_llm_client` (L1)
- **Purpose:** Abstract chat-completion client that returns a JSON object: one system prompt, one user message, an optional model override. Vendors subclass it; extractors depend on this.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `data_loading.DeepSeekClient`, `industry_graph.ApplicationExtractor`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `fetch_json` | Ask the model and return its answer parsed as a JSON object. | str, str, str \| None, Sequence[str] -> LlmReply | `DataSourceError`, `ConfigError` | as class | see class |

### `LlmConfig` — `quant_cn.quant_cn.core.config` (L1)
- **Purpose:** The LLM endpoint used for extraction (D-098): OpenAI-compatible chat completions URL, default model, limits, and the API key, which comes from env DEEPSEEK_API_KEY only.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `core.Config`, `data_loading.DeepSeekClient`.
- **Tests:** `tests/core/test_config.py` (TC-C-014..014).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `DeepSeekClient` — `quant_cn.quant_cn.data_loading.deep_seek_client` (L3)
- **Purpose:** Call the DeepSeek (OpenAI-compatible) chat-completions endpoint with JSON output and temperature 0 and model reasoning off unless LlmConfig.thinking, paced and retried by RequestPacer. Every reply is cached on disk under `cache_dir/<hash[:2]>/<hash>.json`, keyed by model + system + user + stop, so a re-run costs nothing and gives the same graph (D-098). The key comes from LlmConfig (env only).
- **Base:** BaseLlmClient. **Depends on (injected):** LlmConfig, Clock, Path | None, HttpTransport | None.
- **Used by:** `research_space`.
- **Tests:** `tests/data_loading/test_deep_seek_client.py` (TC-DSC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LlmConfig, Clock, Path \| None, HttpTransport \| None -> None | — | callers of the class | — |
| `fetch_json` | One JSON answer, from the cache when the same request was made before. | str, str, str \| None, Sequence[str] -> LlmReply | `ConfigError`, `DataSourceError` | as class | see class |
| `get_usage` | Calls, local-cache hits, tokens and money spent since construction. | — -> dict[str, float] | — | as class | see class |
| `record_usage` | Append this client's usage so far as one JSON line to the cost ledger. | Path, str -> dict[str, Any] | `OSError` | as class | see class |
| `compute_cost` | CNY cost of one call at the configured peak prices, halved off-peak (Beijing time). | str, int, int, int -> float | — | as class | see class |

### `Evidence` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** A verbatim quote and the page it was found on (after the quote check).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationResult`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ApplicationResult` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** What the model found in one report, after validation: per revenue line the downstream applications (taxonomy node or proposed name, main/secondary, evidence) and customer types; named counterparties with role and evidence; and the items dropped because their quote was not in the text.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationExtractor`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ApplicationExtractor` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** Send the business / industry pages of one report, its revenue lines and the candidate downstream taxonomy nodes to the LLM, and keep only answers whose verbatim quote is found in the supplied pages (whitespace ignored). A quote found on another page than claimed is kept with the page corrected. Unknown node ids become proposals (node_id None). Roles outside ROLES (customer, supplier, partner, competitor, subsidiary, mention) are dropped; competitor mentions are peer evidence (D-102).
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_applications` | Ask the model about one report and validate the answer against the text. | str, Sequence[tuple[int, str]], Sequence[str], Sequence[tuple[str, str]] -> ApplicationResult | `DataSourceError` | as class | see class |

### `ApplicationItem` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** One downstream application of a revenue line as the LLM returned it.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.LineItem`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `LineItem` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** One revenue line with its applications and customer types as returned.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationReply`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `CounterpartyItem` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** One company named in the text, with its role, as returned.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationReply`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ApplicationReply` — `quant_cn.quant_cn.industry_graph.application_extractor` (L4)
- **Purpose:** The whole LLM reply of one report, validated before the quote check.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ApplicationExtractor`.
- **Tests:** `tests/industry_graph/test_application_extractor.py` (TC-AE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuoteChecker` — `quant_cn.quant_cn.industry_graph.quote_checker` (L4)
- **Purpose:** Hold the pages sent to an LLM and accept a returned quote only if it occurs verbatim (whitespace ignored) on one of them. The claimed page is preferred; a quote found on another sent page is kept with that page. Also assembles the page-tagged text ("[第N页]") sent to the model, truncated in page order to a character budget, so the checked pages are exactly the sent pages.
- **Base:** none. **Depends on (injected):** Sequence[tuple[int, str]].
- **Used by:** `industry_graph.ApplicationExtractor`, `industry_graph.ValuationExtractor`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-QC-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Sequence[tuple[int, str]] -> None | — | callers of the class | — |
| `build_prompt_text` | Page-tagged text for the prompt and the pages it contains. | Sequence[tuple[int, str]], int -> tuple[str, list[tuple[int, str]]] | — | as class | see class |
| `find_evidence` | Accept a quote if it occurs on a sent page. | str, int -> Evidence \| None | — | as class | see class |

### `ValuationItem` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** Base of the reply shapes: unknown keys ignored, so a richer reply still validates.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.ValuationReply`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ValuationReply` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** The LLM reply for one broker report, before the quote check: rating, target price, methods (multiple, implied or target, base year), forecasts, comparables, assumptions.
- **Base:** ValuationItem. **Depends on (injected):** —.
- **Used by:** `industry_graph.ValuationExtractor`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ValuationResult` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** One report's valuation after validation: only quote-checked target price, methods and assumptions; methods carry `multiple_kind` (D-109) and a base year; comparables carry a ts_code when it could be resolved.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ValuationExtractor`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ValuationExtractor` — `quant_cn.quant_cn.industry_graph.valuation_extractor` (L4)
- **Purpose:** Extract how a broker values a company (plan 13, D-105, D-109). Pages sent: the first LEAD_PAGES plus every page matching KEYWORDS, within a character budget. Kept: a target price and methods whose quotes are on a sent page; methods with a multiple must have a base year and a multiple_kind of "implied_at_price" or "target" (otherwise dropped); assumptions with a checked quote. Comparables are resolved to ts_codes through an injected name → code map when the report gives no code.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_valuation_extractor.py` (TC-VE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `list_pages` | The pages of a report worth sending, as (page number, text). | Sequence[str] -> list[tuple[int, str]] | — | as class | see class |
| `fetch_valuation` | Ask the model about one report and keep only what the text supports. | str, Sequence[tuple[int, str]], Mapping[str, str] \| None -> ValuationResult | `DataSourceError` | as class | see class |

### `QuarterlyNoteItem` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** One fact the LLM found in the notes, before the quote check.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.QuarterlyNoteReply`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuarterlyNoteReply` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** The LLM reply for one quarterly report.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.QuarterlyNoteExtractor`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuarterlyNoteResult` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** The quote-checked facts of one quarterly report.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.QuarterlyNoteExtractor`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `QuarterlyNoteExtractor` — `quant_cn.quant_cn.industry_graph.quarterly_note_extractor` (L4)
- **Purpose:** Q1 and Q3 reports carry no business chapter; their only narrative is the "主要会计数据、 财务指标发生变动的情况及原因" table and the "其他提醒事项" note. `list_note_pages` cuts those pages (from the first NOTE_START page up to the statements), `compute_note_chars` measures the text so the caller can skip near-empty notes, and `fetch_notes` asks the LLM for orders and contracts, customers won, capacity changes, profit drivers and new products, keeping only items whose verbatim quote is on a sent page and whose kind is in KINDS (plan 12 phase 4, user request 2026-11-07).
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_quarterly_note_extractor.py` (TC-QNE-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `list_note_pages` | The narrative pages (1-based) of a quarterly report. | Sequence[str] -> list[tuple[int, str]] | — | as class | see class |
| `compute_note_chars` | Characters of real note text: "□适用 √不适用" placeholders and whitespace removed. | Sequence[tuple[int, str]] -> int | — | as class | see class |
| `fetch_notes` | Ask the model about one report's notes and validate the answer against the text. | str, str, Sequence[tuple[int, str]] -> QuarterlyNoteResult | `DataSourceError` | as class | see class |

### `TaxonomyNode` — `quant_cn.quant_cn.industry_graph.product_taxonomy` (L4)
- **Purpose:** One node of the taxonomy as the matcher and views need it.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ProductTaxonomy`, `industry_graph.ProductMatcher`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PT-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `labels` | Name and aliases. | — -> tuple[str, ...] | — | as class | see class |

### `ProductTaxonomy` — `quant_cn.quant_cn.industry_graph.product_taxonomy` (L4)
- **Purpose:** Load config/industry_chain/*.yaml once: nodes (names and aliases always strings, even when YAML reads "1,4-丁二醇" style values as numbers), the merged-id map, and the Shenwan L3 → segment map (`sw_l3_map`). Answers which segments and products belong to a company's Shenwan codes, which is the context ProductMatcher uses.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `industry_graph.ProductMatcher`, `research_space`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PT-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `get_node` | The node for an id, after translating a merged id. | str -> TaxonomyNode \| None | — | as class | see class |
| `get_surviving_id` | Translate an id removed by the cross-sector merge to its surviving id. | str -> str | — | as class | see class |
| `list_nodes` | Nodes of the given types, in file order. | tuple[str, ...] -> list[TaxonomyNode] | — | as class | see class |
| `list_context_ids` | Segments mapped to the company's Shenwan codes (with their child segments) and the products in those segments. | list[str] -> set[str] | — | as class | see class |

### `ProductMatch` — `quant_cn.quant_cn.industry_graph.product_matcher` (L4)
- **Purpose:** One taxonomy node a revenue line maps to, with how it was found.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.ProductMatcher`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PM-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `ProductMatcher` — `quant_cn.quant_cn.industry_graph.product_matcher` (L4)
- **Purpose:** Map a company's revenue line to taxonomy nodes without the LLM. Order: generic lines (其他, 投资收益, 抵销, ...) map to nothing and `is_generic` says so, so callers can drop them from the denominator; the name is normalized (parentheses and suffixes such as 收入/业务/产品 removed; for "A:B:C" the leaf is tried first, then the top level); each product, segment or material label scores exact 1.0, contains 0.6-0.9 by length share, character-bigram overlap up to 0.6; labels inside the company's Shenwan context (ProductTaxonomy.list_context_ids) get CONTEXT_BONUS; the best label at or above MIN_SCORE wins (products before segments on ties). A compound line ("A、B及C") is split first; when two or more parts match, each part is a match, otherwise the whole line (or its one matching part) is matched. Last resort: a company whose Shenwan codes map to exactly one segment gets that segment with how="sector".
- **Base:** none. **Depends on (injected):** ProductTaxonomy.
- **Used by:** `research_space`.
- **Tests:** `tests/industry_graph/test_product_matcher.py` (TC-PM-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ProductTaxonomy -> None | — | callers of the class | — |
| `is_generic` | True for lines that name no product (residuals, accounting items, eliminations). | str -> bool | — | as class | see class |
| `find_matches` | Taxonomy nodes for one revenue line. | str, list[str] -> list[ProductMatch] | — | as class | see class |

### `ReportDigest` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** One broker report reduced to what the synthesis needs: the quote-checked fields of a ValuationExtractor result (plan 13), tagged with a short id the model must cite.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewSynthesizer`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `format_text` | The digest as one prompt block. | — -> str | — | as class | see class |

### `ViewPoint` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** One synthesized point with the report refs it rests on.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewReply`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BrokerViewReply` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** The LLM reply before the citation check.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewSynthesizer`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BrokerView` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** The synthesized view after the citation check.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BrokerViewSynthesizer`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BrokerViewSynthesizer` — `quant_cn.quant_cn.industry_graph.broker_view_synthesizer` (L4)
- **Purpose:** Synthesize the broker view of one product, Shenwan L3 industry or company from many report digests (user, 2026-11-08: the broker part must be the pattern across reports, not a list). The model may use only the digests; every point must cite digest refs, and refs not among the digests are removed; a point left without a valid ref is dropped (the citation check plays the role QuoteChecker plays for single documents). Digests are sent newest first within a character budget.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_broker_view_synthesizer.py` (TC-BVS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_view` | Ask the model for the synthesized view and check its citations. | str, str, Sequence[ReportDigest] -> BrokerView | `DataSourceError` | as class | see class |

### `ModeClaim` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** One quoted answer: a value (variant id, pricing mode, pass-through) with its evidence.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeReply`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PriceAction` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** A stated price move: direction, what, magnitude, evidence.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeReply`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BusinessModeReply` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** The LLM reply for one report before validation.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeExtractor`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BusinessModeResult` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** The quote-checked reading: each claim is a dict {value, reason, evidence} or None.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.BusinessModeExtractor`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `BusinessModeExtractor` — `quant_cn.quant_cn.industry_graph.business_mode_extractor` (L4)
- **Purpose:** Read the business-section pages of one annual report for the business-model fields that only the text can give (BUSINESS_MODEL_DESIGN §4.5 T1, §4b.7): which candidate variant of the company's archetype fits (or a proposed new one), the pricing mode, the cost pass-through and the stated price actions. Kept: claims whose verbatim quote is on a sent page and whose value is allowed (variant among the candidates, pricing in PRICING, pass-through in PASS_THROUGH, direction in DIRECTIONS); the rest is dropped and counted.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_business_mode_extractor.py` (TC-BME-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_mode` | Ask the model about one report and validate the answer against the text. | str, str, Sequence[tuple[str, str, str]], Sequence[tuple[int, str]] -> BusinessModeResult | `DataSourceError` | as class | see class |

### `Reason` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** One reason for the verdict with the evidence keys it rests on.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.AdjudicationReply`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `AdjudicationReply` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** The LLM reply before validation.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.PricingAdjudicator`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `Adjudication` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** The validated verdict.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.PricingAdjudicator`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `PricingAdjudicator` — `quant_cn.quant_cn.industry_graph.pricing_adjudicator` (L4)
- **Purpose:** For a company whose rule-based pricing-power label is insufficient or whose archetype check is inconsistent (BUSINESS_MODEL_DESIGN §4.5, §4b.7), give the model every measured signal, the annual-report claims and the broker-view summary, each under a key, and ask for one label, a confidence, whether the default archetype holds (or which allowed archetype fits) and the reasons. The citation check: reasons must cite supplied keys (unknown keys removed; a reason left with none is dropped); a label, confidence or archetype outside the allowed values raises (label) or is cleared (archetype) so nothing unverifiable is stored.
- **Base:** none. **Depends on (injected):** BaseLlmClient, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_pricing_adjudicator.py` (TC-PAD-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, str \| None -> None | — | callers of the class | — |
| `fetch_verdict` | Ask for the verdict and validate it. | str, str, Mapping[str, str], Mapping[str, str] -> Adjudication | `DataSourceError` | as class | see class |

### `MoatClaim` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** One claimed advantage: its moat type, a short statement, the figure the company gives (if any) and the evidence.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.MoatReply`, `industry_graph.MoatExtractor`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `MoatReply` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** The LLM reply before validation.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `industry_graph.MoatExtractor`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-003..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `MoatResult` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** The quote-checked claims of one report.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `industry_graph.MoatExtractor`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `MoatExtractor` — `quant_cn.quant_cn.industry_graph.moat_extractor` (L4)
- **Purpose:** Read the 核心竞争力分析 pages of one annual report and list the advantages the company claims, each classified as one of MOAT_TYPES (cost, switching costs, intangibles, network effects, efficient scale) with the figure it cites. These are claims, not proof: the rule layer tests them against ROIC, margins and share (§4.4). Kept: claims with an allowed type and a verbatim quote on a sent page.
- **Base:** none. **Depends on (injected):** BaseLlmClient, int, str | None.
- **Used by:** `lake`.
- **Tests:** `tests/industry_graph/test_moat_extractor.py` (TC-ME-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseLlmClient, int, str \| None -> None | — | callers of the class | — |
| `fetch_claims` | Ask the model about one report and validate the answer against the text. | str, Sequence[tuple[int, str]] -> MoatResult | `DataSourceError` | as class | see class |

### `CurveSummary` — `quant_cn.quant_cn.calculation.futures_curve` (L4)
- **Purpose:** The shape of one contract family's curve on one date: front, most-held, 6- and 12-month and last prices, and the slope from the most-held month to 12 months after it (or to the last later month when the curve is shorter).
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `calculation.FuturesCurve`.
- **Tests:** `tests/calculation/test_futures_curve.py` (TC-FCV-002..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|

### `FuturesCurve` — `quant_cn.quant_cn.calculation.futures_curve` (L4)
- **Purpose:** Back-month futures curve per contract family (e.g. "AL.SHF") and per material node (config/material_prices.yaml maps MAT_* ids to families), for the commodity price the market implies against the curve (plan 16 phase 2). A curve on a date is every listed month of the family that has a quote that day and has not expired (delivery month >= the trade month), priced at settle (close when settle is missing), with months ahead counted from the trade month. PIT: only quotes of that trade date are used.
- **Base:** none. **Depends on (injected):** pd.DataFrame, Mapping[str, Sequence[str]].
- **Used by:** `plan`.
- **Tests:** `tests/calculation/test_futures_curve.py` (TC-FCV-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | pd.DataFrame, Mapping[str, Sequence[str]] -> None | — | callers of the class | — |
| `list_families` | Contract families mapped to a material node. | str -> list[str] | — | as class | see class |
| `build_curve` | The family's curve on one date. | pd.DataFrame, str, str -> pd.DataFrame | `ValueError` | as class | see class |
| `compute_summary` | Front, dominant, 6m, 12m and last prices and the curve shape. | pd.DataFrame, str, str -> CurveSummary | — | as class | see class |
| `list_material_summaries` | One summary per family of a material. | pd.DataFrame, str, str -> list[CurveSummary] | `ValueError` | as class | see class |
| `build_dominant_series` | Daily price of the most-held unexpired month (regressor for profit sensitivity). | pd.DataFrame, str -> pd.DataFrame | `ValueError` | research checks; `ImpliedExpectations.compute_sensitivity` input | TC-FCV-006 |

### `ImpliedExpectations` — `quant_cn.quant_cn.calculation.implied_expectations` (L4)
- **Purpose:** Turn a market cap into what it already pays for (D-121: "priced in", not "cheap"). Years priced: the market cap above a normal value V0 is read as an annuity of excess profit E = TTM profit - 10-year median profit, discounted at `discount_rate`; n = -ln(1 - r*(MC - V0)/E) / ln(1 + r), 0 when MC ≤ V0, `max_years` when the market pays more than a perpetuity of E, NaN when E ≤ 0. Three bases, always shown side by side: V0 = median profit x `normal_pe` (primary), x the stock's own median PE, and the pre-cycle market cap. Each on net profit and on deducted net profit. Reverse DCF: the constant growth g of TTM profit over `dcf_years`, exiting at `normal_pe` x final profit, that makes the discounted value equal the market cap (bisection in GROWTH_BOUNDS, clamped). Pure: the caller loads market caps and PEs.
- **Base:** none. **Depends on (injected):** DiscoverySettings.
- **Used by:** `plan`.
- **Tests:** `tests/calculation/test_implied_expectations.py` (TC-IE-001..007). Inputs from `calculation.CompanyCyclePanel.list_quarters` and `calculation.FuturesCurve.build_dominant_series` (passed in by the caller).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DiscoverySettings -> None | — | callers of the class | — |
| `compute_years` | Years of excess profit the market cap pays for above a base value. | float, float, float -> float | — | as class | see class |
| `compute_implied_growth` | Annual profit growth over dcf_years that justifies the market cap (reverse DCF). | float, float -> float | — | as class | see class |
| `compute_sensitivity` | Annual profit change per unit commodity price (OLS of quarterly profit on quarterly mean futures price, x4; NaN below 8 quarters or R² 0.3). | pd.DataFrame, pd.DataFrame -> dict[str, float] | — | as class | TC-IE-006 |
| `compute_implied_price` | Commodity price at which normal_pe x profit(p) equals the market cap. | float, float, float, float -> float | — | as class | TC-IE-007 |
| `build` | Years priced on three bases and implied growth for every company with a market cap. | pd.DataFrame, pd.DataFrame -> pd.DataFrame | `ValueError` | as class | see class |

## C. Abstract base classes / extension points

| Class | Module | Layer | Purpose | Abstract methods (purpose each) | Known subclasses | Added |
|---|---|---|---|---|---|---|
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | Abstract vendor client: one logical query returns all pages as one DataFrame. | `query`: Run one query and return every row across pages. | `AkshareClient`, `BaostockClient`, `TushareClient`, `BaseWebClient` | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | Abstract record of which (dataset, key) pairs are fully downloaded. | `read_done_keys`: All keys recorded as done for a dataset.; `mark_done`: Record a finished key, replacing any earlier record for it.; `save`: Make recorded keys durable (e.g. write the parquet mirror). | `FetchLog` | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | Download one dataset as a sequence of keys | `list_keys`: All fetch keys for [start, end], ascending.; `build_params`: API parameters for one key. | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher`, `DateWindowFetcher` | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | Abstract append-only log of runs and per-key events | `open_run`: Open a run and return its id.; `record_event`: Append one event (fetched / skipped / empty / failed / blocked).; `close_run`: Close a run with its final status. | `RunLog` | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | Abstract unit of pipeline work: list its units, then run and report. | `name`: Step name shown in progress and reports.; `list_units`: Compute the work units (e.g. keys) just before running.; `run`: Do the work listed by `list_units`. | `CompactStep`, `DeriveStep`, `FetchStep`, `EvaluationStep`, `FeatureStep`, `UniverseStep` | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | Abstract sink for raw fetch results and curated partitions. | `write_raw`: Persist one fetch key's rows atomically.; `write_curated`: Replace one curated partition atomically after validating its schema. | `ParquetWriter` | 2026-09-27 |
| `BaseChecker` | `quant_cn.core.docs.base_checker` | 1 | Abstract repository check: inspect the tree, return findings (empty = pass). | `run`: Run the check over the repository. | `ContractChecker`, `IndexChecker`, `NameChecker`, `SizeChecker` | 2026-09-27 |
| `BaseFactor` | `quant_cn.factor.base_factor` | 5 | Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it needs and how many sessions of price history before the first output date | `compute_raw`: The raw factor value per stock and session. | `EarningsYieldFactor`, `MomentumFactor`, `ProfitGrowthFactor`, `ReversalFactor`, `RoeFactor`, `TurnoverFactor` | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 6 | Extension point for how steps are executed (local now, Prefect later, D-022) | `run`: Execute steps in order under one run id. | `PrefectRunner`, `LocalRunner` | 2026-09-27 |
| `BaseChart` | `quant_cn.visualization.base_chart` | 7 | Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages) | `build_figure`: Build the unthemed figure from the input frame. | `FactorChart`, `PriceChart` | 2026-09-27 |
| `BaseWebClient` | `quant_cn.data_loading.base_web_client` | 3 | Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). | `get_vendor_name`: Short vendor name used in error messages. | `CninfoClient`, `EastmoneyReportClient` | 2026-11-07 |
| `BaseLlmClient` | `quant_cn.quant_cn.core.base_llm_client` | 1 | Abstract chat-completion client that returns a JSON object: one system prompt, one user message, an optional model override. | `fetch_json`: Ask the model and return its answer parsed as a JSON object. |  | 2026-11-07 |

## D. Exceptions

| Class | Module | Parent | Purpose / raised when | Raised by | Added |
|---|---|---|---|---|---|
| `QuantCnError` | `quant_cn.core.exceptions` | `Exception` | Root of every exception the package raises, so callers catch project errors in one place. | `pipeline.LocalRunner.run`, `cli.QuantCnCli.run`, `core.ConfigError`, `core.DataSourceError`, `core.LakeError`, `core.SchemaError`, `pipeline.PrefectRunner` | 2026-09-27 |
| `ConfigError` | `quant_cn.core.exceptions` | `QuantCnError` | Configuration is missing, malformed or unsafe (e.g. lake root inside the repository). | `core.Config.load`, `core.Config.get_dataset`, `data_loading.TushareClient`, `data_loading.FetcherFactory.build`, `pipeline.DownloadPipeline.run`, `pipeline.CuratePipeline`, `factor.FactorFactory`, `data_loading.DocumentDownloader` | 2026-09-27 |
| `SchemaError` | `quant_cn.core.exceptions` | `QuantCnError` | A DataFrame does not satisfy its declared Schema (columns, dtypes, primary key). | `core.Schema.normalize`, `core.Schema.validate` | 2026-09-27 |
| `DataSourceError` | `quant_cn.core.exceptions` | `QuantCnError` | The external data source failed: API error code, retries exhausted, malformed response. | `data_loading.TushareClient.query`, `core.BaseFetcher.run`, `core.PermissionDeniedError`, `data_loading.AkshareClient`, `data_loading.BaostockClient`, `data_loading.DocumentDownloader`, `data_loading.RequestPacer` | 2026-09-27 |
| `PermissionDeniedError` | `quant_cn.core.exceptions` | `DataSourceError` | The account lacks permission (points) for an endpoint; the dataset is blocked, not broken. | `data_loading.TushareClient.query`, `pipeline.LocalRunner.run`, `pipeline.PrefectRunner` | 2026-09-27 |
| `LakeError` | `quant_cn.core.exceptions` | `QuantCnError` | The local lake cannot be read or written: missing dataset, failed atomic write, bad catalog. | `lake.ParquetWriter`, `lake.TradingCalendar`, `lake.LakeQuery.sql`, `cli.QuantCnCli`, `lake.Compactor`, `pipeline.DownloadPipeline`, `lake.FetchLog`, `lake.LakeCatalog`, `lake.RunLog`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`, `lake.QualityViews`, `lake.RebuildAudit`, `lake.LakeReader`, `lake.TickerAliasMap`, `data_loading.DocumentDownloader`, `lake.DocumentViews`, `cli.DocumentCommands` | 2026-09-27 |

## E. Schemas (DataFrame / typed records)

| Schema | Module | Purpose | Index | Columns (dtype) | Invariants | Produced by | Consumed by | Added |
|---|---|---|---|---|---|---|---|---|
| `PRICE_PANEL` | `quant_cn.core.frames` | daily bars with adjustment factor and adjusted close | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), open (float64), high (float64), low (float64), close (float64), pre_close (float64), vol (float64), amount (float64), adj_factor (float64), close_adj (float64) | key unique and non-null | `lake.LakeQuery.read_prices` | `visualization.PriceChart`, factors, engine | 2026-09-27 |
| `FUNDAMENTALS_PIT` | `quant_cn.core.frames` | point-in-time fundamentals, one value per field per trading day | long; key (trade_date, ts_code, field) | trade_date (string), ts_code (string), field (string), value (float64), end_date (string), ann_date (string) | key unique and non-null | `lake.PitAligner.read_aligned` | factors (plan 04) | 2026-09-27 |
| `VIX_PANEL` | `quant_cn.core.frames` | CBOE-method volatility index per day and option underlying, with per-term inputs | long; key (trade_date, underlying) | trade_date (string), underlying (string), clock (string), vix (float64), var_near (float64), var_next (float64), days_near (float64), days_next (float64), t_near (float64), t_next (float64), f_near (float64), f_next (float64), k0_near (float64), k0_next (float64), n_options_near (float64), n_options_next (float64), rate_near (float64), rate_next (float64), quality_flag (string) | key unique and non-null | `calculation.VixCalculator.compute` | VIX notebook; `pipeline.CalculationStep` (plan 03 ph4) | 2026-09-27 |
| `GEX_PANEL` | `quant_cn.core.frames` | dealer gamma exposure per option (sign assumption D-057) | long; key (trade_date, maturity_date, strike, call_put) | trade_date (string), maturity_date (string), days (float64), strike (float64), call_put (string), oi (float64), price (float64), forward (float64), rate (float64), t (float64), iv (float64), gamma (float64), sign (float64), multiplier (float64), gex (float64) | key unique and non-null | `calculation.GammaExposureCalculator.compute` | positioning notebook; plan 09 event study | 2026-09-27 |
| `FUTURES_POSITIONING` | `quant_cn.core.frames` | index-futures OI regime, top-20 net and basis per product and day | long; key (trade_date, product) | trade_date (string), product (string), main_contract (string), price (float64), price_change (float64), oi_total (float64), oi_change (float64), regime (string), top20_long (float64), top20_short (float64), top20_net (float64), spot (float64), basis_pct (float64), basis_annualised (float64) | key unique and non-null | `calculation.FuturesPositioning.compute` | positioning notebook; plan 09 event study | 2026-09-27 |
| `MARGIN_VINTAGES` | `quant_cn.core.frames` | FIFO margin-financing vintages with liquidation prices (D-058) | long; key (ts_code, entry_date, seeded) | ts_code (string), entry_date (string), entry_price (float64), debt (float64), liquidation_price (float64), price (float64), distance_pct (float64), seeded (float64) | key unique and non-null | `calculation.MarginLadderEstimator.compute_ladder` | `calculation.MarginLadderEstimator.compute_curve` | 2026-09-27 |
| `MARGIN_LADDER` | `quant_cn.core.frames` | financing debt reaching forced sale per market drawdown | long; key (drawdown_pct) | drawdown_pct (float64), debt_forced (float64), share_of_debt (float64) | key unique and non-null | `calculation.MarginLadderEstimator.compute_curve` | positioning notebook | 2026-09-27 |
| `UNIVERSE_PANEL` | `quant_cn.core.frames` | tradeable universe per session with exclusion reason | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), in_universe (float64), reason (string) | key unique and non-null | `pipeline.UniverseStep` (plan 04 ph3) | constructors, `factor.FactorEvaluator` | 2026-09-27 |
| `FACTOR_PANEL` | `quant_cn.core.frames` | factor value (processed and raw) per stock and session | long; key (trade_date, ts_code, factor) | trade_date (string), ts_code (string), factor (string), value (float64), value_raw (float64) | key unique and non-null | `factor.BaseFactor`, `factor.FactorPreprocessor` (plan 04 ph4-5) | `factor.FactorEvaluator`, constructors | 2026-09-27 |
| `IC_SERIES` | `quant_cn.core.frames` | information coefficient per date, factor and horizon with N | long; key (trade_date, factor, horizon) | trade_date (string), factor (string), horizon (float64), ic (float64), n (float64) | key unique and non-null | `statistic.ICCalculator` (plan 04 ph2) | `statistic.ICSignificance` | 2026-09-27 |
| `IC_TEST` | `quant_cn.core.frames` | significance results per factor, horizon, metric and window incl. adjusted p | long; key (factor, horizon, metric, window) | factor (string), horizon (float64), metric (string), value (float64), se (float64), t (float64), p (float64), ci_lo (float64), ci_hi (float64), window (string), p_adj_holm (float64), p_adj_bhy (float64), p_adj_romano_wolf (float64), hlz_pass (float64) | key unique and non-null | `statistic.ICSignificance`, `statistic.MultipleTestingAdjuster` (plan 04 ph2) | `factor.FactorEvaluator` reports | 2026-09-27 |
| `TRIAL_LOG` | `quant_cn.core.frames` | every factor/parameter variant evaluated in a campaign | long; key (campaign, trial_id) | campaign (string), trial_id (string), factor (string), params (string), horizon (float64), sr (float64), ic_mean (float64) | key unique and non-null | `statistic.TrialLog` (plan 04 ph2) | `statistic.MultipleTestingAdjuster`, DSR (plan 06) | 2026-09-27 |
| `FORWARD_RETURN` | `quant_cn.core.frames` | tradeable forward return per stock, session and horizon | long; key (trade_date, ts_code, horizon) | trade_date (string), ts_code (string), horizon (float64), fwd_return (float64) | key unique and non-null | `statistic.ICCalculator.build_forward_returns` | `statistic.ICCalculator`, `statistic.QuantileReturns` | 2026-09-27 |
| `QUANTILE_RETURNS` | `quant_cn.core.frames` | mean forward return per factor quantile and date (0 = long-short) | long; key (trade_date, factor, horizon, quantile) | trade_date (string), factor (string), horizon (float64), quantile (float64), ret (float64), n (float64) | key unique and non-null | `statistic.QuantileReturns.compute` | `factor.FactorEvaluator`, `FactorChart` | 2026-09-27 |
| `EXPOSURE_PANEL` | `quant_cn.core.frames` | industry (Shenwan L1 grouping) and log market cap per universe member and session | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), l1_code (string), industry_backfilled (float64), log_mcap (float64) | key unique and non-null | `lake.ExposureReader.read_exposures` | `factor.FactorPreprocessor` (neutralisation, D-093) | 2026-09-27 |

## F. Allowed standalone functions (`core/utils` only, with justification)

| Function | Module | Purpose | Input -> Output | Why not a class method | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | |
