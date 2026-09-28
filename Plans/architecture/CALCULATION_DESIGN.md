# Calculation Package Design (v1.0, approved 2026-09-27; decision D-032 accepted)

`src/quant_cn/calculation/` (L4, beside `statistic`) holds **domain financial computations** that turn lake
panels into derived market series: volatility indices, implied volatilities, term structures, greeks.
`statistic` stays generic math; `calculation` knows what an option, a forward and a risk-free curve are.
Neither imports the other. First deliverable: a CBOE-method volatility index from A-share option data.

## 1. Package shape
| Class | Module | Purpose |
|---|---|---|
| `BaseCalculation` | `base_calculation.py` | declares `name`, `inputs` (dataset names), `output_schema`; `compute(panels: dict[str, DataFrame]) -> DataFrame`; pure, no I/O |
| `RiskFreeCurve` | `risk_free_curve.py` | per date, interpolate a continuously-compounded rate for any tenor in days from `shibor` tenors (ON, 1W, 2W, 1M, 3M, 6M, 9M, 1Y) |
| `OptionChainBuilder` | `option_chain_builder.py` | join `opt_basic` + `opt_daily` → one tidy chain: `trade_date, underlying, maturity_date, days_to_expiry, strike, call_put, price, volume, oi` |
| `TermSelector` | `term_selector.py` | per date, pick near- and next-term expiries around the 30-day target (CBOE rule; ≥ 7 days to expiry for near term) |
| `ForwardPriceEstimator` | `forward_price_estimator.py` | per expiry: `F = K* + e^{RT}(C − P)` at the strike with the smallest |C − P|; `K0` = largest strike ≤ F |
| `VarianceStripCalculator` | `variance_strip_calculator.py` | per expiry: OTM strip (puts < K0, calls > K0, both at K0 averaged), stop after two consecutive zero prices, `σ² = (2/T) Σ (ΔK/K²) e^{RT} Q(K) − (1/T)(F/K0 − 1)²` |
| `TermInterpolator` | `term_interpolator.py` | weight the two variances to a constant 30 days using minutes (`N_T1`, `N_T2`, `N_30`, `N_365`), `VIX = 100 √(...)` |
| `VixCalculator` (`BaseCalculation`) | `vix_calculator.py` | orchestrates the six steps for one underlying over a date range → `VIX_PANEL` |
| `CalculationFactory` | `calculation_factory.py` | name → instance from YAML (`config/calculations.yaml`) |

Folder: `calculation/INDEX.md`, one module per class, `tests/calculation/` mirroring.

## 2. Method (CBOE VIX white paper, 2019 revision) as applied here
1. **Universe**: options on one configurable underlying (default `510050.SH`, the 50ETF, listed 2015; alternatives `510300.SH`, `159919.SZ`, CFFEX `000300.SH` index options). Standard monthly expiries only; weeklies excluded unless present in `opt_basic`.
2. **Rates**: `RiskFreeCurve` from `shibor` on the same `trade_date`, tenor interpolated to each expiry's days; converted to continuous compounding.
3. **Terms**: `TermSelector` returns (near, next) with `7 ≤ days_near`, `days_near ≤ 30 < days_next` when available; otherwise the two nearest expiries with ≥ 7 days.
4. **Forward and K0** per term, **variance strip** per term, **interpolation** to 30 days: exactly the CBOE formulas; time to expiry in minutes to the 15:00 close.
5. **Output** `VIX_PANEL` (schema in `core.frames`): `trade_date, underlying, vix, var_near, var_next, days_near, days_next, f_near, f_next, k0_near, k0_next, n_options_near, n_options_next, rate_near, rate_next, quality_flag`.

### Data limits and the choices they force
| CBOE input | Tushare field available | Choice (configurable) |
|---|---|---|
| bid/ask midpoint | `opt_daily` has `close`, `settle`, `vol`, `oi`; **no bid/ask** | `price_field: close` (fallback `settle` when `close` is 0/NaN); documented deviation from the white paper |
| "two consecutive zero bids" cut-off | no bids | two consecutive strikes with `price == 0` **or** `vol == 0`, `zero_rule: price_or_volume` |
| minutes to expiry | `maturity_date` only | expiry at 15:00 on `maturity_date`; observation at 15:00 close |
| US T-bill rates | `shibor` | SHIBOR (what the exchange's own iVIX used); alternative `yc_cb` deferred |
| strike step ΔK | irregular after adjustments (dividend-adjusted strikes on ETF options create off-grid strikes) | ΔK computed from neighbours per the white paper; adjusted contracts (`opt_basic.name` suffix "A") **excluded by default**, flag to include |

Every deviation is recorded in `quality_flag` per row so downstream users see when the number is not
white-paper-exact (e.g. `used_settle`, `single_term`, `adjusted_excluded`).

## 3. Data to add (`config/datasets.yaml`, plan 03 phase 1)
| Dataset | Endpoint | Sweep | Primary key | Known on | Notes |
|---|---|---|---|---|---|
| `opt_basic` | `opt_basic` | `exchange` ∈ {SSE, SZSE, CFFEX} | `ts_code` | `list_date` | contract master: `exercise_price`, `maturity_date`, `call_put`, `opt_code`, `name`, `per_unit`, `list_date`, `delist_date` |
| `opt_daily` | `opt_daily` | `trade_date` (+ `exchange`) | `ts_code, trade_date` | `trade_date` | `open, high, low, close, settle, pre_settle, vol, amount, oi` |
| `shibor` | `shibor` | `start_date/end_date` window (year) | `date` | `date` | `on, 1w, 2w, 1m, 3m, 6m, 9m, 1y` in percent |

Sweep kinds `exchange` and `date_window` are new `DatasetSpec.sweep.kind`s: `EnumFetcher` already covers
`exchange`; `date_window` becomes `DateWindowFetcher` (also reusable by `share_float` in plan 06).

## 4. Where it runs
- `pipeline.CalculationStep` (L6) runs a configured `BaseCalculation` over `LakeQuery` panels and writes
  `curated/derived/<name>/year=YYYY/` (e.g. `derived/vix_510050/`). `CuratePipeline` gains a `calculations` stage.
- `research_space/notebooks/YYYYMMDD_vix_replication.ipynb` compares our series against the exchange-published
  iVIX for the overlap period (2015-02 to 2018-02) as the acceptance check.
- `visualization.SeriesChart` (line with events) plots it; `FactorChart` unaffected.

## 5. Tests
| Class | Cases |
|---|---|
| `RiskFreeCurve` | exact tenor hit; interpolation between tenors; extrapolation clamps; percent → continuous conversion |
| `OptionChainBuilder` | join drops contracts without a master row; days_to_expiry from `DateCodec`; adjusted contracts excluded/included by flag |
| `TermSelector` | picks near/next around 30 days; near ≥ 7 days; single-expiry fallback sets `single_term` |
| `ForwardPriceEstimator` | white-paper worked example reproduces `F` and `K0` exactly |
| `VarianceStripCalculator` | white-paper worked example reproduces `σ²` to 1e-6; zero-price cut-off; ΔK at edges |
| `TermInterpolator` | white-paper example reproduces the published VIX (13.69 in the 2019 paper's example) |
| `VixCalculator` | end-to-end on a synthetic chain with known answer; missing rate → `SchemaError`; empty date → no row |
Known-answer fixtures come from the CBOE white paper tables, typed into `tests/calculation/fixtures/`.

## 6. Open questions
None. Closed 2026-09-27 (user approved the recommendations): default underlying `510050.SH`, `510300.SH` also configured; one `VIX_PANEL` table with an `underlying` column; acceptance threshold mean |ours − iVIX| ≤ 0.5 vol points over the 2015-02 → 2018-02 overlap.
