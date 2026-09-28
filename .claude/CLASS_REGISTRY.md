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
| `QuantCnCli` | `quant_cn.cli` | 6 | none | `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup, project-catalog, query | 1 | `Makefile targets doctor, download, compact, lake-rebuild, lake-backup` | `tests/test_cli.py` (TC-QCC-001..004) | 2026-09-27 |
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | ABC | Abstract vendor client: one logical query returns all pages as one DataFrame. | 1 | `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | ABC | Abstract record of which (dataset, key) pairs are fully downloaded. | 5 | `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher` | `tests/lake/test_fetch_log.py` (TC-FL-001..003) | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | ABC | Download one dataset as a sequence of keys | 5 | `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep` | `tests/core/test_base_fetcher.py` (TC-BF-001..006) | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | ABC | Abstract append-only log of runs and per-key events | 3 | `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher` | `tests/lake/test_run_log.py` (TC-RL-001..001) | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | ABC | Abstract unit of pipeline work: list its units, then run and report. | 3 | `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `pipeline.DeriveStep` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | ABC | Abstract sink for raw fetch results and curated partitions. | 2 | `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher` | `tests/core/test_base_classes.py` (TC-BAC-001..001) | 2026-09-27 |
| `Clock` | `quant_cn.core.clock` | 1 | none | The single source of wall time, monotonic time and sleeping | 4 | `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.FetcherFactory`, `data_loading.PeriodSweepFetcher`, `lake.ProjectCatalog` | `tests/core/test_clock.py` (TC-CL-001..002) | 2026-09-27 |
| `LakeConfig` | `quant_cn.core.config` | 1 | BaseModel | Where the lake lives and whether it may sit inside the repository. | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-001..001) | 2026-09-27 |
| `TushareConfig` | `quant_cn.core.config` | 1 | BaseModel | Tushare endpoint, paging, retry and rate-limit settings | 0 | `core.Config`, `data_loading.TushareClient` | `tests/core/test_config.py` (TC-C-002..002) | 2026-09-27 |
| `DownloadConfig` | `quant_cn.core.config` | 1 | BaseModel | Which datasets to download, in what order, and from which start dates (D-015b). | 0 | `core.Config` | `tests/core/test_config.py` (TC-C-004..004) | 2026-09-27 |
| `Config` | `quant_cn.core.config` | 1 | BaseModel | The typed configuration injected everywhere: YAML defaults, machine overrides, environment. | 3 | `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline` | `tests/core/test_config.py` (TC-C-001..008) | 2026-09-27 |
| `SweepSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | How a dataset is swept so each call returns the whole market for one key. | 1 | `core.DatasetSpec` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `CuratedSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Where a dataset lands in `curated/` and which date column drives its yearly partition. | 0 | `core.DatasetSpec` | `tests/core/test_dataset_spec.py` (TC-DS-001..001) | 2026-09-27 |
| `DatasetSpec` | `quant_cn.core.dataset_spec` | 1 | BaseModel | Everything the lake and the fetchers need to know about one dataset, as data (D-012). | 2 | `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.CompactStep`, `lake.DerivedViews`, `lake.ProjectCatalog` | `tests/core/test_dataset_spec.py` (TC-DS-001..004) | 2026-09-27 |
| `DateCodec` | `quant_cn.core.date_codec` | 1 | none | Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps. | 5 | `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`, `data_loading.FetcherFactory`, `cli.QuantCnCli`, `lake.PitAligner`, `visualization.PriceChart` | `tests/core/test_date_codec.py` (TC-DC-001..005) | 2026-09-27 |
| `Finding` | `quant_cn.core.docs.base_checker` | 1 | none | One rule violation at a location, printable as `path:line [rule] message`. | 1 | `core.docs.BaseChecker.run`, `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter` | `tests/core/docs/test_base_checker.py` (TC-BCH-001..001) | 2026-09-27 |
| `BaseChecker` | `quant_cn.core.docs.base_checker` | 1 | ABC | Abstract repository check: inspect the tree, return findings (empty = pass). | 1 | `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter` | `tests/core/docs/test_base_checker.py` (TC-BCH-001..001) | 2026-09-27 |
| `MethodInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One function defined directly in a class body. | 2 | `core.docs.ClassInfo`, `core.docs.CodeScanner.read_module`, `core.docs.ModuleInfo` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..001) | 2026-09-27 |
| `ClassInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One top-level class: span, bases, docstring, methods and the names its body references. | 2 | `core.docs.ModuleInfo`, `core.docs.CodeScanner.read_module`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..002) | 2026-09-27 |
| `ModuleInfo` | `quant_cn.core.docs.code_scanner` | 1 | none | One scanned Python file. | 0 | `core.docs.CodeScanner.read_module`, `core.docs.ContractChecker`, `core.docs.NameChecker`, `core.docs.CodeUnit`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..001) | 2026-09-27 |
| `CodeScanner` | `quant_cn.core.docs.code_scanner` | 1 | none | Parse Python files with `ast` into ModuleInfo records (no import, no execution). | 1 | `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_code_scanner.py` (TC-CS-001..003) | 2026-09-27 |
| `CodeTableBuilder` | `quant_cn.core.docs.code_table_builder` | 1 | none | Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the code-side tables of the `project` schema, one DataFrame per table with fixed columns. | 1 | `lake.ProjectCatalog`, `cli.QuantCnCli` | `tests/core/docs/test_code_table_builder.py` (TC-CTB-001..002) | 2026-09-27 |
| `CodeUnit` | `quant_cn.core.docs.contract_checker` | 1 | none | A class with the module it lives in and its parsed contract. | 0 | `core.docs.ContractChecker` | `tests/core/docs/test_contract_checker.py` (TC-CC-001..001) | 2026-09-27 |
| `ContractChecker` | `quant_cn.core.docs.contract_checker` | 1 | BaseChecker | Check contracts across the tree: class docstrings carry all sections and public methods Purpose + Contract | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_contract_checker.py` (TC-CC-001..005) | 2026-09-27 |
| `ContractLinter` | `quant_cn.core.docs.contract_linter` | 1 | none | Build the four checkers (contracts, index, size, names) for one repository and run the selected groups, returning all findings sorted. | 1 | `scripts/lint_contracts.py`, `tests/test_contracts.py`, `lake.ProjectCatalog`, `cli.QuantCnCli` | `tests/test_contracts.py` (TC-CTL-001..002) | 2026-09-27 |
| `ConventionReader` | `quant_cn.core.docs.convention_reader` | 1 | none | Extract the allowed method-name verb prefixes from the naming convention's §2.1 table. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_convention_reader.py` (TC-CR-001..002) | 2026-09-27 |
| `DecisionRecord` | `quant_cn.core.docs.decisions_reader` | 1 | none | One decision: its log-table row joined with the Context and Decision bullets of its block. | 0 | `core.docs.DecisionsReader` | `tests/core/docs/test_decisions_reader.py` (TC-DR-001..001) | 2026-09-27 |
| `DecisionsReader` | `quant_cn.core.docs.decisions_reader` | 1 | none | Parse DECISIONS.md: the ID/Date/Title/Status/Where table plus `### D-NNN` detail blocks. | 1 | `core.docs.DocTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_decisions_reader.py` (TC-DR-001..002) | 2026-09-27 |
| `DocTableBuilder` | `quant_cn.core.docs.doc_table_builder` | 1 | none | Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into the document-side tables of the `project` schema. | 1 | `lake.ProjectCatalog`, `cli.QuantCnCli` | `tests/core/docs/test_doc_table_builder.py` (TC-DTB-001..002) | 2026-09-27 |
| `UsedByEntry` | `quant_cn.core.docs.docstring_parser` | 1 | none | One line of a `Used by:` section, split into the caller reference and its note. | 0 | `core.docs.DocContract`, `core.docs.DocstringParser.parse` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001) | 2026-09-27 |
| `DocContract` | `quant_cn.core.docs.docstring_parser` | 1 | none | The parsed contract of one class, method or module docstring. | 1 | `core.docs.DocstringParser.parse`, `core.docs.CodeUnit` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..001) | 2026-09-27 |
| `DocstringParser` | `quant_cn.core.docs.docstring_parser` | 1 | none | Split a contract docstring into its sections: Purpose, Contract (Input, Output, Raises), Used by, Test cases. | 1 | `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_docstring_parser.py` (TC-DSP-001..005) | 2026-09-27 |
| `IndexChecker` | `quant_cn.core.docs.index_checker` | 1 | BaseChecker | Every visible folder has an INDEX.md whose folder and file rows equal what is on disk, and whose Contains cell for a .py file lists exactly its top-level classes (fixtures for conftest.py | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_index_checker.py` (TC-IC-001..004) | 2026-09-27 |
| `IndexEntry` | `quant_cn.core.docs.index_reader` | 1 | none | One row of an INDEX.md table: a subfolder or a file with its purpose and named contents. | 0 | `core.docs.IndexInfo`, `core.docs.IndexReader.read` | `tests/core/docs/test_index_reader.py` (TC-IR-001..001) | 2026-09-27 |
| `IndexInfo` | `quant_cn.core.docs.index_reader` | 1 | none | Parsed INDEX.md: title line, subfolder entries, file entries. | 0 | `core.docs.IndexReader.read`, `core.docs.IndexChecker`, `core.docs.DocTableBuilder` | `tests/core/docs/test_index_reader.py` (TC-IR-001..001) | 2026-09-27 |
| `IndexReader` | `quant_cn.core.docs.index_reader` | 1 | none | Parse the fixed INDEX.md format: `## Folders` (Folder, Purpose) and `## Files` (File, Purpose, Contains) tables. | 1 | `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_index_reader.py` (TC-IR-001..002) | 2026-09-27 |
| `MarkdownTable` | `quant_cn.core.docs.markdown_table` | 1 | none | One pipe table with the heading it sits under. | 1 | `core.docs.MarkdownTableReader.read` | `tests/core/docs/test_markdown_table.py` (TC-MTR-001..001) | 2026-09-27 |
| `MarkdownTableReader` | `quant_cn.core.docs.markdown_table` | 1 | none | Extract every pipe table from markdown text, and backticked names from a cell. | 2 | `core.docs.IndexReader`, `core.docs.RegistryReader`, `core.docs.ConventionReader`, `core.docs.ContractLinter`, `core.docs.DecisionsReader`, `core.docs.PlanReader`, `cli.QuantCnCli` | `tests/core/docs/test_markdown_table.py` (TC-MTR-001..003) | 2026-09-27 |
| `NameChecker` | `quant_cn.core.docs.name_checker` | 1 | BaseChecker | Enforce names: lowercase paths (governance `UPPER_SNAKE.md` and tool files excepted), verb-first method and function names from the convention's verb table, no banned verbs, test functions named `test_tc_<id>_<desc>`, and module name matching its primary class. | 2 | `core.docs.ContractLinter` | `tests/core/docs/test_name_checker.py` (TC-NC-001..004) | 2026-09-27 |
| `PhaseRecord` | `quant_cn.core.docs.plan_reader` | 1 | none | One row of a plan's Phases table. | 0 | `core.docs.PlanRecord`, `core.docs.PlanReader.read` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..001) | 2026-09-27 |
| `PlanRecord` | `quant_cn.core.docs.plan_reader` | 1 | none | One execution plan: number, title, header fields and phases. | 0 | `core.docs.PlanReader.read` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..001) | 2026-09-27 |
| `PlanReader` | `quant_cn.core.docs.plan_reader` | 1 | none | Parse a plan file: `# NN — Title`, the two-column header table (Status, Decisions, Depends on plans) and the Phases table. | 1 | `core.docs.DocTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_plan_reader.py` (TC-PR-001..002) | 2026-09-27 |
| `RegistryInfo` | `quant_cn.core.docs.registry_reader` | 1 | none | The registry's content as sets and maps the linter can compare with code. | 0 | `core.docs.RegistryReader.read`, `core.docs.ContractChecker`, `core.docs.CodeTableBuilder` | `tests/core/docs/test_registry_reader.py` (TC-RR-001..001) | 2026-09-27 |
| `RegistryReader` | `quant_cn.core.docs.registry_reader` | 1 | none | Parse CLASS_REGISTRY.md: section A index, section B detail blocks and their method tables, and the class/schema names of sections C, D, E. | 1 | `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_registry_reader.py` (TC-RR-001..003) | 2026-09-27 |
| `RepoFiles` | `quant_cn.core.docs.repo_files` | 1 | none | The set of repository files a linter should see: `git ls-files --cached --others --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored. | 2 | `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.QuantCnCli` | `tests/core/docs/test_repo_files.py` (TC-RF-001..003) | 2026-09-27 |
| `SizeChecker` | `quant_cn.core.docs.size_checker` | 1 | BaseChecker | Fail any .py file over 600 lines, class over 300, function or method over 50 (physical lines, docstrings included), and INDEX.md / SKILL.md / execution plan over 300 lines. | 1 | `core.docs.ContractLinter` | `tests/core/docs/test_size_checker.py` (TC-SC-001..002) | 2026-09-27 |
| `Schema` | `quant_cn.core.schema` | 1 | none | Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared columns are `float64`, and the primary key is unique and non-null. | 4 | `core.DatasetSpec.build_schema` | `tests/core/test_schema.py` (TC-S-001..006) | 2026-09-27 |
| `StepReport` | `quant_cn.core.step_report` | 1 | none | Counts and status of one step (usually one dataset's fetch) so runs can be summarised. | 0 | `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `pipeline.FetchStep`, `pipeline.PipelineReport`, `pipeline.CompactStep`, `pipeline.DeriveStep` | `tests/core/test_base_fetcher.py` (TC-BF-001..001) | 2026-09-27 |
| `TickerNormalizer` | `quant_cn.core.ticker_normalizer` | 1 | none | Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity. | 2 | (none yet) | `tests/core/test_ticker_normalizer.py` (TC-TN-001..004) | 2026-09-27 |
| `FetcherFactory` | `quant_cn.data_loading.fetcher_factory` | 3 | none | Build the right fetcher for a DatasetSpec and inject the shared dependencies. | 1 | `pipeline.DownloadPipeline`, `cli.QuantCnCli` | `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..002) | 2026-09-27 |
| `SingleCallFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets fetched in one (paged) call, key "all": trade_cal, namechange. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-SCF-001..001) | 2026-09-27 |
| `EnumFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Datasets swept over an enumerated list: stock_basic by list_status (L, D, P), index_daily / fund_daily by ts_code, opt_basic by exchange. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-EF-001..001) | 2026-09-27 |
| `DateSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market daily sweeps: trade_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit) | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-DSF-001..002) | 2026-09-27 |
| `PeriodSweepFetcher` | `quant_cn.data_loading.fetchers` | 3 | BaseFetcher | Whole-market report-period sweeps (the *_vip fundamentals): one key per quarter end. | 2 | `data_loading.FetcherFactory.build` | `tests/data_loading/test_fetchers.py` (TC-PSF-001..001) | 2026-09-27 |
| `HttpTransport` | `quant_cn.data_loading.http_transport` | 3 | none | Send one JSON POST and return the decoded JSON object. | 1 | `data_loading.TushareClient` | `tests/data_loading/test_tushare_client.py` (TC-TC-001..001) | 2026-09-27 |
| `TushareClient` | `quant_cn.data_loading.tushare_client` | 3 | BaseApiClient | Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows | 1 | `cli.QuantCnCli` | `tests/data_loading/test_tushare_client.py` (TC-TC-001..007) | 2026-09-27 |
| `Compactor` | `quant_cn.lake.compactor` | 2 | none | Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`. | 1 | `cli.QuantCnCli`, `pipeline.CompactStep`, `pipeline.CuratePipeline` | `tests/lake/test_compactor.py` (TC-CO-001..005) | 2026-09-27 |
| `DerivedViews` | `quant_cn.lake.derived_views` | 2 | none | Create the `derived` schema views built only from curated/: `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor | 1 | `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `cli.QuantCnCli`, `cli.QuantCnCli` | `tests/lake/test_derived_views.py` (TC-DV-001..003) | 2026-09-27 |
| `FetchLog` | `quant_cn.lake.fetch_log` | 2 | BaseFetchLog | Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost. | 5 | `cli.QuantCnCli` | `tests/lake/test_fetch_log.py` (TC-FL-001..005) | 2026-09-27 |
| `LakeCatalog` | `quant_cn.lake.lake_catalog` | 2 | none | Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta` | 8 | `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog` | `tests/lake/test_lake_catalog.py` (TC-LC-001..005) | 2026-09-27 |
| `LakeQuery` | `quant_cn.lake.lake_query` | 2 | none | Run read queries against the catalog views | 3 | `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner` | `tests/lake/test_lake_query.py` (TC-LQ-001..004) | 2026-09-27 |
| `ParquetWriter` | `quant_cn.lake.parquet_writer` | 2 | BaseStore | Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file. | 4 | `cli.QuantCnCli` | `tests/lake/test_parquet_writer.py` (TC-PW-001..005) | 2026-09-27 |
| `PitAligner` | `quant_cn.lake.pit_aligner` | 2 | none | Align fundamentals to trading days without look-ahead | 2 | `pipeline.CuratePipeline`, `research_space/main.ipynb`, `pipeline.DeriveStep`, `cli.QuantCnCli`, `cli.QuantCnCli` | `tests/lake/test_pit_aligner.py` (TC-PA-001..005) | 2026-09-27 |
| `ProjectCatalog` | `quant_cn.lake.project_catalog` | 2 | none | Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings, plus views tree, class_graph, stale and todo | 1 | `cli.QuantCnCli` | `tests/lake/test_project_catalog.py` (TC-PJC-001..004) | 2026-09-27 |
| `RunLog` | `quant_cn.lake.run_log` | 2 | BaseRunLog | Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging. | 3 | `cli.QuantCnCli` | `tests/lake/test_run_log.py` (TC-RL-001..002) | 2026-09-27 |
| `TradingCalendar` | `quant_cn.lake.trading_calendar` | 2 | none | Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake | 5 | `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.QuantCnCli` | `tests/lake/test_trading_calendar.py` (TC-TCA-001..004) | 2026-09-27 |
| `CompactStep` | `quant_cn.pipeline.curate_pipeline` | 4 | BaseStep | Adapt Compactor to a pipeline step: one unit per dataset. | 3 | `pipeline.CuratePipeline` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..001) | 2026-09-27 |
| `DeriveStep` | `quant_cn.pipeline.curate_pipeline` | 4 | BaseStep | Build the derived views and the PIT states view, then record a digest per derived view. | 4 | `pipeline.CuratePipeline` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..002) | 2026-09-27 |
| `CuratePipeline` | `quant_cn.pipeline.curate_pipeline` | 4 | none | Rebuild everything below raw/: compact every dataset, create derived views and PIT states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json. | 1 | `cli.QuantCnCli` | `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..003) | 2026-09-27 |
| `FetchStep` | `quant_cn.pipeline.download_pipeline` | 4 | BaseStep | Adapt one dataset's fetcher to a pipeline step: keys computed in list_units (so the calendar fetched earlier in the run is visible), catalog view refreshed after the run. | 3 | `pipeline.DownloadPipeline.run` | `tests/pipeline/test_download_pipeline.py` (TC-DP-002..002) | 2026-09-27 |
| `DownloadPipeline` | `quant_cn.pipeline.download_pipeline` | 4 | none | Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes | 1 | `cli.QuantCnCli` | `tests/pipeline/test_download_pipeline.py` (TC-DP-001..005) | 2026-09-27 |
| `PipelineReport` | `quant_cn.pipeline.runner` | 4 | none | Result of one pipeline run: its id, overall status and one StepReport per step. | 2 | `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.BaseRunner`, `pipeline.CuratePipeline` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 4 | ABC | Extension point for how steps are executed (local now, Prefect later, D-022) | 1 | `pipeline.LocalRunner`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline` | `tests/pipeline/test_runner.py` (TC-LR-001..001) | 2026-09-27 |
| `LocalRunner` | `quant_cn.pipeline.runner` | 4 | BaseRunner | Run steps serially in this process with a rich progress bar per step | 1 | `cli.QuantCnCli` | `tests/pipeline/test_runner.py` (TC-LR-001..003) | 2026-09-27 |
| `BaseChart` | `quant_cn.visualization.base_chart` | 5 | ABC | Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages) | 4 | `visualization.PriceChart` | `tests/visualization/test_charts.py` (TC-BCA-001..002) | 2026-09-27 |
| `ChartTheme` | `quant_cn.visualization.chart_theme` | 5 | none | The colour and font tokens every chart reads, so charts are written against roles, never raw hex | 1 | `visualization.BaseChart`, `visualization.PriceChart` | `tests/visualization/test_charts.py` (TC-CT-001..001) | 2026-09-27 |
| `PriceChart` | `quant_cn.visualization.price_chart` | 5 | BaseChart | Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one ticker | 1 | `research_space/main.ipynb` | `tests/visualization/test_charts.py` (TC-PC-001..003) | 2026-09-27 |

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

### `QuantCnCli` — `quant_cn.cli` (L6)
- **Purpose:** `python -m quant_cn.cli <command>`: doctor, download, compact, curate, rebuild, backup, project-catalog, query. Builds every service from Config (the only place objects are wired) and prints summaries.
- **Base:** none. **Depends on (injected):** Config | None, Console | None.
- **Used by:** `Makefile targets doctor, download, compact, lake-rebuild, lake-backup`.
- **Tests:** `tests/test_cli.py` (TC-QCC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config \| None, Console \| None -> None | — | callers of the class | — |
| `run` | Parse arguments and dispatch to a command. | Sequence[str] \| None -> int | `SystemExit` | as class | see class |
| `_build_parser` (private) | internal helper over 20 lines | — -> argparse.ArgumentParser | — | internal | — |

### `BaseApiClient` — `quant_cn.core.base_api_client` (L1)
- **Purpose:** Abstract vendor client: one logical query returns all pages as one DataFrame.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `query` | Run one query and return every row across pages. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |

### `BaseFetchLog` — `quant_cn.core.base_fetch_log` (L1)
- **Purpose:** Abstract record of which (dataset, key) pairs are fully downloaded.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.FetchLog`, `core.BaseFetcher`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`.
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
- **Used by:** `data_loading.SingleCallFetcher`, `data_loading.EnumFetcher`, `data_loading.DateSweepFetcher`, `data_loading.PeriodSweepFetcher`, `data_loading.FetcherFactory.build`, `pipeline.FetchStep`.
- **Tests:** `tests/core/test_base_fetcher.py` (TC-BF-001..006).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock -> None | `TypeError` | callers of the class | — |
| `list_keys` | All fetch keys for [start, end], ascending. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
| `build_params` | API parameters for one key. | str, str, str -> dict[str, str] | — | as class | see class |
| `list_due_keys` | Keys that must be fetched: all if forced or overwrite, else pending plus the newest `refetch_recent` keys. | Sequence[str], bool -> list[str] | `LakeError` | as class | see class |
| `fetch_one` | Query the endpoint for one key. | str, str, str -> pd.DataFrame | `DataSourceError`, `PermissionDeniedError` | as class | see class |
| `run` | Fetch every key that needs fetching, writing and logging each before the next. | str, str, str, Sequence[str] \| None, bool, ProgressHook \| None -> StepReport | `DataSourceError`, `PermissionDeniedError`, `SchemaError`, `LakeError` | as class | see class |

### `BaseRunLog` — `quant_cn.core.base_run_log` (L1)
- **Purpose:** Abstract append-only log of runs and per-key events; the source of truth for "what happened".
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.RunLog`, `core.BaseFetcher.run`, `pipeline.LocalRunner`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `open_run` | Open a run and return its id. | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one event (fetched / skipped / empty / failed / blocked). | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Close a run with its final status. | str, str, str -> None | `LakeError` | as class | see class |

### `BaseStep` — `quant_cn.core.base_step` (L1)
- **Purpose:** Abstract unit of pipeline work: list its units, then run and report.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.FetchStep`, `pipeline.BaseRunner.run`, `pipeline.LocalRunner.run`, `pipeline.CompactStep`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `name` | Step name shown in progress and reports. | — -> str | — | as class | see class |
| `list_units` | Compute the work units (e.g. keys) just before running. | — -> list[str] | `QuantCnError` | as class | see class |
| `run` | Do the work listed by `list_units`. | str, ProgressHook \| None -> StepReport | `QuantCnError` | as class | see class |

### `BaseStore` — `quant_cn.core.base_store` (L1)
- **Purpose:** Abstract sink for raw fetch results and curated partitions.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `lake.ParquetWriter`, `core.BaseFetcher`, `lake.Compactor`, `data_loading.FetcherFactory`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`.
- **Tests:** `tests/core/test_base_classes.py` (TC-BAC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `write_raw` | Persist one fetch key's rows atomically. | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition atomically after validating its schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |

### `Clock` — `quant_cn.core.clock` (L1)
- **Purpose:** The single source of wall time, monotonic time and sleeping; tests inject a fake subclass.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`, `core.BaseFetcher.run`, `lake.RunLog`, `lake.Compactor.rebuild`, `pipeline.DownloadPipeline`, `cli.QuantCnCli`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.FetcherFactory`, `data_loading.PeriodSweepFetcher`, `lake.ProjectCatalog`.
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

### `Config` — `quant_cn.core.config` (L1)
- **Purpose:** The typed configuration injected everywhere: YAML defaults, machine overrides, environment.
- **Base:** BaseModel. **Depends on (injected):** —.
- **Used by:** `cli.QuantCnCli`, `data_loading.FetcherFactory`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`.
- **Tests:** `tests/core/test_config.py` (TC-C-001..008).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `load` | Build the configuration from `config/base.yaml`, `config/datasets.yaml`, optional `config/local.yaml`, the repo `.env` and the process environment. | Path \| None, Mapping[str, str] \| None -> Config | `ConfigError` | as class | see class |
| `get_dataset` | Look up one dataset spec by name. | str -> DatasetSpec | `ConfigError` | as class | see class |
| `get_start` | Download start date for a dataset: its own `start`, else long-history start if listed, else the default start. | str -> str | `ConfigError` | as class | see class |

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
- **Used by:** `core.Config`, `core.BaseFetcher`, `core.BaseStore`, `lake.ParquetWriter`, `lake.LakeCatalog`, `lake.Compactor.rebuild`, `data_loading.FetcherFactory.build`, `data_loading.DateSweepFetcher`, `data_loading.EnumFetcher`, `data_loading.PeriodSweepFetcher`, `pipeline.CompactStep`, `lake.DerivedViews`, `lake.ProjectCatalog`.
- **Tests:** `tests/core/test_dataset_spec.py` (TC-DS-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `get_raw_filename` | Hive-style raw file name for one fetch key. | str -> str | — | as class | see class |
| `build_schema` | The dataset's Schema (fields, text fields, primary key). | — -> Schema | `SchemaError` | as class | see class |

### `DateCodec` — `quant_cn.core.date_codec` (L1)
- **Purpose:** Validate and convert Tushare `YYYYMMDD` date strings and generate date keys for sweeps.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `core.Config.load`, `data_loading.DateSweepFetcher.list_keys`, `data_loading.PeriodSweepFetcher.list_keys`, `pipeline.DownloadPipeline.run`, `data_loading.FetcherFactory`, `cli.QuantCnCli`, `lake.PitAligner`, `visualization.PriceChart`.
- **Tests:** `tests/core/test_date_codec.py` (TC-DC-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `validate` | Return `value` unchanged if it is a valid `YYYYMMDD` date string. | str -> str | `ValueError` | as class | see class |
| `to_date` | Parse a `YYYYMMDD` string. | str -> dt.date | `ValueError` | as class | see class |
| `to_str` | Format a date as `YYYYMMDD`. | dt.date -> str | — | as class | see class |
| `list_quarter_ends` | Report periods (Mar 31, Jun 30, Sep 30, Dec 31) within [start, end]. | str, str -> list[str] | `ValueError` | as class | see class |
| `list_weekdays` | Monday-to-Friday dates within [start, end], for announcement-date sweeps. | str, str -> list[str] | `ValueError` | as class | see class |

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
- **Used by:** `core.docs.ContractChecker`, `core.docs.IndexChecker`, `core.docs.SizeChecker`, `core.docs.NameChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.QuantCnCli`.
- **Tests:** `tests/core/docs/test_code_scanner.py` (TC-CS-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `read_module` | Scan one file. | Path, Path -> ModuleInfo | `SyntaxError`, `OSError` | as class | see class |

### `CodeTableBuilder` — `quant_cn.core.docs.code_table_builder` (L1)
- **Purpose:** Turn src/ classes (AST + contract docstrings), the class registry and tests/ into the code-side tables of the `project` schema, one DataFrame per table with fixed columns.
- **Base:** none. **Depends on (injected):** Path, CodeScanner, DocstringParser, RegistryReader.
- **Used by:** `lake.ProjectCatalog`, `cli.QuantCnCli`.
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
- **Used by:** `scripts/lint_contracts.py`, `tests/test_contracts.py`, `lake.ProjectCatalog`, `cli.QuantCnCli`.
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
- **Used by:** `core.docs.DocTableBuilder`, `cli.QuantCnCli`.
- **Tests:** `tests/core/docs/test_decisions_reader.py` (TC-DR-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | All decisions in table order. | Path -> list[DecisionRecord] | `OSError` | as class | see class |

### `DocTableBuilder` — `quant_cn.core.docs.doc_table_builder` (L1)
- **Purpose:** Turn the INDEX.md tree, the files on disk, the decision log and the execution plans into the document-side tables of the `project` schema.
- **Base:** none. **Depends on (injected):** Path, RepoFiles, IndexReader, DecisionsReader, PlanReader.
- **Used by:** `lake.ProjectCatalog`, `cli.QuantCnCli`.
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
- **Used by:** `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.QuantCnCli`.
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
- **Used by:** `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.QuantCnCli`.
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
- **Used by:** `core.docs.IndexReader`, `core.docs.RegistryReader`, `core.docs.ConventionReader`, `core.docs.ContractLinter`, `core.docs.DecisionsReader`, `core.docs.PlanReader`, `cli.QuantCnCli`.
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
- **Used by:** `core.docs.DocTableBuilder`, `cli.QuantCnCli`.
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
- **Used by:** `core.docs.ContractChecker`, `core.docs.ContractLinter`, `core.docs.CodeTableBuilder`, `cli.QuantCnCli`.
- **Tests:** `tests/core/docs/test_registry_reader.py` (TC-RR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | MarkdownTableReader -> None | — | callers of the class | — |
| `read` | Parse the registry file. | Path -> RegistryInfo | `OSError` | as class | see class |

### `RepoFiles` — `quant_cn.core.docs.repo_files` (L1)
- **Purpose:** The set of repository files a linter should see: `git ls-files --cached --others --exclude-standard`, so .gitignore (caches, .env, lake guards) decides what is ignored.
- **Base:** none. **Depends on (injected):** Path.
- **Used by:** `core.docs.IndexChecker`, `core.docs.ContractLinter`, `core.docs.DocTableBuilder`, `cli.QuantCnCli`.
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
- **Used by:** `core.DatasetSpec.build_schema`.
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
- **Used by:** `core.BaseFetcher.run`, `core.BaseStep.run`, `lake.Compactor.rebuild`, `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `pipeline.FetchStep`, `pipeline.PipelineReport`, `pipeline.CompactStep`, `pipeline.DeriveStep`.
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

### `FetcherFactory` — `quant_cn.data_loading.fetcher_factory` (L3)
- **Purpose:** Build the right fetcher for a DatasetSpec and inject the shared dependencies.
- **Base:** none. **Depends on (injected):** Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec.
- **Used by:** `pipeline.DownloadPipeline`, `cli.QuantCnCli`.
- **Tests:** `tests/data_loading/test_fetcher_factory.py` (TC-FF-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec -> None | — | callers of the class | — |
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
- **Purpose:** Whole-market daily sweeps: trade_date keys are trading days (daily, adj_factor, daily_basic, moneyflow, stk_limit); ann_date keys are weekdays (event datasets).
- **Base:** BaseFetcher. **Depends on (injected):** DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec.
- **Used by:** `data_loading.FetcherFactory.build`.
- **Tests:** `tests/data_loading/test_fetchers.py` (TC-DSF-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DatasetSpec, BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, Clock, TradingCalendar, DateCodec -> None | — | callers of the class | — |
| `list_keys` | Trading days (trade_date) or weekdays (ann_date) in [start, end]. | str, str -> list[str] | `LakeError`, `ValueError` | as class | see class |
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

### `HttpTransport` — `quant_cn.data_loading.http_transport` (L3)
- **Purpose:** Send one JSON POST and return the decoded JSON object.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `data_loading.TushareClient`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `fetch_json` | POST `payload` as JSON to `url`. | str, Mapping[str, Any], float -> dict[str, Any] | `OSError`, `ValueError` | as class | see class |

### `TushareClient` — `quant_cn.data_loading.tushare_client` (L3)
- **Purpose:** Query Tushare Pro: one logical query follows limit/offset paging until a short page and returns all rows; rate-limit replies wait and retry without spending retries; permission replies fail fast as PermissionDeniedError; other failures retry up to `retries`.
- **Base:** BaseApiClient. **Depends on (injected):** TushareConfig, Clock, HttpTransport | None.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/data_loading/test_tushare_client.py` (TC-TC-001..007).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | TushareConfig, Clock, HttpTransport \| None -> None | — | callers of the class | — |
| `query` | Fetch every page of one query. | str, Mapping[str, str], Sequence[str] -> pd.DataFrame | `ConfigError`, `PermissionDeniedError`, `DataSourceError` | as class | see class |
| `_fetch_page` (private) | internal helper over 20 lines | str, Mapping[str, object], Sequence[str] -> dict[str, Any] | — | internal | — |

### `Compactor` — `quant_cn.lake.compactor` (L2)
- **Purpose:** Rebuild a dataset's curated partitions from its raw files: select declared fields, cast dtypes, drop duplicate primary keys (keeping one), sort by partition date then key, validate, write, and record a manifest in `meta/manifest/<dataset>.json`.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, BaseStore, Clock.
- **Used by:** `cli.QuantCnCli`, `pipeline.CompactStep`, `pipeline.CuratePipeline`.
- **Tests:** `tests/lake/test_compactor.py` (TC-CO-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, BaseStore, Clock -> None | — | callers of the class | — |
| `rebuild` | Replace the curated partitions of `spec` (all years, or only `years`). | DatasetSpec, set[int] \| None -> StepReport | `SchemaError`, `LakeError` | as class | see class |

### `DerivedViews` — `quant_cn.lake.derived_views` (L2)
- **Purpose:** Create the `derived` schema views built only from curated/: `derived.prices_adj` (daily bars joined to adj_factor, close_adj = close * adj_factor; PRICE_PANEL columns) and `derived.fundamentals_long` (every period-swept dataset unpivoted to one row per numeric field and announced version; statements filtered to report_type = '1').
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, Mapping[str, DatasetSpec].
- **Used by:** `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `cli.QuantCnCli`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_derived_views.py` (TC-DV-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, Mapping[str, DatasetSpec] -> None | — | callers of the class | — |
| `refresh` | (Re)create every derived view whose curated inputs exist; drop the others. | — -> list[str] | `LakeError` | as class | see class |

### `FetchLog` — `quant_cn.lake.fetch_log` (L2)
- **Purpose:** Record finished (dataset, key) pairs in `meta.fetch_log`, mirror them to `meta/fetch_log.parquet` on save, and rebuild the table after the DuckDB file is lost.
- **Base:** BaseFetchLog. **Depends on (injected):** LakeCatalog.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_fetch_log.py` (TC-FL-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | `LakeError` | callers of the class | — |
| `mirror_path` | Location of the durable parquet copy. | — -> Path | — | as class | see class |
| `read_done_keys` | Keys recorded for `dataset`. | str -> set[str] | `LakeError` | as class | see class |
| `mark_done` | Upsert one finished key. | str, str, int, Path \| None -> None | `LakeError` | as class | see class |
| `save` | Atomically rewrite `meta/fetch_log.parquet` from the table. | — -> Path | `LakeError` | as class | see class |
| `rebuild_from_mirror` | Rebuild the table from the parquet mirror, then add raw files the mirror does not know. | — -> int | `LakeError` | as class | see class |

### `LakeCatalog` — `quant_cn.lake.lake_catalog` (L2)
- **Purpose:** Own the lake's single DuckDB connection (`meta/quant_cn.duckdb`): schemas `raw`, `curated`, `meta`; one view per dataset and zone; `meta.dataset_meta`; generated INDEX.md files. The DuckDB file is disposable: `rebuild()` recreates it from the parquet files.
- **Base:** none. **Depends on (injected):** Path, Mapping[str, DatasetSpec], bool.
- **Used by:** `lake.FetchLog`, `lake.RunLog`, `lake.LakeQuery`, `lake.Compactor`, `pipeline.FetchStep.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog`.
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
- **Used by:** `lake.TradingCalendar`, `lake.Compactor.rebuild`, `cli.QuantCnCli`, `pipeline.CuratePipeline`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`.
- **Tests:** `tests/lake/test_lake_query.py` (TC-LQ-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog -> None | — | callers of the class | — |
| `sql` | Execute a query and return the result as a DataFrame. | str, Sequence[object] \| None -> pd.DataFrame | `LakeError` | as class | see class |
| `has_view` | True if `schema.view` exists in the catalog. | str -> bool | `LakeError` | as class | see class |
| `read_prices` | Adjusted daily prices from `derived.prices_adj` for a date range. | str, str, Sequence[str] \| None -> pd.DataFrame | `LakeError`, `SchemaError` | as class | see class |

### `ParquetWriter` — `quant_cn.lake.parquet_writer` (L2)
- **Purpose:** Write raw fetch results and curated partitions as zstd parquet, atomically (write `.tmp`, fsync, rename), so a crash never leaves a half-written file.
- **Base:** BaseStore. **Depends on (injected):** Path.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_parquet_writer.py` (TC-PW-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Path -> None | — | callers of the class | — |
| `get_raw_path` | Target path of one raw fetch key. | DatasetSpec, str -> Path | — | as class | see class |
| `get_curated_path` | Target path of one curated partition. | DatasetSpec, int \| None -> Path | — | as class | see class |
| `write_raw` | Persist one fetch key's rows, dtypes coerced by the dataset schema (dates stay strings). | DatasetSpec, str, pd.DataFrame -> Path \| None | `SchemaError`, `LakeError` | as class | see class |
| `write_curated` | Replace one curated partition after validating it against the dataset schema. | DatasetSpec, int \| None, pd.DataFrame -> Path | `SchemaError`, `LakeError` | as class | see class |

### `PitAligner` — `quant_cn.lake.pit_aligner` (L2)
- **Purpose:** Align fundamentals to trading days without look-ahead. A version announced on `known_on` (f_ann_date / ann_date) becomes effective on the first trading day strictly after it; on each day the visible value of a field is the latest report period effective so far, in its latest effective restatement. Older-period restatements never replace a newer period. Built as the DuckDB view `derived.fundamentals_states` (one row per change) and read with an ASOF JOIN from trading days.
- **Base:** none. **Depends on (injected):** LakeCatalog, LakeQuery, DateCodec.
- **Used by:** `pipeline.CuratePipeline`, `research_space/main.ipynb`, `pipeline.DeriveStep`, `cli.QuantCnCli`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_pit_aligner.py` (TC-PA-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, LakeQuery, DateCodec -> None | — | callers of the class | — |
| `refresh` | (Re)create `derived.fundamentals_states` from derived.fundamentals_long and the curated trading calendar. | — -> str | `LakeError` | as class | see class |
| `read_aligned` | Point-in-time values for every trading day in [start, end] and every (ticker, field) that has become visible by that day. | str, str, Sequence[str] \| None, Sequence[str] \| None -> pd.DataFrame | `ValueError`, `LakeError` | as class | see class |

### `ProjectCatalog` — `quant_cn.lake.project_catalog` (L2)
- **Purpose:** Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes, methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings, plus views tree, class_graph, stale and todo. Markdown and code stay the source of truth; the schema is dropped and rebuilt, never edited.
- **Base:** none. **Depends on (injected):** LakeCatalog, CodeTableBuilder, DocTableBuilder, Mapping[str, DatasetSpec], ContractLinter, Clock.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_project_catalog.py` (TC-PJC-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, CodeTableBuilder, DocTableBuilder, Mapping[str, DatasetSpec], ContractLinter, Clock -> None | — | callers of the class | — |
| `rebuild` | Drop and recreate every table and view of schema `project` in one transaction. | bool -> dict[str, int] | `LakeError`, `RuntimeError` | as class | see class |

### `RunLog` — `quant_cn.lake.run_log` (L2)
- **Purpose:** Append run and per-key events to `meta.run_log` (run_id, started_at, finished_at, kind, dataset, key, status, n_rows, duration_ms, message) and echo them to logging.
- **Base:** BaseRunLog. **Depends on (injected):** LakeCatalog, Clock.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_run_log.py` (TC-RL-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeCatalog, Clock -> None | `LakeError` | callers of the class | — |
| `open_run` | Insert the run row (dataset and key NULL, status "running"). | str -> str | `LakeError` | as class | see class |
| `record_event` | Append one key event. | str, str, str, str, int, int, str -> None | `LakeError` | as class | see class |
| `close_run` | Set status, message and finished_at on the run row. | str, str, str -> None | `LakeError` | as class | see class |

### `TradingCalendar` — `quant_cn.lake.trading_calendar` (L2)
- **Purpose:** Answer trading-day questions (sessions in a range, is_open, next, prev) from the SSE calendar in the lake; loads lazily so it works after trade_cal is fetched in the same run.
- **Base:** none. **Depends on (injected):** LakeQuery.
- **Used by:** `data_loading.DateSweepFetcher.list_keys`, `data_loading.FetcherFactory`, `cli.QuantCnCli`.
- **Tests:** `tests/lake/test_trading_calendar.py` (TC-TCA-001..004).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | LakeQuery -> None | — | callers of the class | — |
| `refresh` | Drop the cached calendar so the next call re-reads trade_cal. | — -> None | — | as class | see class |
| `list_sessions` | Trading days within [start, end]. | str, str -> list[str] | `LakeError` | as class | see class |
| `is_open` | True if `date` is a trading day. | str -> bool | `LakeError` | as class | see class |
| `get_next` | First trading day strictly after `date`. | str -> str | `LakeError` | as class | see class |
| `get_prev` | Last trading day strictly before `date`. | str -> str | `LakeError` | as class | see class |

### `CompactStep` — `quant_cn.pipeline.curate_pipeline` (L4)
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

### `DeriveStep` — `quant_cn.pipeline.curate_pipeline` (L4)
- **Purpose:** Build the derived views and the PIT states view, then record a digest per derived view.
- **Base:** BaseStep. **Depends on (injected):** DerivedViews, PitAligner, LakeQuery, Path.
- **Used by:** `pipeline.CuratePipeline`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | DerivedViews, PitAligner, LakeQuery, Path -> None | — | callers of the class | — |
| `name` | Step name. | — -> str | — | as class | see class |
| `list_units` | One unit: the derived layer. | — -> list[str] | — | as class | see class |
| `run` | Refresh derived views (and PIT states when fundamentals exist), write digests. | str, ProgressHook \| None -> StepReport | `LakeError` | as class | see class |
| `build_digests` | md5 over every row of each view, rows ordered by their text form; equal digests mean byte-identical derived data. | Sequence[str] -> dict[str, str] | `LakeError` | as class | see class |

### `CuratePipeline` — `quant_cn.pipeline.curate_pipeline` (L4)
- **Purpose:** Rebuild everything below raw/: compact every dataset, create derived views and PIT states, regenerate lake indexes, and record digests in meta/manifest/derived_digests.json.
- **Base:** none. **Depends on (injected):** Config, Compactor, DerivedViews, PitAligner, LakeQuery, LakeCatalog, BaseRunner.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/pipeline/test_curate_pipeline.py` (TC-CP-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, Compactor, DerivedViews, PitAligner, LakeQuery, LakeCatalog, BaseRunner -> None | — | callers of the class | — |
| `run` | Compact the datasets (default all), then derive and index. | Sequence[str] \| None -> PipelineReport | `ConfigError`, `SchemaError`, `LakeError` | as class | see class |

### `FetchStep` — `quant_cn.pipeline.download_pipeline` (L4)
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

### `DownloadPipeline` — `quant_cn.pipeline.download_pipeline` (L4)
- **Purpose:** Resolve which datasets and date ranges to download, run one FetchStep per dataset through the runner, and regenerate the lake indexes; `dry_run` lists pending keys without calling the API.
- **Base:** none. **Depends on (injected):** Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/pipeline/test_download_pipeline.py` (TC-DP-001..005).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | Config, FetcherFactory, BaseRunner, LakeCatalog, BaseFetchLog, Clock, DateCodec -> None | — | callers of the class | — |
| `run` | Download the requested datasets (default: config.download.order). | Sequence[str] \| None, str \| None, str \| None, bool, bool -> PipelineReport | `ConfigError`, `ValueError`, `DataSourceError` | as class | see class |

### `PipelineReport` — `quant_cn.pipeline.runner` (L4)
- **Purpose:** Result of one pipeline run: its id, overall status and one StepReport per step.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner.run`, `pipeline.DownloadPipeline.run`, `cli.QuantCnCli`, `pipeline.BaseRunner`, `pipeline.CuratePipeline`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `list_blocked` | Names of steps blocked by missing permissions. | — -> list[str] | — | as class | see class |
| `to_frame` | One row per step for display or logging. | — -> pd.DataFrame | — | as class | see class |

### `BaseRunner` — `quant_cn.pipeline.runner` (L4)
- **Purpose:** Extension point for how steps are executed (local now, Prefect later, D-022); steps never import the runner's backend.
- **Base:** ABC. **Depends on (injected):** —.
- **Used by:** `pipeline.LocalRunner`, `pipeline.DownloadPipeline`, `pipeline.CuratePipeline`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `run` | Execute steps in order under one run id. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `LocalRunner` — `quant_cn.pipeline.runner` (L4)
- **Purpose:** Run steps serially in this process with a rich progress bar per step; a permission failure marks the step blocked and continues; any other project error closes the run as failed and re-raises (finished keys stay done).
- **Base:** BaseRunner. **Depends on (injected):** BaseRunLog, Console | None, bool.
- **Used by:** `cli.QuantCnCli`.
- **Tests:** `tests/pipeline/test_runner.py` (TC-LR-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | BaseRunLog, Console \| None, bool -> None | — | callers of the class | — |
| `run` | See BaseRunner.run. | str, Sequence[BaseStep] -> PipelineReport | `QuantCnError` | as class | see class |

### `BaseChart` — `quant_cn.visualization.base_chart` (L5)
- **Purpose:** Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages); the base applies theme, size, hover and export.
- **Base:** ABC. **Depends on (injected):** ChartTheme, int, int.
- **Used by:** `visualization.PriceChart`.
- **Tests:** `tests/visualization/test_charts.py` (TC-BCA-001..002).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, int, int -> None | `TypeError` | callers of the class | — |
| `build_figure` | Build the unthemed figure from the input frame. | pd.DataFrame -> go.Figure | `ValueError`, `SchemaError` | as class | see class |
| `render` | Build the figure and apply the theme: surfaces, ink, recessive grid, unified hover. | pd.DataFrame -> go.Figure | `ValueError`, `SchemaError` | as class | see class |
| `to_html` | The themed chart as an HTML fragment (plotly.js from its CDN). | pd.DataFrame -> str | `ValueError`, `SchemaError` | as class | see class |
| `write_html` | Save the themed chart as a standalone HTML page. | pd.DataFrame, Path -> Path | `ValueError`, `SchemaError`, `OSError` | as class | see class |

### `ChartTheme` — `quant_cn.visualization.chart_theme` (L5)
- **Purpose:** The colour and font tokens every chart reads, so charts are written against roles, never raw hex. Values follow the dataviz reference palette; `up`/`down` are its red and green slots (A-share convention: red up, green down), validated per mode; the light pair sits in the CVD 6-8 band, so up candles are hollow as the secondary encoding.
- **Base:** none. **Depends on (injected):** —.
- **Used by:** `visualization.BaseChart`, `visualization.PriceChart`.
- **Tests:** `tests/visualization/test_charts.py` (TC-CT-001..001).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `from_mode` | The theme for a display mode. | Mode -> ChartTheme | `ValueError` | as class | see class |

### `PriceChart` — `quant_cn.visualization.price_chart` (L5)
- **Purpose:** Daily candles (backward-adjusted by default: OHLC x adj_factor) over a volume panel for one ticker. Two stacked panels with their own y-axes (never a dual axis); x is a category axis of trading days so non-trading days leave no gaps. Up candles hollow, down candles filled.
- **Base:** BaseChart. **Depends on (injected):** ChartTheme, str, DateCodec, bool, int, int.
- **Used by:** `research_space/main.ipynb`.
- **Tests:** `tests/visualization/test_charts.py` (TC-PC-001..003).

| Method | Purpose | Input -> Output | Raises | Used by | TC IDs |
|---|---|---|---|---|---|
| `__init__` | wire dependencies | ChartTheme, str, DateCodec, bool, int, int -> None | — | callers of the class | — |
| `build_figure` | Candles and volume for `ts_code`. | pd.DataFrame -> go.Figure | `SchemaError`, `ValueError` | as class | see class |

## C. Abstract base classes / extension points

| Class | Module | Layer | Purpose | Abstract methods (purpose each) | Known subclasses | Added |
|---|---|---|---|---|---|---|
| `BaseApiClient` | `quant_cn.core.base_api_client` | 1 | Abstract vendor client: one logical query returns all pages as one DataFrame. | `query`: Run one query and return every row across pages. | `TushareClient` | 2026-09-27 |
| `BaseFetchLog` | `quant_cn.core.base_fetch_log` | 1 | Abstract record of which (dataset, key) pairs are fully downloaded. | `read_done_keys`: All keys recorded as done for a dataset.; `mark_done`: Record a finished key, replacing any earlier record for it.; `save`: Make recorded keys durable (e.g. write the parquet mirror). | `FetchLog` | 2026-09-27 |
| `BaseFetcher` | `quant_cn.core.base_fetcher` | 1 | Download one dataset as a sequence of keys | `list_keys`: All fetch keys for [start, end], ascending.; `build_params`: API parameters for one key. | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher` | 2026-09-27 |
| `BaseRunLog` | `quant_cn.core.base_run_log` | 1 | Abstract append-only log of runs and per-key events | `open_run`: Open a run and return its id.; `record_event`: Append one event (fetched / skipped / empty / failed / blocked).; `close_run`: Close a run with its final status. | `RunLog` | 2026-09-27 |
| `BaseStep` | `quant_cn.core.base_step` | 1 | Abstract unit of pipeline work: list its units, then run and report. | `name`: Step name shown in progress and reports.; `list_units`: Compute the work units (e.g. keys) just before running.; `run`: Do the work listed by `list_units`. | `CompactStep`, `DeriveStep`, `FetchStep` | 2026-09-27 |
| `BaseStore` | `quant_cn.core.base_store` | 1 | Abstract sink for raw fetch results and curated partitions. | `write_raw`: Persist one fetch key's rows atomically.; `write_curated`: Replace one curated partition atomically after validating its schema. | `ParquetWriter` | 2026-09-27 |
| `BaseChecker` | `quant_cn.core.docs.base_checker` | 1 | Abstract repository check: inspect the tree, return findings (empty = pass). | `run`: Run the check over the repository. | `ContractChecker`, `IndexChecker`, `NameChecker`, `SizeChecker` | 2026-09-27 |
| `BaseRunner` | `quant_cn.pipeline.runner` | 4 | Extension point for how steps are executed (local now, Prefect later, D-022) | `run`: Execute steps in order under one run id. | `LocalRunner` | 2026-09-27 |
| `BaseChart` | `quant_cn.visualization.base_chart` | 5 | Abstract chart: subclasses build a plotly figure from a DataFrame (frames only, never objects from other packages) | `build_figure`: Build the unthemed figure from the input frame. | `PriceChart` | 2026-09-27 |

## D. Exceptions

| Class | Module | Parent | Purpose / raised when | Raised by | Added |
|---|---|---|---|---|---|
| `QuantCnError` | `quant_cn.core.exceptions` | `Exception` | Root of every exception the package raises, so callers catch project errors in one place. | `pipeline.LocalRunner.run`, `cli.QuantCnCli.run`, `core.ConfigError`, `core.DataSourceError`, `core.LakeError`, `core.SchemaError` | 2026-09-27 |
| `ConfigError` | `quant_cn.core.exceptions` | `QuantCnError` | Configuration is missing, malformed or unsafe (e.g. lake root inside the repository). | `core.Config.load`, `core.Config.get_dataset`, `data_loading.TushareClient`, `data_loading.FetcherFactory.build`, `pipeline.DownloadPipeline.run`, `pipeline.CuratePipeline` | 2026-09-27 |
| `SchemaError` | `quant_cn.core.exceptions` | `QuantCnError` | A DataFrame does not satisfy its declared Schema (columns, dtypes, primary key). | `core.Schema.normalize`, `core.Schema.validate` | 2026-09-27 |
| `DataSourceError` | `quant_cn.core.exceptions` | `QuantCnError` | The external data source failed: API error code, retries exhausted, malformed response. | `data_loading.TushareClient.query`, `core.BaseFetcher.run`, `core.PermissionDeniedError` | 2026-09-27 |
| `PermissionDeniedError` | `quant_cn.core.exceptions` | `DataSourceError` | The account lacks permission (points) for an endpoint; the dataset is blocked, not broken. | `data_loading.TushareClient.query`, `pipeline.LocalRunner.run` | 2026-09-27 |
| `LakeError` | `quant_cn.core.exceptions` | `QuantCnError` | The local lake cannot be read or written: missing dataset, failed atomic write, bad catalog. | `lake.ParquetWriter`, `lake.TradingCalendar`, `lake.LakeQuery.sql`, `cli.QuantCnCli`, `lake.Compactor`, `pipeline.DownloadPipeline`, `lake.FetchLog`, `lake.LakeCatalog`, `lake.RunLog`, `pipeline.DeriveStep`, `lake.DerivedViews`, `lake.PitAligner`, `lake.ProjectCatalog` | 2026-09-27 |

## E. Schemas (DataFrame / typed records)

| Schema | Module | Purpose | Index | Columns (dtype) | Invariants | Produced by | Consumed by | Added |
|---|---|---|---|---|---|---|---|---|
| `PRICE_PANEL` | `quant_cn.core.frames` | daily bars with adjustment factor and adjusted close | long; key (trade_date, ts_code) | trade_date (string), ts_code (string), open (float64), high (float64), low (float64), close (float64), pre_close (float64), vol (float64), amount (float64), adj_factor (float64), close_adj (float64) | key unique and non-null | `lake.LakeQuery.prices` (phase 5) | factors, engine, charts (plans 03-04) | 2026-09-27 |
| `FUNDAMENTALS_PIT` | `quant_cn.core.frames` | point-in-time fundamentals, one value per field per trading day | long; key (trade_date, ts_code, field) | trade_date (string), ts_code (string), field (string), value (float64), end_date (string), ann_date (string) | key unique and non-null | `lake.PitAligner` (phase 5) | `QualityFactor`, `ValueFactor` (plan 03) | 2026-09-27 |

## F. Allowed standalone functions (`core/utils` only, with justification)

| Function | Module | Purpose | Input -> Output | Why not a class method | Used by | Tests | Added |
|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | |
