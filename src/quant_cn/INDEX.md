# src/quant_cn/

The package. A layer imports only its own layer or lower (CODING_STANDARD §2.1); `pipeline`/`statistic` never import each other; `back_testing`/`portfolio`/`visualization` are mutually independent; nothing imports `research_space`.

## Folders
| Folder | Purpose |
|---|---|
| [`back_testing/`](back_testing/INDEX.md) | L5 engine, fills constrained by stk_limit, costs, results |
| [`core/`](core/INDEX.md) | L1 base classes, exceptions, Config, Schema, DateCodec, TickerNormalizer, logging |
| [`data_loading/`](data_loading/INDEX.md) | L3 Tushare client and one fetcher per sweep pattern; writes into the lake |
| [`lake/`](lake/INDEX.md) | L2 parquet writer, DuckDB catalog, fetch log, compactor, query API, PIT aligner |
| [`pipeline/`](pipeline/INDEX.md) | L4 resumable steps: download -> compact -> curate -> features |
| [`portfolio/`](portfolio/INDEX.md) | L5 position sizing, constraints, rebalancing schedules |
| [`statistic/`](statistic/INDEX.md) | L4 factor stats (IC, quantile returns), descriptive stats, regressions |
| [`visualization/`](visualization/INDEX.md) | L5 charts for prices, factors, backtest results; plotly, themed, notebook + HTML export |

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `cli.py` | Command-line entry point and composition root (L6): wires config, lake and pipeline | `QuantCnCli` |
