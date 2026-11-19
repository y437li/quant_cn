# 03 — Calculation package: CBOE-method VIX from A-share option data

| | |
|---|---|
| Status | doing — phases 2–3 done (dda0409); phase 1 leftovers and phase 4 open; phase 5 todo; phase 6 doing (daily monitor) |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-032, D-046, D-047, D-048, D-049, D-050, D-051, D-052, D-152 |
| Depends on plans | 01 (phases 1–5) |

## Goal
A daily 30-day volatility index for one or more A-share option underlyings, computed by the CBOE method from
lake data, stored as a derived dataset, and validated against the exchange's historical iVIX.

## Scope
- In: `calculation` package (§1 of CALCULATION_DESIGN), three new datasets (`opt_basic`, `opt_daily`, `shibor`), `DateWindowFetcher`, `pipeline.CalculationStep`, `VIX_PANEL` schema, replication notebook, `SeriesChart`.
- Out: implied-vol surfaces, greeks, other indices (later calculators), intraday.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Option and rate data | `datasets.yaml` entries for `opt_basic`, `opt_daily`, `shibor`; `DateWindowFetcher`; `EnumFetcher` sweep by `exchange`; curated schemas | dry run lists keys; live pull of 2026-08 `opt_daily` (SSE) + `opt_basic` + 2026 `shibor` lands; `make check` green | 01 ph4 | doing: datasets + live pulls done; `DateWindowFetcher` and curated schemas open |
| 2 | Building blocks | `BaseCalculation`, `RiskFreeCurve`, `OptionChainBuilder`, `TermSelector` | white-paper and synthetic TCs pass; contracts, registry blocks, indexes | 1 | done |
| 3 | Core formulas | `ForwardPriceEstimator`, `VarianceStripCalculator`, `TermInterpolator` | CBOE worked example reproduced: `F`, `K0`, `σ²` (1e-6), VIX 13.69 | 2 | done (known answers: Black-76 flat-vol chains, not the white-paper 13.69 example — see Log) |
| 4 | Calculator + step | `VixCalculator`, `CalculationFactory`, `config/calculations.yaml`, `pipeline.CalculationStep`, `VIX_PANEL` in `core.frames`, `derived/vix/` partitions | end-to-end on the Aug-2026 sample writes a row per trading day with `quality_flag`; `make lake-rebuild` byte-identical | 3 | doing: `VixCalculator` + `VIX_PANEL` done; `CalculationFactory`, `CalculationStep`, `derived/vix/` open |
| 6 | Daily volatility monitor | dataset `cboe_vix` (`CboeClient`, source `cboe`); `opt_daily` from 20250101; `VolatilityMonitorSettings` + `config/volatility_monitor.yaml`; `VolatilityMonitorBuilder` → `volatility_monitor.json`; `VolatilityReportSection` in the 持仓监测 e-mail; Go `/api/volatility`, React `#volatility` (波动率监测); `make volatility-monitor` in track-daily | real lake run writes US VIX + 5 A-share lines with 1-year percentiles; alerts US VIX ≥ 25 or +30% in a day, 300 / 科创50 ≥ 1-year 90th pct; `make check` + `make app-check` green | 4 (`VixCalculator`) | doing |
| 5 | Validation | backfill `opt_daily`/`shibor` 2015-02 → 2018-02 for `510050.SH`; notebook `YYYYMMDD_vix_replication.ipynb`; `visualization.SeriesChart` | mean `\|ours − iVIX\|` ≤ 0.5 vol pts over the overlap; deviations explained by `quality_flag`; notebook runs top to bottom | 4 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `DateWindowFetcher` | new (subclass `BaseFetcher`) | data_loading | 1 | `FetcherFactory`; later `share_float` (plan 06) |
| `BaseCalculation` | new | calculation | 2 | `VixCalculator`, `CalculationFactory`, `pipeline.CalculationStep` |
| `RiskFreeCurve` | new | calculation | 2 | `VixCalculator`; later IV/greeks calculators |
| `OptionChainBuilder` | new | calculation | 2 | `VixCalculator`; later IV surface |
| `TermSelector` | new | calculation | 2 | `VixCalculator` |
| `ForwardPriceEstimator`, `VarianceStripCalculator`, `TermInterpolator` | new | calculation | 3 | `VixCalculator` |
| `VixCalculator` | new | calculation | 4 | `CalculationStep`; notebook |
| `CalculationFactory` | new | calculation | 4 | `CalculationStep` |
| `CalculationStep` | new (subclass `BaseStep`) | pipeline | 4 | `CuratePipeline.stage_calculations`, `cli compact` |
| `VIX_PANEL` | new schema | core.frames | 4 | `VixCalculator` (produce), `SeriesChart`, notebook (consume) |
| `CboeClient` | new (subclass `BaseWebClient`) | data_loading | 6 | `cli.ServiceBuilder` (source `cboe`) |
| `VolatilityLine`, `VolatilityMonitorSettings` | new | core | 6 | `VolatilityMonitorBuilder`, `cli.ReportCommands` |
| `VolatilityMonitorBuilder` | new | calculation | 6 | `cli.ReportCommands` |
| `VolatilityReportSection` | new (subclass `ReportSection`) | visualization | 6 | `MonitorReportRenderer` via `cli.ReportCommands` |
| `SeriesChart` | new (subclass `BaseChart`) | visualization | 5 | notebook; later `EquityCurveChart` reuse |

## Risks
- No bid/ask in `opt_daily`: closes replace midpoints; the acceptance threshold (0.5 vol pts) may need loosening on illiquid days. `quality_flag` makes this visible.
- `opt_daily` permission tier: verify in phase 1 before building on it; `PermissionDeniedError` marks it blocked.
- Dividend-adjusted contracts ("A" suffix) create off-grid strikes; excluded by default, which thins the strip on affected months.
- Backfill size: ~3 years × ~250 days × ~100–300 contracts per underlying, small; SHIBOR daily, tiny.
- iVIX reference series must be obtained (SSE published 2015-02 to 2018-02); if unavailable, validate against a broker-published proxy and lower the criterion to "shape and level agree", recorded as a decision.

## Open items (2026-09-27)
- Phase 1 leftovers: `DateWindowFetcher` (shibor currently one range call), curated schemas for the four option/rate datasets, adding them to `download.order`.
- ~~index_daily follow-up~~ done: D-049, download refuses a `--start` later than the configured start for overwrite + range datasets.
- White-paper worked example (VIX 13.69) not in the repo; phase 3 accepted Black-76 flat-volatility known answers instead. To close the original criterion, type the white-paper tables into `tests/calculation/fixtures/` (small, one-off).
- Prototype notebook checks outside their pre-set bands (listed in the notebook, not widened): forward/spot below 0.99 on 7 rows (CSI500 / STAR ETFs, futures-basis discount); VIX − ATM IV outside [−2, +5] on 5 STAR50 ETF skew days. Phases 2–4 must reproduce these numbers before they change any rule.

- Phase 6 gap (2026-11-13): include dividend-adjusted ETF contracts with their pre-ex-date strike (strike × per_unit / 10000) before the ETF's ex-date and the adjusted strike after; needs the ETF ex-dates (Tushare `fund_div`). Until then those sessions are `failed` rows and drop out of the percentile.

## Open questions
None. CALCULATION_DESIGN §6 closed with the recommendations: default underlying `510050.SH` with `510300.SH` also configured; one `VIX_PANEL` table with an `underlying` column; acceptance mean |ours − iVIX| ≤ 0.5 vol points.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-13 | 6 | Real run after the `opt_daily` backfill (20250102–20261113, 451 days, 8.14M rows; compacted 9.96M): 26 s, 6 lines, no alerts. US VIX 18.7 (73rd pct); 50ETF 14.1 (4th), 300ETF 17.6 (21st), 500ETF 29.3 (78th), 中证1000 29.7 (81st), 科创50 48.3 (85th). Gaps: 50ETF 17 / 300ETF 25 / 500ETF 49 of 250 sessions fail with one usable expiry, all around ETF dividends (2025-11/12, 500ETF also 2026-06): `opt_basic` carries the *current* name and strike, so contracts later dividend-adjusted ("…A", unit 10,260) are excluded on every date, including before the ex-date. 科创50 and 中证1000 complete. App rebuilt and restarted; smoke `volatility: 6 cards · ok` (390 px no overflow) |
| 2026-11-13 | 6 | Built (user: "vix也需要监测" → "可以，按这个做"; D-152): `CboeClient` + dataset `cboe_vix` (9,315 days since 1990, last 20261112 = 18.70); `VolatilityMonitorSettings`, `VolatilityMonitorBuilder` (TC-VMB-001..006; computes the A-share VIX on the fly with `VixCalculator` instead of waiting for phase 4's `derived/vix/` partitions), `VolatilityReportSection` (TC-VRS-001..002), CLI `volatility-monitor` (TC-RPC-005), Go `GetVolatilityMonitor` + `/api/volatility` (TC-ST-025..026, TC-API-014), React `features/volatility` (TC-VOF-001..003) with sidebar item 波动率监测; `opt_daily` start moved to 20250101 and backfill running. The shared ph7 files (report_commands, morning_report_builder, Makefile, handlers.go, store.go, app-route, app.tsx) are edited but left for plan 15's ph7 commit (peer quant-cn-b9) |
| 2026-11-13 | 6 | Added and approved (user: "可以，按这个做"). First read 11-13: US VIX 18.7 (1-year 70th pct; 28.2 on 11-05); 50ETF 14.1 (lowest since Aug), 300ETF 17.6, 500ETF 29.3, 中证1000 29.7, 科创50 48.3 |
| 2026-09-27 | 2–3 | `calculation` package (9 classes, 29 tests) + `VixCalculator` + `VIX_PANEL` (dda0409, quant-cn-b7). Notebook now imports the package only and reproduces the prototype numbers exactly; committed WITH outputs at the user's request (D-051, exception to D-040). Known answers: Black-76 flat-vol chains (white-paper 13.69 example not reproduced; tables not in repo) |
| 2026-09-27 | 2–3 | Finding: the CSI 300 VIX drop on 20260917 is a calendar-clock artifact: the near term rolled onto an expiry spanning the Mid-Autumn and National Day holidays. `ExpiryClock` gains a trading-session mode (21 sessions / 244-session year) alongside the white-paper calendar mode; on the trading clock the 300 VIX stays ≈ 18 (D-052) |
| 2026-09-27 | 1 | D-049: `download` refuses `--start` later than the configured start for overwrite + range datasets. D-050: `DatasetSpec.extend_days`, `trade_cal` fetched +400 days ahead for expiry and next-day maths |
| 2026-09-27 | 1 | Prototype ahead of the package (user to quant-cn-b7: "do the vix calculation in a jupyter notebook", "use 300", "calculate all of them", "most recent vix for the 300"): `research_space/notebooks/20260927_vix_calculation.ipynb` computes CBOE-method VIX for 12 underlyings (5 SSE ETFs, 4 SZSE ETFs, CFFEX IH/IO/IM), 20260803–20260924, 468/468 underlying-days. Latest (20260924) 300 family: CFFEX IO 17.28, SZSE 159919 17.05, SSE 510300 16.96. Synthetic flat-20% BS chain → 20.14; VIX/realised 0.85–1.17 (4add2d4) |
| 2026-09-27 | 1 | Data: `opt_basic` (new sweep kind `exchange`: SSE/SZSE/CFFEX), `opt_daily` (by trade_date, all exchanges, ~24k rows/day), `shibor` (single range call), `fund_daily` (ETF closes, `option_etfs` enum) configured; live pulls: opt_basic 31,002; opt_daily 1,005,216 rows / 39 days; shibor 183; fund_daily 1,602. Not in `download.order`. `make check` green: 191 passed, lint 0, stale 0 |
| 2026-09-27 | 1 | Incident: `index_daily --start 20260101` overwrote its raw history (refresh = overwrite); restored at once with a default-range refetch (28,350 rows since 2010). Follow-up recorded in Open items |
| 2026-09-27 | — | Approved by user ("approve"); recommendations for §6 adopted |
| 2026-09-27 | — | Drafted from user request: calculation package, first function CBOE-method VIX from option data |
