# 03 — Calculation package: CBOE-method VIX from A-share option data

| | |
|---|---|
| Status | approved 2026-09-27, not started (after plan 02) |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-032 |
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
| 1 | Option and rate data | `datasets.yaml` entries for `opt_basic`, `opt_daily`, `shibor`; `DateWindowFetcher`; `EnumFetcher` sweep by `exchange`; curated schemas | dry run lists keys; live pull of 2026-08 `opt_daily` (SSE) + `opt_basic` + 2026 `shibor` lands; `make check` green | 01 ph4 | todo |
| 2 | Building blocks | `BaseCalculation`, `RiskFreeCurve`, `OptionChainBuilder`, `TermSelector` | white-paper and synthetic TCs pass; contracts, registry blocks, indexes | 1 | todo |
| 3 | Core formulas | `ForwardPriceEstimator`, `VarianceStripCalculator`, `TermInterpolator` | CBOE worked example reproduced: `F`, `K0`, `σ²` (1e-6), VIX 13.69 | 2 | todo |
| 4 | Calculator + step | `VixCalculator`, `CalculationFactory`, `config/calculations.yaml`, `pipeline.CalculationStep`, `VIX_PANEL` in `core.frames`, `derived/vix/` partitions | end-to-end on the Aug-2026 sample writes a row per trading day with `quality_flag`; `make lake-rebuild` byte-identical | 3 | todo |
| 5 | Validation | backfill `opt_daily`/`shibor` 2015-02 → 2018-02 for `510050.SH`; notebook `YYYYMMDD_vix_replication.ipynb`; `visualization.SeriesChart` | mean |ours − iVIX| ≤ 0.5 vol pts over the overlap; deviations explained by `quality_flag`; notebook runs top to bottom | 4 | todo |

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
| `SeriesChart` | new (subclass `BaseChart`) | visualization | 5 | notebook; later `EquityCurveChart` reuse |

## Risks
- No bid/ask in `opt_daily`: closes replace midpoints; the acceptance threshold (0.5 vol pts) may need loosening on illiquid days. `quality_flag` makes this visible.
- `opt_daily` permission tier: verify in phase 1 before building on it; `PermissionDeniedError` marks it blocked.
- Dividend-adjusted contracts ("A" suffix) create off-grid strikes; excluded by default, which thins the strip on affected months.
- Backfill size: ~3 years × ~250 days × ~100–300 contracts per underlying, small; SHIBOR daily, tiny.
- iVIX reference series must be obtained (SSE published 2015-02 to 2018-02); if unavailable, validate against a broker-published proxy and lower the criterion to "shape and level agree", recorded as a decision.

## Open questions
None. CALCULATION_DESIGN §6 closed with the recommendations: default underlying `510050.SH` with `510300.SH` also configured; one `VIX_PANEL` table with an `underlying` column; acceptance mean |ours − iVIX| ≤ 0.5 vol points.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-27 | — | Approved by user ("approve"); recommendations for §6 adopted |
| 2026-09-27 | — | Drafted from user request: calculation package, first function CBOE-method VIX from option data |
