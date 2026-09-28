# Roadmap — the one status board

Every plan appears here with its status. The `plan` skill updates this table whenever a plan's status
changes. Designs live in `../architecture/`, rules in `../standards/`, choices in `../decisions/`.

| Plan | Builds | Implements design | Depends on | Status |
|---|---|---|---|---|
| [00 model roles](00_model_roles.md) | executor agent (Opus), settings, edit-guard hook, skill routing | D-016 | — | approved, not applied |
| [01 data lake](01_data_lake.md) | `core`, `lake`, `data_loading`, download + curate pipelines, PIT views, first charts, `main.ipynb` | FOLDER_STRUCTURE §2, DATA_LOADING_DESIGN, SRC_DESIGN §2.1–2.4 | 00 (not applied; user chose to proceed) | **done** 2026-09-27 (5 commits, 174 tests, 95% coverage); deferred: dense price reindex, `to_png`, `PanelChart` |
| [02 project catalog](02_project_catalog.md) | `ProjectCatalog`: repo tree, registry, plans as SQL | D-017 | 01 (done) | doing — ph1 delivered (D-033); ph2–4 started by quant-cn-b7 |
| [03 VIX calculation](03_vix_calculation.md) | `calculation` package: CBOE-method VIX; `opt_basic`, `opt_daily`, `shibor` datasets; `DateWindowFetcher`; `CalculationStep`; `SeriesChart`; iVIX replication notebook | CALCULATION_DESIGN v1.0, SRC_DESIGN §2.4b | 01 (done) | approved, not started (after 02) |
| 04 factors | phase 1: lake read API (`read_panel`, `read_fundamentals_pit`, `read_reference`, dense prices, `register_frame`, `PanelCache`, D-041); then `statistic` primitives; `factor` package: `BaseFactor`, six factors in `factor/library/`, `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner`, `FactorFactory`; `UniverseStep`, `FeaturePipeline`, `FactorChart`; pyproject import-linter layers updated to the 8-layer table | SRC_DESIGN §2.4–2.6 | 01 | to draft |
| 05 portfolio + backtest | constructors, constraints, schedule; engine, execution, costs, result, analyzer; equity/position charts, `ReportBuilder` | SRC_DESIGN §2.7–2.9 | 04 | to draft |
| 06 events | forecast, express, holdertrade, share_float datasets (`DateWindowFetcher`), event factors, Shenwan industries | DATA_CATALOG, SRC_DESIGN | 01, 04 | to draft |
| 07 research ops | walk-forward, parameter search, multi-strategy; `PrefectRunner` (D-022) | SRC_DESIGN §5 | 05 | to draft |

Status vocabulary: `to draft` → `drafted, awaiting approval` → `approved, not started` → `doing (phase N)` → `done` | `superseded`.
