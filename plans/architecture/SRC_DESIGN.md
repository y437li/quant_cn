# `src/quant_cn` Design (v1.2, 2026-09-27; D-020, D-028, D-032, D-041 read API)

How the ten packages fit together, what each owns, where the extension points are, and the shared
frames that let independent packages talk without importing each other. Plan-level detail lives in
`plans/execution/`; this document is the map.

## 1. Data flow

```
Tushare ──► data_loading ──► lake.raw ──► lake.curated / derived ──► LakeQuery (SQL, PIT-safe)
                                                                          │
              pipeline.FeaturePipeline ◄── factor.BaseFactor ◄── statistic ─┤  PricePanel, FundamentalsPIT
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
package boundary except `core` types. `cli` (L6) is the composition root that assembles concrete classes.

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

### 2.2b Lake read API — the loading engine (D-041)
`LakeQuery` is the only way code above the lake reads data. Built today: `sql`, `has_view`, `read_prices`.
Completed to this surface in plan 04 phase 1 (factors and the universe step are its first consumers):

| Method | Purpose | Output |
|---|---|---|
| `sql(query, params)` | any read against catalog views | DataFrame |
| `read_panel(dataset, start, end, tickers=None, columns=None)` | one curated dataset as a long panel, PK-sorted | DataFrame in the dataset's curated schema |
| `read_prices(start, end, tickers=None, adjusted=True, dense=False)` | prices; `dense=True` reindexes to `TradingCalendar` sessions with suspended days as NaN rows (closes the phase-5 deferral) | `PRICE_PANEL` |
| `read_fundamentals_pit(fields, start, end, tickers=None)` | PIT-aligned fundamentals via `PitAligner` | `FUNDAMENTALS_PIT` |
| `read_reference(name)` | `stock_basic`, `namechange`, `trade_cal`, `index_daily` as frames | curated schema |
| `read_universe(start, end)` | the `UniversePanel` once `UniverseStep` exists | `UNIVERSE_PANEL` |
| `register_frame(name, frame)` | expose a notebook/in-memory frame as a DuckDB view for joins | view name |
| `list_views()` / `has_view(name)` | discovery | list[str] / bool |

`PanelCache` (lake): optional in-memory Arrow cache keyed by (method, args) with a size cap, injected into
`LakeQuery`; on by default in notebooks, off in pipelines. All methods validate their output with the
frame's `Schema` before returning. Names follow the verb table (`read_`, `list_`, `register_`).

### 2.3 `data_loading` (L3) — getting bytes from Tushare
| Class | Purpose |
|---|---|
| `TushareClient` (`BaseApiClient`) | POST, paging, retry, rate-limit sleep, permission errors → `DataSourceError` |
| `SingleCallFetcher` (none), `EnumFetcher` (list_status, ts_code), `DateSweepFetcher` (trade_date, ann_date), `PeriodSweepFetcher` (period), later `MonthWindowFetcher` (month) | one class per **sweep pattern**, not per endpoint; the endpoint comes from `DatasetSpec` (DATA_LOADING_DESIGN §2.2) |
| `FetcherFactory` | `spec.sweep.kind` → fetcher instance; adding a dataset with a known pattern needs no new class |

### 2.4 `statistic` (L4) — generic math on frames, no I/O, no factor knowledge
| Class | Purpose |
|---|---|
| `Winsorizer`, `Standardizer` (z-score, rank) | cross-sectional per-date transforms on a long panel |
| `Neutralizer` | residualise a value column against industry dummies / size per date |
| `ICCalculator` | Spearman/Pearson IC per date between any value column and forward returns |
| `QuantileReturns` | per-date quantile buckets of a value column and their forward returns |
| `ReturnStats` | annualized return/vol, Sharpe, max drawdown, hit rate over an `EquityCurve` |
| `CrossSectionalRegression` | per-date OLS of returns on columns, t-stats, R² |

### 2.4b `calculation` (L4) — domain financial computations (D-032, `CALCULATION_DESIGN.md`)
| Class | Purpose |
|---|---|
| `BaseCalculation` | `name`, `inputs`, `output_schema`; `compute(panels) -> DataFrame`; pure |
| `RiskFreeCurve`, `OptionChainBuilder`, `TermSelector`, `ForwardPriceEstimator`, `VarianceStripCalculator`, `TermInterpolator` | CBOE VIX building blocks, one module each |
| `VixCalculator` | 30-day volatility index per underlying → `VIX_PANEL` |
| `CalculationFactory` | name → instance from `config/calculations.yaml` |
Later: implied-vol surface, greeks, term-structure calculators. `calculation` and `statistic` never import each other; `factor` may use both (e.g. a VIX-regime factor).

### 2.5 `factor` (L5) — factor definitions and factor research (D-028)
| Class | Purpose |
|---|---|
| `BaseFactor` | declares `name`, `inputs` (datasets), `lookback`; `compute(panels) -> FactorPanel`; value at date T uses only data known by close of T |
| `MomentumFactor`, `VolatilityFactor`, `TurnoverFactor`, `SizeFactor`, `ValueFactor` (pe/pb from `daily_basic`), `QualityFactor` (roe, margins via PIT fundamentals) | first concrete factors, one module each under `factor/library/` |
| `FactorPreprocessor` | ordered chain of `statistic` transforms (winsorize → standardize → neutralize), each step optional and logged |
| `FactorEvaluator` | IC / ICIR, quantile ladder, long-short, turnover, decay via `statistic` → `FactorReport` frames |
| `SignalCombiner` | weighted sum of z-scored factors → one score column (`FactorPanel` with `factor == "score"`) |
| `FactorFactory` | resolves factor names from YAML to instances (reads the package's registered classes) |

Folder shape: `factor/base_factor.py`, `factor/factor_preprocessor.py`, `factor/factor_evaluator.py`,
`factor/signal_combiner.py`, `factor/factor_factory.py`, `factor/library/<name>_factor.py` (one class each),
`factor/library/INDEX.md`. Adding a factor = one module in `library/` + registry block + one YAML line.

### 2.6 `pipeline` (L6) — ordered, resumable steps
| Class | Purpose |
|---|---|
| `BaseRunner` → `LocalRunner` (now), `PrefectRunner` (deferred, D-022) | runs `BaseStep`s in dependency order through a pluggable runner; steps never import the runner's backend |
| `DownloadPipeline` | reference → daily sweeps → period sweeps, per `config.download` |
| `CuratePipeline` | compact → derived (adjusted prices, fundamentals PIT) → indexes |
| `UniverseStep` | investable universe per date → `UniversePanel` (listed, not ST, not suspended, ≥ N days since listing, exchange filter); reasons kept per exclusion |
| `FeaturePipeline` | runs configured `factor.BaseFactor`s over `LakeQuery` panels → `FactorPanel` partitions in `curated/derived/features/` |
| `CalculationStep` | runs a configured `calculation.BaseCalculation` → `curated/derived/<name>/` (plan 03) |

### 2.7 `portfolio` (L7) — from scores to target weights
| Class | Purpose |
|---|---|
| `BasePortfolioConstructor` | `construct(scores: FactorPanel, universe: UniversePanel, date) -> TargetWeightPanel` |
| `TopNEqualWeight`, `ScoreWeighted`, later `RiskParity`, `MeanVariance` | constructors |
| `ConstraintSet` | max single weight, sector cap, turnover cap, long-only; applied after construction |
| `RebalanceSchedule` | monthly / weekly / N-day via `TradingCalendar` |

### 2.8 `back_testing` (L7) — simulate target weights
| Class | Purpose |
|---|---|
| `BacktestEngine` | daily loop: at open of T+1 trade toward weights decided at close of T; holds cash, positions, NAV |
| `ExecutionModel` | fill price (next open / VWAP), reject when suspended (no bar) or price at `stk_limit` (limit-up buy / limit-down sell), partial fills by volume cap |
| `CostModel` | commission, stamp duty on sells, transfer fee, slippage bps; A-share defaults in `config/backtest.yaml` |
| `BacktestResult` | `EquityCurve`, `TradeLog`, `PositionPanel`; `to_frame()` per component; benchmark from `index_daily` |
| `PerformanceAnalyzer` | metrics vs benchmark using `statistic.ReturnStats`; exposure, turnover, cost drag |

### 2.9 `visualization` (L7) — charts over frames only
| Class | Purpose |
|---|---|
| `BaseChart` | theme tokens, size, `show()`, `to_html()`, `to_png()`; plotly figure inside |
| `PriceChart`, `PanelChart` | candles + volume (adjusted); small multiples |
| `FactorChart` | IC series, ICIR bar, quantile-return ladder, decay |
| `EquityCurveChart` | NAV vs benchmark, drawdown band, rebalance markers |
| `PositionChart` | weight heatmap, sector exposure over time |
| `ReportBuilder` | one HTML report from a list of charts and metric tables |

### 2.10 `cli` (L8) — composition root
| Class | Purpose |
|---|---|
| `Cli` (`src/quant_cn/cli.py`) | wires `Config` and concrete classes together and exposes `doctor`, `download`, `compact`, `rebuild`, `backup` sub-commands; the only place concrete classes are instantiated together; top import-linter layer, imports anything, imported by nothing |

## 3. Shared frames (`core.frames`, all long/tidy, dates `YYYYMMDD` strings, tickers `ts_code`)

| Schema | Primary key | Columns | Produced by | Consumed by |
|---|---|---|---|---|
| `PRICE_PANEL` | `trade_date, ts_code` | open, high, low, close, pre_close, vol, amount, adj_factor, close_adj | `LakeQuery.prices` | factors, engine, charts |
| `FUNDAMENTALS_PIT` | `trade_date, ts_code, field` | value, end_date, ann_date | `PitAligner` | `QualityFactor`, `ValueFactor` |
| `UNIVERSE_PANEL` | `trade_date, ts_code` | in_universe, reason | `UniverseStep` | constructors, evaluator |
| `FACTOR_PANEL` | `trade_date, ts_code, factor` | value, value_raw | `factor.BaseFactor`, `factor.FactorPreprocessor`, `factor.SignalCombiner` | evaluator, constructors |
| `TARGET_WEIGHT_PANEL` | `trade_date, ts_code` | weight | constructors | `BacktestEngine` |
| `TRADE_LOG` | `trade_date, ts_code, side` | qty, price, cost, reason (filled / rejected_limit / rejected_suspended) | engine | analyzer, charts |
| `POSITION_PANEL` | `trade_date, ts_code` | qty, weight, market_value | engine | analyzer, `PositionChart` |
| `EQUITY_CURVE` | `trade_date` | nav, benchmark_nav, cash, exposure, turnover, cost | engine | `ReturnStats`, `EquityCurveChart` |
| `VIX_PANEL` | `trade_date, underlying` | vix, var_near, var_next, days_near/next, f_near/next, k0_near/next, n_options_near/next, rate_near/next, quality_flag | `VixCalculator` | `SeriesChart`, regime factors, notebooks |

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
| 03 | `calculation` package: CBOE-method VIX (`opt_basic`, `opt_daily`, `shibor` datasets, `DateWindowFetcher`, `CalculationStep`, `SeriesChart`, iVIX replication) | 01 | drafted |
| 04 | `statistic` primitives, `factor` package (`BaseFactor` + six factors in `library/`, `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner`, `FactorFactory`), `UniverseStep`, `FeaturePipeline`, `FactorChart` | 01 | to draft |
| 05 | `portfolio` (constructors, constraints, schedule), `back_testing` (engine, execution, costs, result, analyzer), `EquityCurveChart`, `PositionChart`, `ReportBuilder` | 04 | to draft |
| 06 | events datasets (forecast, express, holdertrade, share_float) + event factors; Shenwan industries | 01, 04 | to draft |
| 07 | walk-forward / parameter search, multi-strategy portfolios; `PrefectRunner` | 05 | to draft |

## 6. Open questions
None. Closed 2026-09-27 with the recommended defaults (user: "approve"):
- Backtests are daily-bar only in plan 04; `ExecutionModel` is the single seam if intraday is added later.
- Industry neutralization starts with `stock_basic.industry`; Shenwan classification arrives with plan 05.
- `SignalCombiner` in `factor` produces the score consumed by `portfolio` (already in §2.5).
