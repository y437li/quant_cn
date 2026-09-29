# 04 — Factors: read API, statistic tests, universe, factor library, evaluation

| | |
|---|---|
| Status | approved 2026-09-28 (user: "once you finish the planning assign to the other session to execute"); handed to quant-cn-b7 |
| Owner | user / executor quant-cn-b7 (build) / quant-cn-a1 (record) |
| Created | 2026-09-28 |
| Notion | pending |
| Decisions | D-041, D-053, D-054, D-055, D-060 |
| Depends on plans | 01, 02 (done); 03 phases 2–3 (done, `VIX_PANEL` regime for conditioning) |

## Goal
Six factors from FACTOR_LIBRARY §8, computed point-in-time over the full lake, each with a significance report
that meets FACTOR_TESTING_DESIGN §6, produced by a `FeaturePipeline` step and browsable in a notebook; the
read API, universe and statistic test classes every later plan reuses.

## Scope
- In: `LakeQuery` read API + `PanelCache` + ticker alias map (D-041, D-053); `statistic` primitives and the core test set (FACTOR_TESTING_DESIGN §5, first group); `UniverseStep`; `factor` package with six library factors; `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner`, `FactorFactory`; `FeaturePipeline`; `FactorChart`; evaluation notebook; two statement fields added to `datasets.yaml` and refetched.
- Out: risk-model exposures (plan 05), backtest-level tests (`DeflatedSharpe`, `BacktestOverfitting`, `SharpeRatioTest` → plan 06), analyst factors (plan 07), remaining catalogue factors (later campaigns).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Read API + alias map | `LakeQuery.read_panel / read_prices(dense=) / read_fundamentals_pit / read_reference / list_views / register_frame`, `PanelCache`, `TickerAliasMap` (old→new code from `stock_basic` + `namechange` + the three known pairs, applied in `prices_adj`), `frames` for `UNIVERSE_PANEL`, `FACTOR_PANEL`, `IC_SERIES`, `IC_TEST`, `TRIAL_LOG` | every method schema-validated; dense prices reindex to sessions; alias map restores the 3 double-listed histories (TC); cache hit/miss test | — | todo |
| 2 | Statistic core | `Winsorizer`, `Standardizer`, `Neutralizer`, `QuantileReturns`, `ReturnStats`, `ICCalculator`, `HacVariance`, `BlockBootstrap`, `ICSignificance`, `MultipleTestingAdjuster`, `TrialLog` with the formulas of FACTOR_TESTING_DESIGN §10 in the docstrings | known-answer tests of §10 pass (NW coverage, Holm/BH/BHY example, PT uniform p, bootstrap CI coverage); no I/O | 1 | todo |
| 3 | Universe | `UniverseStep` → `UNIVERSE_PANEL` per session: listed, not ST/*ST (via `namechange`), not suspended, ≥ 120 sessions since listing, exchanges per config (BJ excluded by default, D-054); exclusion reasons kept | counts per date plausible vs `stock_basic`; PIT test on an ST entry/exit; written to `derived/universe/` | 1 | todo |
| 4 | Factor library | `BaseFactor`, `FactorFactory`, `config/factors.yaml`; six factors in `factor/library/`: `EarningsYieldFactor` (EP TTM), `RoeFactor` (TTM), `ProfitGrowthFactor` (net profit TTM yoy), `MomentumFactor` (12-1), `ReversalFactor` (1-month, −), `TurnoverFactor` (60-session mean, −); each with a synthetic PIT test | six `FACTOR_PANEL`s over the full lake; each factor's restatement test proves no early visibility; coverage ≥ 90% of universe from 2019 | 2, 3 | todo |
| 5 | Preprocess, evaluate, combine | `FactorPreprocessor` (winsorise → standardise → industry/size neutralise, using `stock_basic.industry` until plan 05), `FactorEvaluator` → `FACTOR_REPORT` (IC series, §2 tests, campaign-level §3 adjustments, quantile ladder, turnover, decay), `SignalCombiner`, `FeaturePipeline` step writing `derived/features/` | reports for all six at h = 1/5/10/20/60 with NW t, bootstrap CI, BHY-adjusted p, HLZ flag, sub-period consistency; `TrialLog` records every variant; `make lake-rebuild` reproduces features byte-identical | 4 | todo |
| 6 | Chart + notebook | `FactorChart` (IC series with CI band, ICIR bars, quantile ladder, decay), notebook `YYYYMMDD_factor_campaign_01.ipynb` calling the package, outputs committed (D-051 pattern) | notebook runs top to bottom; acceptance verdict per factor per FACTOR_TESTING_DESIGN §6 printed; library entries marked accepted / composite-input / archived in FACTOR_LIBRARY | 5 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `LakeQuery` (extend), `PanelCache`, `TickerAliasMap` | extend / new | lake | 1 | `UniverseStep`, `BaseFactor` inputs via `FeaturePipeline`, notebooks, plan 05/06 |
| `UNIVERSE_PANEL`, `FACTOR_PANEL`, `IC_SERIES`, `IC_TEST`, `TRIAL_LOG`, `FACTOR_REPORT` | new schemas | core.frames | 1, 5 | producers/consumers above |
| `Winsorizer`, `Standardizer`, `Neutralizer`, `QuantileReturns`, `ReturnStats` | new | statistic | 2 | `FactorPreprocessor`, `FactorEvaluator`; plan 05 `ExposureStandardizer` |
| `ICCalculator`, `HacVariance`, `BlockBootstrap`, `ICSignificance`, `MultipleTestingAdjuster`, `TrialLog` | new | statistic | 2 | `FactorEvaluator`; plan 05 `RiskModelValidator`; plan 09 `EventStudy` |
| `UniverseStep` | new (`BaseStep`) | pipeline | 3 | `FeaturePipeline`, plan 05 estimation universe, plan 06 |
| `BaseFactor`, `FactorFactory`, six `*Factor` | new | factor | 4 | `FeaturePipeline`, `FactorEvaluator` |
| `FactorPreprocessor`, `FactorEvaluator`, `SignalCombiner` | new | factor | 5 | `FeaturePipeline`, notebook; plan 06 constructors consume `SignalCombiner` output |
| `FeaturePipeline` | new | pipeline | 5 | `cli features`, `CuratePipeline` |
| `FactorChart` | new (`BaseChart`) | visualization | 6 | notebook, plan 06 `ReportBuilder` |

## Risks
- Statistic formulas implemented as variants: mitigated by §10 being binding and the known-answer tests in §7/§10.
- Fundamental history from 2019 only: TTM growth needs 8 quarters, so growth factors start 2021; reported coverage will show it.
- Neutralisation with coarse `stock_basic.industry` until Shenwan arrives (plan 05); mark reports "pre-Shenwan".
- Bootstrap cost (2,000 × 6 × 5): cache `IC_SERIES`, run adjusters once per campaign.
- Lake contention with plan 09 downloads: coordinate via "lake free" messages.

## Open questions
None at approval; FACTOR_TESTING_DESIGN §9 recommendations adopted (Spearman for acceptance, HLZ 3.0 hurdle with Harvey-Liu reported, cached IC series).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-28 | — | Drafted and approved by user instruction; handed to quant-cn-b7 for execution |
