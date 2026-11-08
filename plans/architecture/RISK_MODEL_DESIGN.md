# Risk Model Design — Barra-style multi-factor risk model (v1.1, 2026-09-28; D-045; factor list per D-061)

`src/quant_cn/risk/` (L5, beside `factor`, mutually independent) estimates a fundamental multi-factor risk
model of the CNE5/CNE6 family for A-shares: style + industry + country factors, daily factor returns by
constrained weighted regression, a factor covariance matrix and stock-specific risk, all as lake frames.
Consumers: `portfolio` (optimiser, constraints), `back_testing` (risk attribution), research notebooks.

## 1. Model
Return decomposition per stock `n` on day `t`:  `r_n = f_c + Σ_i X_ni f_i + Σ_s X_ns f_s + u_n`
- **Country factor** `f_c`: exposure 1 for every stock.
- **Industry factors** `f_i`: Shenwan level-1 classification (31 industries), exposure 0/1. Constraint
  `Σ_i w_i f_i = 0` with `w_i` = industry cap weights, which identifies the country factor.
- **Style factors** `f_s` (CNE5 set, descriptors in §3): Size, Beta, Momentum, Residual Volatility,
  Non-linear Size, Book-to-Price, Liquidity, Earnings Yield, Growth, Leverage. Exposures are winsorised
  (±3 sd), standardised to cap-weighted mean 0 and equal-weighted sd 1, then orthogonalised where CNE5
  does (Residual Volatility and Non-linear Size vs Size and Beta).
- **Estimation universe**: `UniversePanel` (listed, not ST, not suspended, ≥ 6 months since listing);
  regression weights `√(circ_mv)`, capped at the 95th percentile.
- **Factor covariance** `F`: EWMA on factor returns (vol half-life 90 d, correlation half-life 480 d),
  Newey-West autocorrelation adjustment (lags 2), eigenfactor risk adjustment (de-bias small eigenvalues),
  volatility regime adjustment (cross-sectional bias statistic scaling). Forecast horizon 21 days.
- **Specific risk** `Δ`: EWMA of residual variance (half-life 90 d, Newey-West lags 5); structural model
  (regression of specific vol on exposures) for stocks with thin residual history; Bayesian shrinkage
  toward size-decile means; same regime adjustment.
- **Portfolio risk**: `σ_p² = hᵀ X F Xᵀ h + hᵀ Δ h`; marginal contributions, factor/specific split,
  active risk vs a benchmark from `index_weight`.

## 2. Package shape (`risk/`, one module per class)
| Class | Purpose |
|---|---|
| `BaseRiskModel` | `fit(start, end)` → model frames; `predict_portfolio_risk(weights, date)`; declares inputs and output schemas |
| `IndustryClassifier` | Shenwan L1 membership per date from `index_member_all` (fallback `stock_basic.industry` mapped to 31 groups), PIT on `in_date`/`out_date` |
| `DescriptorBuilder` | raw descriptors (§3) from `PRICE_PANEL`, `daily_basic`, `FUNDAMENTALS_PIT`; one method per descriptor, verb `compute_` |
| `ExposureStandardizer` | winsorise → cap-weighted demean → equal-weighted unit sd → orthogonalise; fills missing exposures by industry-size regression |
| `FactorReturnEstimator` | per-date constrained WLS (`√cap` weights, industry constraint via restriction matrix); returns factor returns, t-stats, R², residuals |
| `FactorCovarianceEstimator` | EWMA + Newey-West → `EigenfactorAdjuster` → `VolatilityRegimeAdjuster` |
| `EigenfactorAdjuster` | Monte-Carlo eigenvalue de-biasing (CNE5 §, 1,000 sims, seeded) |
| `VolatilityRegimeAdjuster` | bias-statistic multiplier λ over a trailing window; applied to F and Δ |
| `SpecificRiskEstimator` | EWMA residual vol → `StructuralSpecificRisk` fallback → `BayesianShrinker` |
| `RiskModel` (`BaseRiskModel`) | orchestrates the above; writes `RISK_EXPOSURE`, `FACTOR_RETURN`, `FACTOR_COV`, `SPECIFIC_RISK`; loads a fitted model for a date |
| `RiskDecomposer` | portfolio total/active risk, factor vs specific, marginal and % contributions, top exposures → `RISK_DECOMP` |
| `RiskModelValidator` | bias statistics (portfolio and factor), Q-statistics, R² time series → `RISK_VALIDATION` |
| `RiskModelFactory` | name → configured `RiskModel` from `config/risk_model.yaml` (half-lives, lags, universe, factor set) |

`pipeline.RiskModelStep` (L6) runs `RiskModel.fit` incrementally per date and writes `curated/derived/risk/<model>/`.
`visualization.RiskChart` (L7): factor-return cumulative lines, covariance heatmap, risk decomposition bars.

## 3. Descriptors
Full list, published CNE5 weights, CNE6 extensions and the Tushare mapping: `RISK_FACTOR_LIST.md`. Plan 05
builds v1 (Size, Beta, Momentum, Residual Volatility, Book-to-Price, Liquidity) in phase 2 and completes CNE5's
ten in phase 6 (Non-linear Size, Earnings Yield = CETOP 0.21 / ETOP 0.11 / EPFWD 0.68 if analyst data,
Growth = EGRO 0.24 / SGRO 0.47 / analyst 0.29, Leverage = MLEV 0.38 / DTOA 0.35 / BLEV 0.27). Missing analyst
descriptors renormalise the remaining weights and flag `no_analyst`. CNE6 additions are v3.

## 4. Frames (`core.frames`, long format)
| Schema | Primary key | Columns |
|---|---|---|
| `RISK_EXPOSURE` | `trade_date, ts_code, factor` | exposure, exposure_raw, is_filled |
| `FACTOR_RETURN` | `trade_date, factor` | ret, t_stat, r2 (per date, repeated), n_obs |
| `FACTOR_COV` | `trade_date, factor_i, factor_j` | cov, cov_raw, horizon_days |
| `SPECIFIC_RISK` | `trade_date, ts_code` | sigma, sigma_raw, method (ewma / structural / shrunk) |
| `RISK_DECOMP` | `trade_date, portfolio, component` | risk, pct, kind (factor / specific / total / active) |
| `RISK_VALIDATION` | `trade_date, metric, scope` | value, window, notes |

## 5. Data to add
| Dataset | Endpoint | Sweep | Key | Known on | Use |
|---|---|---|---|---|---|
| `index_classify` | `index_classify` | `src=SW2021`, `level=L1` | `index_code` | — | Shenwan L1 industry list |
| `index_member_all` | `index_member_all` | `l1_code` | `ts_code, l1_code, in_date` | `in_date` | membership history with `out_date` |
| `index_weight` | `index_weight` | `index_code` + month window | `index_code, con_code, trade_date` | `trade_date` | benchmark weights for active risk (CSI 300/500/1000) |

## 6. Tests
- Synthetic market with a known factor structure (`core.testing.SyntheticMarket` extended with factor loadings and covariance): estimator recovers factor returns (corr > 0.99), covariance within tolerance, specific risk unbiased.
- Constraint holds: cap-weighted industry returns sum to 0 to 1e-10 every date.
- Standardiser: cap-weighted mean 0, sd 1, winsorisation bounds respected.
- Eigenfactor adjustment: eigenvalues of the adjusted matrix ≥ raw for small eigenvalues on a simulated set; matrix stays PSD.
- Bias statistics on simulated data fall within [0.9, 1.1] for random portfolios.
- Live acceptance (plan phase 5): bias statistics for 100 random long-only portfolios over a 12-month window between 0.85 and 1.15; median R² of daily regressions ≥ 0.25.

## 7. Open questions
None. Closed 2026-09-28 with the recommendations: six styles in v1, ten in a second pass (config); `.BJ` excluded; CNE5 half-lives 90/480 as defaults, tuned via `RiskModelValidator` with a decision; optimiser in `portfolio`, frames only between `risk` and `portfolio`.
