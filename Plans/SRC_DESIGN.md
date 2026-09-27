# `src/quant_cn` Design (DRAFT v0.1, 2026-09-27, decision D-020 proposed)

How the eight packages fit together, what each owns, where the extension points are, and the shared
frames that let independent packages talk without importing each other. Plan-level detail lives in
`Plans/plans/`; this document is the map.

## 1. Data flow

```
Tushare ──► data_loading ──► lake.raw ──► lake.curated / derived ──► LakeQuery (SQL, PIT-safe)
                                                                          │
              pipeline.FeaturePipeline ◄── statistic.BaseFactor ◄─────────┤  PricePanel, FundamentalsPIT
                       │                                                  │
                       ▼ FactorPanel, UniversePanel                        │
              portfolio.BasePortfolioConstructor ──► TargetWeightPanel     │
                       │                                                  │
                       ▼                                                  │
              back_testing.BacktestEngine ──► BacktestResult.to_frame()   │
                       │                                                  │
                       ▼ EquityCurve, TradeLog, PositionPanel              │
              visualization.BaseChart / ReportBuilder ◄───────────────────┘
```
Everything between packages is a **DataFrame with a registered Schema** (§3). Objects never cross a
package boundary except `core` types.

## 2. Packages

### 2.1 `core` (L1) — contracts everyone shares
| Class | Purpose |
|---|---|
| `Config` (+ `LakeConfig`, `TushareConfig`, `DownloadConfig`, `UniverseConfig`, `BacktestConfig`) | typed view of `config/*.yaml`, env overrides; injected everywhere |
| `DatasetSpec` (+ `SweepSpec`, `PartitionSpec`) | one dataset's endpoint, key, known-on, partition, schema |
| `QuantCnError` → `ConfigError`, `SchemaError`, `DataSourceError`, `LakeError`, `BacktestError` | the only exceptions raised |
| `Schema` | DataFrame contract: columns, dtypes, primary key, invariants; `validate()`, `empty()` |
| `frames` (module of `Schema` instances) | the shared panel schemas of §3 |
| `DateCodec`, `TickerNormalizer` | the only date/ticker conversions (D-005) |
| `Clock` | injectable "now"; real in production, fixed in tests and backtests |
| Bases: `BaseApiClient`, `BaseStore`, `BaseFetchLog`, `BaseFetcher`, `BaseStep` | extension points used by two or more layers |

### 2.2 `lake` (L2) — storage, catalog, query
| Class | Purpose |
|---|---|
| `ParquetWriter` | atomic hive-named parquet writes into `raw/` and `curated/` |
| `LakeCatalog` | DuckDB file: views over zones, `dataset_meta`, `fetch_log`, `run_log`, `project` schema (plan 02); `rebuild()`, `write_indexes()` |
| `RunLog` | append-only run/step/key events (`meta.run_log`) for monitoring; source of truth for "what happened" (D-022) |
| `FetchLog` | done-keys for resumable downloads, DuckDB table + parquet copy |
| `Compactor` | raw files → yearly curated partitions, schema-checked, manifests |
| `LakeQuery` | the read API: `sql()`, `panel(dataset, start, end, tickers)`, `prices(adjusted=True)` |
| `PitAligner` | ASOF-join fundamentals/events to trading dates on `known_on`, next-day shift |
| `TradingCalendar` | trading-day arithmetic from `trade_cal`: `next()`, `prev()`, `sessions(start,end)`, `is_open()`; used by every layer above |
| `ProjectCatalog` | repo tree / registry / plans as SQL (plan 02) |

### 2.3 `data_loading` (L3) — getting bytes from Tushare
| Class | Purpose |
|---|---|
| `TushareClient` (`BaseApiClient`) | POST, paging, retry, rate-limit sleep, permission errors → `DataSourceError` |
| `SingleCallFetcher` (none), `EnumFetcher` (list_status, ts_code), `DateSweepFetcher` (trade_date, ann_date), `PeriodSweepFetcher` (period), later `MonthWindowFetcher` (month) | one class per **sweep pattern**, not per endpoint; the endpoint comes from `DatasetSpec` (DATA_LOADING_DESIGN §2.2) |
| `FetcherFactory` | `spec.sweep.kind` → fetcher instance; adding a dataset with a known pattern needs no new class |

### 2.4 `pipeline` (L4) — ordered, resumable steps
| Class | Purpose |
|---|---|
| `BaseRunner` → `LocalRunner` (now), `PrefectRunner` (deferred, D-022) | runs `BaseStep`s in dependency order through a pluggable runner; steps never import the runner's backend |
| `KeyExecutor` | iterates a fetcher's keys (serial now, thread pool later, D-015g); the writer is the only sink |
| `DownloadPipeline` | reference → daily sweeps → period sweeps, per `config.download` |
| `CuratePipeline` | compact → derived (adjusted prices, fundamentals PIT) → indexes |
| `UniverseStep` | investable universe per date → `UniversePanel` (listed, not ST, not suspended, ≥ N days since listing, exchange filter); reasons kept per exclusion |
| `FeaturePipeline` | runs configured `BaseFactor`s over `LakeQuery` panels → `FactorPanel` partitions in `curated/derived/features/` |

### 2.5 `statistic` (L4) — computation, no I/O, no plotting
| Class | Purpose |
|---|---|
| `BaseFactor` | declares `inputs` (datasets), `lookback`, `name`; `compute(panels) -> FactorPanel`; value at date T uses only data known by close of T |
| `MomentumFactor`, `VolatilityFactor`, `TurnoverFactor`, `SizeFactor`, `ValueFactor` (pe/pb from `daily_basic`), `QualityFactor` (roe, margins via PIT fundamentals) | first concrete factors, one class each |
| `FactorPreprocessor` | winsorize, z-score, industry/size neutralize; every step optional and logged |
| `FactorEvaluator` | IC / ICIR, quantile returns, long-short, turnover, decay → `FactorReport` frames |
| `ReturnStats` | annualized return/vol, Sharpe, max drawdown, hit rate over an `EquityCurve` |
| `CrossSectionalRegression` | per-date OLS of returns on factors, t-stats, R² |

### 2.6 `portfolio` (L5) — from scores to target weights
| Class | Purpose |
|---|---|
| `BasePortfolioConstructor` | `construct(scores: FactorPanel, universe: UniversePanel, date) -> TargetWeightPanel` |
| `TopNEqualWeight`, `ScoreWeighted`, later `RiskParity`, `MeanVariance` | constructors |
| `ConstraintSet` | max single weight, sector cap, turnover cap, long-only; applied after construction |
| `RebalanceSchedule` | monthly / weekly / N-day via `TradingCalendar` |

### 2.7 `back_testing` (L5) — simulate target weights
| Class | Purpose |
|---|---|
| `BacktestEngine` | daily loop: at open of T+1 trade toward weights decided at close of T; holds cash, positions, NAV |
| `ExecutionModel` | fill price (next open / VWAP), reject when suspended (no bar) or price at `stk_limit` (limit-up buy / limit-down sell), partial fills by volume cap |
| `CostModel` | commission, stamp duty on sells, transfer fee, slippage bps; A-share defaults in `config/backtest.yaml` |
| `BacktestResult` | `EquityCurve`, `TradeLog`, `PositionPanel`; `to_frame()` per component; benchmark from `index_daily` |
| `PerformanceAnalyzer` | metrics vs benchmark using `statistic.ReturnStats`; exposure, turnover, cost drag |

### 2.8 `visualization` (L5) — charts over frames only
| Class | Purpose |
|---|---|
| `BaseChart` | theme tokens, size, `show()`, `to_html()`, `to_png()`; plotly figure inside |
| `PriceChart`, `PanelChart` | candles + volume (adjusted); small multiples |
| `FactorChart` | IC series, ICIR bar, quantile-return ladder, decay |
| `EquityCurveChart` | NAV vs benchmark, drawdown band, rebalance markers |
| `PositionChart` | weight heatmap, sector exposure over time |
| `ReportBuilder` | one HTML report from a list of charts and metric tables |

## 3. Shared frames (`core.frames`, all long/tidy, dates `YYYYMMDD` strings, tickers `ts_code`)

| Schema | Primary key | Columns | Produced by | Consumed by |
|---|---|---|---|---|
| `PRICE_PANEL` | `trade_date, ts_code` | open, high, low, close, pre_close, vol, amount, adj_factor, close_adj | `LakeQuery.prices` | factors, engine, charts |
| `FUNDAMENTALS_PIT` | `trade_date, ts_code, field` | value, end_date, ann_date | `PitAligner` | `QualityFactor`, `ValueFactor` |
| `UNIVERSE_PANEL` | `trade_date, ts_code` | in_universe, reason | `UniverseStep` | constructors, evaluator |
| `FACTOR_PANEL` | `trade_date, ts_code, factor` | value, value_raw | `BaseFactor`, `FactorPreprocessor` | evaluator, constructors |
| `TARGET_WEIGHT_PANEL` | `trade_date, ts_code` | weight | constructors | `BacktestEngine` |
| `TRADE_LOG` | `trade_date, ts_code, side` | qty, price, cost, reason (filled / rejected_limit / rejected_suspended) | engine | analyzer, charts |
| `POSITION_PANEL` | `trade_date, ts_code` | qty, weight, market_value | engine | analyzer, `PositionChart` |
| `EQUITY_CURVE` | `trade_date` | nav, benchmark_nav, cash, exposure, turnover, cost | engine | `ReturnStats`, `EquityCurveChart` |

Rules: long format only (DuckDB- and parquet-friendly); pivot inside a method, never across a boundary.
Every producer validates with `Schema.validate()` before returning; every consumer trusts the schema.

## 4. Design rules that cut across packages
- **Time discipline**: a value dated T is known at close of T. Anything acting on it trades at the open of the next trading day; `ExecutionModel` owns that lag, nobody else re-implements it.
- **Universe is data**: `UniversePanel` is computed once per date and joined; no factor or constructor filters tickers ad hoc.
- **Configuration over code**: factors, constructors, costs and schedules are chosen by name in YAML and resolved through small factories (`FactorFactory`, `ConstructorFactory`) that read the class registry of the package. A new factor = one subclass + one registry row + one YAML line.
- **No I/O in `statistic`, `portfolio`, `back_testing`, `visualization`**: they receive frames and return frames or figures; `pipeline` and `research_space` do the reading and writing through `LakeQuery`/`ParquetWriter`.
- **Fakes, not mocks**: tests use `FakeTushareClient`, a mini lake in `tmp_path`, and a synthetic `PRICE_PANEL` generator (`core.testing.SyntheticMarket`) with known answers (e.g. a deterministic momentum leader).

## 5. Roadmap of plans

| Plan | Builds | Depends on | Status |
|---|---|---|---|
| 00 | model roles (agent, hook, settings) | — | drafted |
| 01 | `core`, `lake`, `data_loading`, `DownloadPipeline`, `CuratePipeline`, `PitAligner`, `BaseChart`/`PriceChart`, `main.ipynb` | 00 | approved |
| 02 | `ProjectCatalog` (project schema in DuckDB) | 01 ph3 | drafted |
| 03 | `TradingCalendar`, `UniverseStep`, `BaseFactor` + six factors, `FactorPreprocessor`, `FactorEvaluator`, `FeaturePipeline`, `FactorChart` | 01 | to draft |
| 04 | `portfolio` (constructors, constraints, schedule), `back_testing` (engine, execution, costs, result, analyzer), `EquityCurveChart`, `PositionChart`, `ReportBuilder` | 03 | to draft |
| 05 | events datasets (forecast, express, holdertrade, share_float) + event factors | 01, 03 | to draft |
| 06 | walk-forward / parameter search, multi-strategy portfolios | 04 | to draft |

## 6. Open questions
1. Backtest granularity: daily bars only (recommended for plan 04) or design `ExecutionModel` for intraday from the start?
2. Industry classification for neutralization: Shenwan (`index_classify`, needs extra endpoint in plan 05) or `stock_basic.industry` (free, coarser)? Recommendation: start with `stock_basic.industry`, upgrade in plan 05.
3. Should `portfolio` consume raw `FactorPanel` or a combined `ScorePanel` produced by a `SignalCombiner` in `statistic`? Recommendation: add `SignalCombiner` (weighted sum of z-scored factors) to plan 03.
