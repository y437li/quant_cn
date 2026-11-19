# src/quant_cn/pipeline/

L4: resumable steps: download -> compact -> curate -> features. May import from: L1–L3.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `curate_pipeline.py` | raw -> curated -> derived: compaction, derived views, PIT states, indexes, digests | `CompactStep`, `DeriveStep`, `CuratePipeline` |
| `download_pipeline.py` | Download datasets from Tushare into the lake in dependency order (DATA_LOADING_DESIGN §2.1) | `FetchStep`, `DownloadPipeline` |
| `evaluation_step.py` | Evaluate the campaign's features and persist reports and trials (plan 04 phase 5) | `EvaluationStep` |
| `feature_step.py` | Processed factors and the combined score, materialised to derived/features (plan 04 phase 5) | `FeatureStep` |
| `make_target_runner.py` | run one make target as a subprocess, echo output, keep the tail, kill at the time limit (plan 38) | `MakeTargetRunner` |
| `prefect_runner.py` | Run pipeline steps as a Prefect 3 flow so runs are visible in the Prefect UI (D-022) | `PrefectRunner` |
| `risk_model_step.py` | Fit the risk model and write derived/risk_* frames per year (plan 05) | `RiskModelStep` |
| `risk_validation_writer.py` | The risk model's acceptance report: bias statistics and fit (plan 05) | `RiskValidationWriter` |
| `runner.py` | Runners execute BaseSteps in order; LocalRunner adds rich progress and RunLog events (D-022) | `PipelineReport`, `BaseRunner`, `LocalRunner` |
| `task_status_builder.py` | task_status.json from the task ledger: latest run and per-step history (plan 38) | `TaskStatusBuilder` |
| `universe_step.py` | The tradeable universe per session, materialised to derived/universe (plan 04 phase 3) | `UniverseStep` |
| `update_all_runner.py` | run update steps in order, continue past failures, skip dependents, record the ledger (plan 38) | `TargetRunner`, `UpdateAllRunner` |
