# src/quant_cn/

The package. A layer imports only its own layer or lower (CODING_STANDARD §2.1); `pipeline`/`statistic` never import each other; `back_testing`/`portfolio`/`visualization` are mutually independent; nothing imports `research_space`.

## Folders
| Folder | Purpose |
|---|---|
| [`back_testing/`](back_testing/INDEX.md) | L5 engine, fills constrained by stk_limit, costs, results |
| [`calculation/`](calculation/INDEX.md) | L4 calculation: CBOE VIX, Black-76, rate curve, option chains |
| [`core/`](core/INDEX.md) | L1 base classes, exceptions, Config, Schema, DateCodec, TickerNormalizer, logging |
| [`data_loading/`](data_loading/INDEX.md) | L3 Tushare client and one fetcher per sweep pattern; writes into the lake |
| [`factor/`](factor/INDEX.md) | TODO purpose |
| [`industry_graph/`](industry_graph/INDEX.md) | L4: industry-chain graph — report parsing, taxonomy, extraction, query (plan 12) |
| [`lake/`](lake/INDEX.md) | L2 parquet writer, DuckDB catalog, fetch log, compactor, query API, PIT aligner |
| [`pipeline/`](pipeline/INDEX.md) | L4 resumable steps: download -> compact -> curate -> features |
| [`portfolio/`](portfolio/INDEX.md) | L5 position sizing, constraints, rebalancing schedules |
| [`risk/`](risk/INDEX.md) | L5 Barra-style multi-factor risk model (CNE5 family): exposures, factor returns, covariance, specific risk, validation |
| [`statistic/`](statistic/INDEX.md) | L4 factor stats (IC, quantile returns), descriptive stats, regressions |
| [`visualization/`](visualization/INDEX.md) | L5 charts for prices, factors, backtest results; plotly, themed, notebook + HTML export |

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `cli.py` | Command-line entry point and composition root (L6): wires config, lake and pipeline | `QuantCnCli`, `ResearchCommands` |
| `document_commands.py` | CLI `download-docs` (plan 12 ph2, D-101) and `import-labels` (label files -> derived/labels parquet, plan 28 ph0) | `DocumentCommands` |
| `gauge_commands.py` | CLI `retail-gauge` (daily readings), `retail-gauge-backtest` (walk-forward + evaluation) (plan 21 ph3) and `opportunity-list` (ph4) | `GaugeCommands` |
| `service_builder.py` | Composition of pipelines, runners and readers from Config (the cli's service factory) | `ServiceBuilder` |
| `app_service_builder.py` | composition root for the app's portfolio documents: watchlist and holdings risk with condition evaluation (plan 15 ph7f) | `AppServiceBuilder` |
| `report_commands.py` | CLI `morning-report`: last session from the lake calendar, build and send (or --dry-run) the two morning e-mails (plan 15 ph7e); `macro-monitor` writes macro_monitor.json (ph7h) | `ReportCommands` |
| `update_commands.py` | CLI `update-all`: every daily update in order, task ledger, summary, task_status.json (plan 38) | `UpdateCommands` |
