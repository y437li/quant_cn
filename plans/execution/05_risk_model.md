# 05 — Barra-style multi-factor risk model

| | |
|---|---|
| Status | approved 2026-09-28, not started (after plan 04) |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-045, D-061 |
| Depends on plans | 04 (factors: read API, universe, `statistic` primitives, descriptors reuse) |

## Goal
A daily fitted CNE5-style risk model for A-shares (country + 31 Shenwan industries + style factors) whose
factor covariance and specific risk forecast realised risk without bias, stored as lake frames and usable
by the portfolio optimiser and for risk attribution.

## Scope
- In: `risk` package (RISK_MODEL_DESIGN §2), Shenwan and index-weight datasets, `RiskModelStep`, six risk frames, `RiskChart`, validation notebook.
- Out: the optimiser itself (plan 06), transaction-cost model, intraday risk, analyst-estimate descriptors (no data).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Industry and benchmark data (datasets delivered by plan 11 ph2; this phase = `IndustryClassifier` only) | `index_classify`, `index_member_all`, `index_weight` in `datasets.yaml`; `IndustryClassifier` (PIT membership, `stock_basic.industry` fallback) | live pull lands; every universe stock on a sample date maps to exactly one L1 industry; PIT test on an `out_date` | 04 ph1 | todo |
| 2 | Descriptors and exposures | `DescriptorBuilder` (v1 per RISK_FACTOR_LIST §4: Size, Beta, Momentum, Residual Volatility, Book-to-Price, Liquidity with CNE5 weights), `ExposureStandardizer`, `RISK_EXPOSURE` schema | standardiser invariants pass; exposures for the 2026-08 sample written; missing-fill rate reported | 1 | todo |
| 3 | Factor returns | `FactorReturnEstimator` (constrained WLS), `FACTOR_RETURN` | synthetic recovery corr > 0.99; industry constraint holds to 1e-10; live daily R² reported | 2 | todo |
| 4 | Covariance and specific risk | `FactorCovarianceEstimator`, `EigenfactorAdjuster`, `VolatilityRegimeAdjuster`, `SpecificRiskEstimator`, `StructuralSpecificRisk`, `BayesianShrinker`, `FACTOR_COV`, `SPECIFIC_RISK` | PSD every date; synthetic bias stats in [0.9, 1.1]; regime multiplier logged | 3 | todo |
| 5 | Model, step, validation | `RiskModel`, `RiskModelFactory`, `config/risk_model.yaml`, `RiskDecomposer`, `RiskModelValidator`, `pipeline.RiskModelStep`, `RiskChart`, notebook `YYYYMMDD_risk_model_validation.ipynb` | 12-month backfill fitted; bias stats of 100 random portfolios in [0.85, 1.15]; median daily R² ≥ 0.25; `make lake-rebuild` reproduces frames | 4 | todo |
| 6 | Ten-style pass (v2) | Non-linear Size, Earnings Yield (CETOP, ETOP, EPFWD if `report_rc`), Growth (EGRO, SGRO, analyst if available), Leverage (MLEV, DTOA, BLEV) with CNE5 weights; fields from RISK_FACTOR_LIST §5 added and refetched | validation rerun; adjusted R² and bias stats not worse than v1; decision on default set; v3 (CNE6) scoped as a follow-up plan | 5 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `IndustryClassifier` | new | risk | 1 | `DescriptorBuilder`, `ExposureStandardizer`, `FactorReturnEstimator`, `RiskDecomposer`; later `factor.Neutralizer` inputs via frames |
| `DescriptorBuilder`, `ExposureStandardizer` | new | risk | 2 | `RiskModel` |
| `FactorReturnEstimator` | new | risk | 3 | `RiskModel`, `RiskModelValidator` |
| `FactorCovarianceEstimator`, `EigenfactorAdjuster`, `VolatilityRegimeAdjuster` | new | risk | 4 | `RiskModel` |
| `SpecificRiskEstimator`, `StructuralSpecificRisk`, `BayesianShrinker` | new | risk | 4 | `RiskModel` |
| `BaseRiskModel`, `RiskModel`, `RiskModelFactory` | new | risk | 5 | `RiskModelStep`, `RiskDecomposer`, notebook; later `portfolio` optimiser (frames) |
| `RiskDecomposer`, `RiskModelValidator` | new | risk | 5 | notebook; later `back_testing.PerformanceAnalyzer` (frames) |
| `RiskModelStep` | new (subclass `BaseStep`) | pipeline | 5 | `CuratePipeline`, `cli` |
| `RiskChart` | new (subclass `BaseChart`) | visualization | 5 | notebook, later `ReportBuilder` |
| `RISK_EXPOSURE`, `FACTOR_RETURN`, `FACTOR_COV`, `SPECIFIC_RISK`, `RISK_DECOMP`, `RISK_VALIDATION` | new schemas | core.frames | 2–5 | producers above; `portfolio`, `back_testing` consumers |
| `SyntheticMarket` | extend (factor loadings, covariance) | core.testing | 3 | risk tests, later backtest tests |

## Risks
- Short fundamental history in the lake (2019+): growth descriptors need 3–5 years; phase 6 depends on the backfill depth (D-015b).
- Thin residual histories for new listings: structural model and shrinkage must be tested on the live sample, not just synthetic.
- Shenwan classification revisions (2014 vs 2021 scheme): pin `SW2021` and record any remapping as a decision.
- Computational cost: 1,000-sim eigenfactor adjustment per date; cache per date, run only on refits.
- Half-lives and lags are judgement calls; every value lives in `config/risk_model.yaml` with the CNE5 default noted.

## Open questions
None. RISK_MODEL_DESIGN §7 closed with the recommendations: six styles first then ten (both behind config); `.BJ` excluded from the estimation universe; CNE5 default half-lives (90/480) tuned later via `RiskModelValidator`; the optimiser lives in `portfolio` and consumes `FACTOR_COV`/`SPECIFIC_RISK` frames, `risk` and `portfolio` never import each other.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-28 | 2, 6 | RISK_FACTOR_LIST (D-061): v1/v2/v3 sets and published CNE5 weights adopted; phase 6 = CNE5 v2 |
| 2026-09-28 | — | Approved by user ("approve"); §7 recommendations adopted |
| 2026-09-27 | — | Drafted from user request: Barra-style risk management model |
