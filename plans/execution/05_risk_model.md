# 05 — Barra-style multi-factor risk model

| | |
|---|---|
| Status | done 2026-11-11 (phases 1–8); default `cne5_v3`; follow-up: USE4 alignment (factor-vol NW lags 5, gamma blend, monthly bias / MRAD), then re-test AIDC as a model style |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-045, D-061, D-127 |
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
| 1 | Industry and benchmark data (datasets delivered by plan 11 ph2; this phase = `IndustryClassifier` only) | `index_classify`, `index_member_all`, `index_weight` in `datasets.yaml`; `IndustryClassifier` (PIT membership, `stock_basic.industry` fallback) | live pull lands; every universe stock on a sample date maps to exactly one L1 industry; PIT test on an `out_date` | 04 ph1 | done 2026-11-11 |
| 2 | Descriptors and exposures | `DescriptorBuilder` (v1 per RISK_FACTOR_LIST §4: Size, Beta, Momentum, Residual Volatility, Book-to-Price, Liquidity with CNE5 weights), `ExposureStandardizer`, `RISK_EXPOSURE` schema | standardiser invariants pass; exposures for the 2026-08 sample written; missing-fill rate reported | 1 | done 2026-11-11 |
| 3 | Factor returns | `FactorReturnEstimator` (constrained WLS), `FACTOR_RETURN` | synthetic recovery corr > 0.99; industry constraint holds to 1e-10; live daily R² reported | 2 | done 2026-11-11 |
| 4 | Covariance and specific risk | `FactorCovarianceEstimator`, `EigenfactorAdjuster`, `VolatilityRegimeAdjuster`, `SpecificRiskEstimator`, `StructuralSpecificRisk`, `BayesianShrinker`, `FACTOR_COV`, `SPECIFIC_RISK` | PSD every date; synthetic bias stats in [0.9, 1.1]; regime multiplier logged | 3 | done 2026-11-11 |
| 5 | Model, step, validation | `RiskModel`, `RiskModelFactory`, `config/risk_model.yaml`, `RiskDecomposer`, `RiskModelValidator`, `pipeline.RiskModelStep`, `RiskChart`, notebook `YYYYMMDD_risk_model_validation.ipynb` | 12-month backfill fitted; bias stats of 100 random portfolios in [0.85, 1.15]; median daily R² ≥ 0.25; `make lake-rebuild` reproduces frames | 4 | done 2026-11-11 |
| 6 | Ten-style pass (v2) | Non-linear Size, Earnings Yield (CETOP, ETOP, EPFWD if `report_rc`), Growth (EGRO, SGRO, analyst if available), Leverage (MLEV, DTOA, BLEV) with CNE5 weights; fields from RISK_FACTOR_LIST §5 added and refetched | validation rerun; adjusted R² and bias stats not worse than v1; decision on default set; v3 (CNE6) scoped as a follow-up plan | 5 | done 2026-11-11 |
| 7 | US market sensitivity (proposed 2026-11-11) | dataset `index_global` (Tushare; SPX, US date d visible from the next China session); descriptor `us_beta` = partial beta of the stock's China-day-t return on the S&P 500 return of the last US session before t, controlling for the China cap-weighted market (252 d, half-life 63, `PriceDescriptors.compute_partial_beta`); style `us_sensitivity` in `config/risk_model.yaml` | gate (D-061 v3): kept only if median adjusted R² rises and random-portfolio / benchmark bias stats stay in [0.85, 1.15] vs `cne5_v2`; else left out of the default with the numbers logged | 6 | done 2026-11-11 (gate passed; in default `cne5_v2_spx`) |
| 8 | Requested styles (2026-11-11, via session quant-cn-5c) | generic `external_series` / `theme_baskets` in `config/risk_model.yaml`; (a) FCFP = (TTM OCF − TTM capex) / mcap as style `cash_flow_yield` (orth. to earnings_yield, book_to_price) or inside earnings_yield; (b) `usd_sensitivity` = partial beta on USDCNH.FXCM (FXCM bars dated by their open: +1 day shift); (c) `ai_dc_sensitivity` = partial beta on the 885887.TI 数据中心(AIDC) basket (circ_mv-weighted, excluding the stock, from the 2020-03-06 list date; membership is a 2026 snapshot); (d) `arm_sensitivity` = partial beta on the overnight Arm Holdings (Nasdaq ARM) return, China market controlled, same alignment as `us_beta` (US date d usable from the next China session); new dataset `us_daily` (Tushare, ARM only for now; access checked 2026-11-12: 794 rows 2023-09-14..2026-11-11, IPO-day row dropped); no exposure before 252 d of history (≈ 2024-09), so the style starts then (D-133); (e) `gold_sensitivity` = partial beta on XAUUSD.FXCM (`fx_daily`, bid_close, +1 day shift like USD; access checked: 2019-01..2026-11-11); (f) `us_rate_sensitivity` = partial beta on the daily change of the US 10-year Treasury yield (new dataset `us_tycr`, column y10; new external kind `level` = first difference in bp; US date d usable from the next China session; checked 2019-01..2026-11-10); (g) `oil_sensitivity` = partial beta on INE crude (SC main contract from `fut_daily`, same-day: night + day session close at 15:00, so no overnight shift) because FXCM USOil / UKOil stop at 2023-06-01 (D-133) | same gate as phase 7 vs `cne5_v2_spx`, numbers logged per style (D-134 USD, D-130 AIDC, D-131 FCF) | 7 | done 2026-11-11 — default `cne5_v3` (cash_flow_yield + usd_sensitivity), `ai_dc_sensitivity` as monitor |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `IndustryClassifier` | **reuse** `derived.industry_l1` via `lake.ExposureReader` (D-093, D-127) | lake | 1 | `RiskInputLoader` |
| `RiskInputs`, `RiskInputLoader` | new | risk | 2 | `RiskModelStep` |
| `EwmWindow`, `PriceDescriptors`, `FundamentalDescriptors` | new | risk | 2 | `DescriptorBuilder`, estimators |
| `DescriptorBuilder`, `ExposureStandardizer` | new (reuse `statistic.Standardizer`, `Neutralizer`) | risk | 2 | `RiskModel` |
| `FactorReturnEstimator` | new | risk | 3 | `RiskModel` |
| `FactorCovarianceEstimator`, `EigenfactorAdjuster`, `VolatilityRegimeAdjuster` | new | risk | 4 | `RiskModel` |
| `SpecificRiskEstimator`, `StructuralSpecificRisk`, `BayesianShrinker` | new | risk | 4 | `RiskModel` |
| `BaseRiskModel`, `RiskModel`, `RiskSnapshot`, `RiskModelFactory` | new | risk | 5 | `RiskModelStep`, `RiskDecomposer`, notebook; later `portfolio` (frames) |
| `RiskDecomposer`, `RiskModelValidator` | new | risk | 5 | notebook, `RiskValidationWriter`; later `back_testing` (frames) |
| `RiskModelStep`, `RiskValidationWriter` | new (`BaseStep`) — standalone `make risk-model`, not in curate (D-127) | pipeline | 5 | `cli.ServiceBuilder`, `ResearchCommands` |
| `RiskChart` | new (subclass `BaseChart`) | visualization | 5 | notebook, later `ReportBuilder` |
| `RiskModelSettings`, `StyleSpec` | new (`config/risk_model.yaml`) | core | 2–6 | every risk class |
| `RISK_EXPOSURE`, `FACTOR_RETURN`, `SPECIFIC_RETURN`, `FACTOR_COV`, `SPECIFIC_RISK`, `RISK_DECOMP`, `RISK_VALIDATION` | new schemas (`SPECIFIC_RETURN` added, D-127) | core.frames | 2–5 | producers above; `portfolio`, `back_testing` consumers |
| `SyntheticMarket` | built as test helper `tests/risk/synthetic_market.SyntheticFactorMarket` | tests | 3 | risk tests |

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
| 2026-11-12 | 8 | (h) `dividend_yield` (DTOP = dv_ttm / 100, user "加入股息率"; added by quant-cn-5c, b5 offline): passed the gate vs cne5_v3 (adj R² 0.2741 vs 0.2733, bias unchanged, own bias 1.031); default renamed `cne5_v3_dy` (D-148); TC-DB-006 |
| 2026-11-11 | 8 | User accepted the recommendation ("ok"; AIDC "可以monitor", "单独展示"): default `cne5_v3` = CNE5 ten + us_sensitivity + usd_sensitivity + cash_flow_yield; live run 650d1711f7fe median adj R² 0.2732 (v2_spx 0.2711), random portfolios 100% in band (median 1.018), CSI 300/500/1000 0.934/1.082/1.046; FCFP inside EY rejected (0.2707); `ai_dc_sensitivity` = monitor style (`monitor_returns.parquet`, notebook §6, D-130); scalable digests for the risk tables after an OOM on 115.6 M rows (D-135); decisions D-130, D-131, D-134, D-135 |
| 2026-11-12 | 8 | (e) gold, (f) US 10y rate, (g) crude oil sensitivities added (user: "还有原油,美国的利率，以及黄金的sensitive"); same gate |
| 2026-11-12 | 8 | (d) `arm_sensitivity` added to the phase-8 candidates (user: "把arm也加进去吧", meaning Arm share-price sensitivity); runs through the same gate; D-133 proposed |
| 2026-11-11 | 5 | Live lake: `make risk-model` run 24e0c12dfcdb (`cne5_v2_spx`, 118.6 M rows, ~9 min) reproduces the catalog-copy fit to 3e-12; digests recorded; notebook `20261111_risk_model_validation.ipynb` executed; `make check` passes |
| 2026-11-11 | 7 | Done (user approved "spx only"): `index_global` SPX, `us_beta` partial beta, style `us_sensitivity`. Gate vs `cne5_v2`, 2019→2026: median adj R² 0.2711 vs 0.2695, last-year R² 0.304 vs 0.301, random portfolios 100% in band (median 1.019), median factor abs(bias - 1) 0.057 vs 0.059, CSI 300/500/1000 0.936/1.081/1.044, own bias 0.886; daily mean abs t 2.58 (1.8 in 2019 → 3.3 in 2026). Default renamed `cne5_v2_spx` (D-128) |
| 2026-11-11 | 7 | Proposed (user: "这里面要加美股s&p的factor"): S&P 500 sensitivity style behind the v3 gate |
| 2026-11-11 | 6 | Default set decided: `cne5_v2` (ten styles). 2019→2026 on a catalog copy: median adj R² 0.2695 vs v1 0.2615; last-year R² 0.301 vs 0.291; random portfolios 100% in band for both (median bias 1.016 vs 1.006); median factor abs(bias - 1) 0.059 vs 0.067; CSI 300 bias 0.930 vs 0.876 |
| 2026-11-11 | 1–6 | Built (user: "把A股版barra 做好"): `risk` package (19 classes), `RiskModelStep` + `RiskValidationWriter`, `RiskChart`, 7 frames, `config/risk_model.yaml` (default `cne5_v2`, ten styles), `make risk-model`; 80 tests, risk coverage 99%; D-127 records the build choices (industry view reused, full seeded refit outside curate, monthly growth snapshots, coverage gate, `SPECIFIC_RETURN`) |
| 2026-09-28 | 2, 6 | RISK_FACTOR_LIST (D-061): v1/v2/v3 sets and published CNE5 weights adopted; phase 6 = CNE5 v2 |
| 2026-09-28 | — | Approved by user ("approve"); §7 recommendations adopted |
| 2026-09-27 | — | Drafted from user request: Barra-style risk management model |
