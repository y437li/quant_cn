# src/quant_cn/pipeline/

L4: resumable steps: download -> compact -> curate -> features. May import from: L1–L3.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `curate_pipeline.py` | raw -> curated -> derived: compaction, derived views, PIT states, indexes, digests | `CompactStep`, `DeriveStep`, `CuratePipeline` |
| `download_pipeline.py` | Download datasets from Tushare into the lake in dependency order (DATA_LOADING_DESIGN §2.1) | `FetchStep`, `DownloadPipeline` |
| `prefect_runner.py` | Run pipeline steps as a Prefect 3 flow so runs are visible in the Prefect UI (D-022) | `PrefectRunner` |
| `runner.py` | Runners execute BaseSteps in order; LocalRunner adds rich progress and RunLog events (D-022) | `PipelineReport`, `BaseRunner`, `LocalRunner` |
| `universe_step.py` | The tradeable universe per session, materialised to derived/universe (plan 04 phase 3) | `UniverseStep` |
