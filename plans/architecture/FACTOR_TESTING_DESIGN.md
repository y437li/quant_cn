# Factor Significance Testing Design (v1.2, 2026-09-30; D-060; D-090; decay reporting D-095)

What `statistic` must provide so that an IC, an ICIR or a Sharpe ratio is reported *with* its evidence, and so
that testing 55 candidate factors does not manufacture false discoveries. Every number in `FactorEvaluator`'s
report comes from these classes; the acceptance bar in FACTOR_LIBRARY §7 is defined in terms of them.

## 1. Estimands
| Quantity | Definition | Horizons |
|---|---|---|
| IC_t | cross-sectional Spearman (default) or Pearson correlation between factor value at T and forward return over h sessions | h = 1, 5, 10, 20, 60 |
| mean IC, ICIR | mean(IC_t), mean(IC_t)/sd(IC_t) (optionally × √(244/h) annualised) | |
| IC decay | mean IC as a function of h; half-life from an exponential fit | |
| Quantile spread | top-minus-bottom decile forward return; long-short Sharpe | |
| Hit rate | share of dates with IC_t > 0 | |

## 2. Single-factor tests (`IcSignificance`)
| Test | What it answers | Method |
|---|---|---|
| Newey-West t on mean IC | is mean IC ≠ 0 given autocorrelated IC_t (overlapping horizons make IC_t serially correlated by construction) | HAC standard error with lag = h − 1 (at least Bartlett with ⌊4(T/100)^{2/9}⌋); t = mean / se |
| Block-bootstrap CI | distribution of mean IC and ICIR without normality | stationary (Politis-Romano) or circular block bootstrap, block = max(h, 20), 2,000 resamples, seeded; 95% CI |
| Fisher-z on pooled IC | quick screen | z = atanh(IC) √(N−3), aggregated by Stouffer over dates (reported, not used for acceptance) |
| Pesaran-Timmermann (2009 version) | directional accuracy of factor sign vs return sign beyond chance | PT statistic with serial-correlation-robust variance |
| Sign consistency | does the factor work in every regime | mean IC sign and NW t per sub-period (2019–21, 2022–24, 2025–) and per `VIX_PANEL.regime` |
| Structural break | did the factor die | Bai-Perron single break in IC_t mean; sup-F with HAC |
| Decay fit | how fast it fades | mean IC by horizon h ∈ {1, 5, 10, 20, 60}; `peak_horizon` = argmax; exponential half-life fitted only on horizons ≥ peak; if the profile is non-decreasing through h = 60, report `half_life = NA (rising)` and `ic_60 / ic_20` as the accumulation ratio (D-095) |

## 3. Many-factor corrections (`MultipleTestingAdjuster`, `DataSnoopingTest`)
The catalogue has ~55 factors × 5 horizons × variants: dozens to hundreds of trials.
| Method | Use |
|---|---|
| Harvey, Liu & Zhu (2016) hurdle | a factor needs |t| ≥ 3.0 (not 2.0) to count as a discovery given the field's search history; applied to the NW t |
| Holm and Benjamini-Hochberg-Yekutieli | family-wise error (Holm) and false-discovery-rate (BHY, dependence-robust) adjusted p-values across all factors tested in one campaign; FDR target 5% |
| Romano-Wolf stepdown | bootstrap-based FWER control that uses the correlation between factor ICs (less conservative than Holm); shares the block bootstrap of §2 |
| White Reality Check / Hansen SPA | is the *best* factor in the family better than a zero benchmark after accounting for the search; SPA studentised and consistent p-value |
| Harvey & Liu (2020) double bootstrap | estimated share of true discoveries and the implied t-hurdle for *this* family; reported alongside HLZ's fixed 3.0 |

## 4. Backtest-level tests (`DeflatedSharpe`, `BacktestOverfitting`, `SharpeRatioTest`)
| Method | Use |
|---|---|
| Probabilistic Sharpe Ratio (Bailey & López de Prado 2012) | P(SR > benchmark) with skew and kurtosis corrections and finite sample length |
| Deflated Sharpe Ratio (2014) | PSR against the expected maximum Sharpe from N trials with variance of trial Sharpes; the number of trials is *logged by the evaluator*, not guessed |
| Minimum backtest length | sessions needed so a chosen SR is not attributable to the number of trials |
| Probability of Backtest Overfitting, CSCV (Bailey et al. 2017) | combinatorially symmetric cross-validation over S = 16 slices of the parameter-selection process; PBO ≤ 0.1 acceptable |
| Ledoit-Wolf (2008) HAC / bootstrap test for Sharpe differences | comparing two factors or a factor vs its composite; (2018) extension for several |
| Walk-forward out-of-sample | fit 2 years, trade 6 months, roll; out-of-sample IC and Sharpe reported separately from in-sample |

## 5. Classes (`statistic`, one module each, no I/O)
| Class | Purpose | Output |
|---|---|---|
| `IcCalculator` | IC_t series per horizon, Spearman/Pearson, with per-date N | `IC_SERIES` (`trade_date, factor, horizon, ic, n`) |
| `HacVariance` | Newey-West / Bartlett HAC variance with automatic or fixed lag | used by several classes |
| `BlockBootstrap` | stationary and circular block resampling of a time series or a panel of dates, seeded | resample generator |
| `IcSignificance` | §2 tests for one factor and horizon | `IC_TEST` rows (`factor, horizon, metric, value, se, t, p, ci_lo, ci_hi, window`) |
| `MultipleTestingAdjuster` | Holm, BHY, Romano-Wolf adjusted p-values; HLZ hurdle flag | `IC_TEST` rows with `p_adj_*` |
| `DataSnoopingTest` | White RC and Hansen SPA over a family of IC or return series | family-level p-values |
| `DeflatedSharpe` | PSR, DSR, minimum backtest length given a trial log | scalar rows |
| `BacktestOverfitting` | CSCV PBO over a parameter grid's performance matrix | PBO, logit distribution |
| `SharpeRatioTest` | Ledoit-Wolf difference test | statistic, p |
| `TrialLog` | append-only record of every factor/parameter variant evaluated in a campaign (feeds DSR and the adjusters) | `TRIAL_LOG` (`campaign, trial_id, factor, params, horizon, sr, ic_mean`) |
`factor.FactorEvaluator` (L5) orchestrates these and writes `FACTOR_REPORT` = IC series + tests + quantile results
per factor; `RiskModelValidator` reuses `HacVariance` and `BlockBootstrap`.

## 6. Acceptance bar (replaces FACTOR_LIBRARY §7's ICIR-only rule)
A factor enters `factor/library/` when, at the 20-session horizon on the full sample:
1. NW t of mean IC ≥ 3.0 (HLZ hurdle) **and** BHY-adjusted p ≤ 0.05 within its campaign;
2. same IC sign with NW t ≥ 1.5 in each of the three sub-periods;
3. block-bootstrap 95% CI of ICIR excludes 0;
4. for a traded variant: DSR ≥ 0.95 given the campaign's `TrialLog`, PBO ≤ 0.10, out-of-sample IC ≥ 50% of in-sample.
Otherwise it may stay as a documented *input to a composite* or be archived with its report.

## 7. Tests for the tests
- Simulated IC_t with known mean and AR(1) autocorrelation (φ = 0.3, 0.6) and MA(19) overlapping sums: prewhitened NW t coverage at 95% within ±2 pp (AR) and ≥ 93% (MA); naive t over-rejects (83% / 65%) as expected.
- Null family of 200 random factors: BHY keeps false discoveries ≤ 5%; Holm/Romano-Wolf FWER ≤ 5%; SPA p uniform.
- DSR reproduces the worked example in Bailey & López de Prado (2014); CSCV reproduces the PBO on the paper's synthetic grid.
- Pesaran-Timmermann on independent signs → p ≈ uniform.
- References are cited in each class docstring's Purpose with paper and year; formulas in the method docstrings.

## 8. Placement in plans
Plan 04 phase 2 ("statistic primitives") grows to include §5's classes in two steps: `IcCalculator`, `HacVariance`,
`BlockBootstrap`, `IcSignificance`, `MultipleTestingAdjuster`, `TrialLog` first (needed before any factor is
accepted); `DataSnoopingTest`, `DeflatedSharpe`, `BacktestOverfitting`, `SharpeRatioTest` in a later phase of
plan 04 or with plan 06 where traded backtests exist.

## 9. Open questions
1. Default IC: Spearman (robust to outliers, standard in A-share research) or Pearson on standardised values? Recommendation: Spearman for acceptance, both reported.
2. HLZ 3.0 fixed hurdle vs Harvey-Liu double-bootstrap hurdle estimated on our own family: use both, accept on the stricter? Recommendation: report both, accept on 3.0 until the family exceeds 100 trials.
3. Bootstrap size 2,000 per test × 55 factors × 5 horizons is heavy: cache IC series and run adjusters once per campaign.

## 10. Formulas (binding; each goes into the implementing method's docstring, with the reference)
Notation: `T` dates, `IC_t` the per-date IC, `μ̂ = mean(IC_t)`, `h` horizon in sessions.

**IC and forward return.** `IC_t = corr_rank(f_{i,t}, r_{i,t→t+h})` across stocks `i` in the universe at `t`
(Spearman; Pearson variant on standardised `f`). Forward return is **tradeable**: `r_{i,t→t+h} =
P^{adj}_{i, close(t+h)} / P^{adj}_{i, open(t+1)} − 1`, so the factor known at the close of `t` is traded at the
next open (SRC_DESIGN §4 time discipline). Option `close_to_close` (close t → close t+h) is reported for
comparison only. ICIR `= μ̂ / sd(IC_t)`; annualised `× √(244/h)` when stated.

**Newey-West HAC t, prewhitened (D-090).** Centre `x_t = IC_t − μ̂`. Prewhiten with an AR(1) fitted by OLS,
`ρ̂ = Σ x_t x_{t−1} / Σ x_{t−1}²`, capped at 0.97; residuals `e_t = x_t − ρ̂ x_{t−1}`. Bartlett kernel on the
residuals: `γ̂_l = (1/T) Σ_{t=l+1}^{T} e_t e_{t−l}`, `Ω̂_e = γ̂_0 + 2 Σ_{l=1}^{L} (1 − l/(L+1)) γ̂_l`,
`L = max(h − 1, ⌊4 (T/100)^{2/9}⌋)`. Recolour: `Ω̂ = Ω̂_e / (1 − ρ̂)²`; `se = √(Ω̂ / T)`; `t = μ̂ / se`;
two-sided `p` from Student-t with `T − 1` df. (Newey & West 1987, 1994; Andrews & Monahan 1992.)
The unprewhitened estimator is available (`prewhiten=False`) for comparison only: on the §7 simulations it
covers 93.8% / 89.8% / 88.4% (AR(1) φ = 0.3 / 0.6 / MA(19)) against 94.8% / 95.1% / 99.0% prewhitened, i.e. it
would let ~12% of null factors pass |t| > 1.96 at h = 20.

**Stationary block bootstrap** (Politis & Romano 1994). Block lengths `~ Geometric(1/b)`, `b = max(h, 20)`,
wrap-around; `B = 2,000` resamples, seed fixed; statistic recomputed per resample; 95% CI = percentile
[2.5%, 97.5%]; bootstrap `p` for `H0: μ = 0` = share of `|μ̂* − μ̂| ≥ |μ̂|`. Circular block bootstrap (fixed
block `b`) as an option.

**Pesaran-Timmermann (2009 regression form).** With sign indicators `y_t = 1{r_t > 0}`, `x_t = 1{f_t > 0}`
(here per stock-date pooled, or on the long-short return series), estimate `y_t = a + β x_t + e_t` by OLS;
`PT = β̂ / se_HAC(β̂)`, `p` from the normal. The 1992 statistic `(P̂ − P*) / √(V̂(P̂) − V̂(P*))` with
`P* = P_y P_x + (1 − P_y)(1 − P_x)` is reported alongside.

**Holm** (step-down FWER): order `p_(1) ≤ … ≤ p_(m)`; `p^{adj}_(i) = max_{j ≤ i} min(1, (m − j + 1) p_(j))`.
**Benjamini-Hochberg** (FDR): `p^{adj}_(i) = min_{j ≥ i} min(1, m p_(j) / j)`.
**Benjamini-Hochberg-Yekutieli** (FDR under arbitrary dependence): replace `m` by `m · c(m)`, `c(m) = Σ_{k=1}^{m} 1/k`.

**Romano-Wolf step-down** (2005, 2016 algorithm). Studentised statistics `t_k` for `k = 1..m`, ordered
descending; bootstrap (same block bootstrap) the vector `t*_k` under the null (recentred); at step `s`, the
critical value is the 95th percentile of `max_{k ∈ remaining} t*_k`; reject all remaining `k` with `t_k` above it,
remove them, repeat until none is rejected. Adjusted `p_k` = smallest level at which `k` is rejected, enforced
monotone.

**Harvey-Liu-Zhu hurdle** (2016): a discovery requires `|t_NW| ≥ 3.0`. **Harvey & Liu (2020)** double
bootstrap: bootstrap the panel of factor `IC_t` series to estimate the fraction of true nulls `π̂_0` and the
`t` hurdle giving 5% FDR for this family; report both hurdles.

**White Reality Check** (2000). For factors `k = 1..m` with per-date performance `d_{k,t}` (IC_t or long-short
return minus benchmark 0): `V̄ = max_k √T d̄_k`; bootstrap `V̄* = max_k √T (d̄*_k − d̄_k)`; `p = P(V̄* ≥ V̄)`.
**Hansen SPA** (2005): `T_SPA = max(0, max_k √T d̄_k / ω̂_k)` with `ω̂_k` the HAC sd of `d_{k,t}`; bootstrap
with recentring `μ̂^c_k = d̄_k · 1{√T d̄_k / ω̂_k ≥ −√(2 ln ln T)}` (consistent p); also report the lower
(`μ̂^l_k = min(d̄_k, 0)`) and upper (`μ̂^u = 0`) p-values.

**Probabilistic Sharpe Ratio** (Bailey & López de Prado 2012), per-period (not annualised) `ŜR`, `T`
observations, skew `γ̂_3`, kurtosis `γ̂_4` (non-excess, 3 for normal):
`PSR(SR*) = Φ[ (ŜR − SR*) √(T − 1) / √(1 − γ̂_3 ŜR + ((γ̂_4 − 1)/4) ŜR²) ]`.
**Deflated Sharpe Ratio** (2014): with `N` trials from `TrialLog` and `V̂[ŜR_n]` the variance of the trials'
Sharpe ratios, `SR* = √V̂[ŜR_n] · [ (1 − γ) Φ^{-1}(1 − 1/N) + γ Φ^{-1}(1 − 1/(N e)) ]`, `γ = 0.5772…`
(Euler-Mascheroni); `DSR = PSR(SR*)`. **Minimum backtest length** (2014): sessions
`T_min ≈ ( [ (1 − γ) Φ^{-1}(1 − 1/N) + γ Φ^{-1}(1 − 1/(N e)) ] / SR_target )²` with `SR_target` per period;
verify against the paper's figure in the test.

**CSCV probability of backtest overfitting** (Bailey, Borwein, López de Prado, Zhu 2017). Performance matrix
`M` (`T × N`, one column per trial); split rows into `S = 16` blocks; for each of the `C(S, S/2)` combinations,
in-sample = the chosen blocks, out-of-sample = the rest; `n* = argmax_n SR_IS(n)`; `ω̄ = rank_OOS(n*) / (N + 1)`;
`λ = ln(ω̄ / (1 − ω̄))`; `PBO = share of combinations with λ < 0` (the in-sample winner ranks below the median
out of sample). Also report the OOS-vs-IS performance degradation slope and the probability of OOS loss.

**Ledoit-Wolf Sharpe difference** (2008). `Δ̂ = ŜR_1 − ŜR_2` with `ŜR_k = μ̂_k / √(γ̂_k − μ̂_k²)`
(`γ̂_k` second non-central moment); gradient `∇` of `Δ` w.r.t. `(μ_1, μ_2, γ_1, γ_2)`; HAC (prewhitened,
Andrews-Monahan) covariance `Ψ̂` of the moment series; `se = √(∇ᵀ Ψ̂ ∇ / T)`; `p` from the normal or from
the studentised circular block bootstrap (their recommended version).

**Bai-Perron single break in mean.** For `τ ∈ [0.15T, 0.85T]`: `F(τ)` = HAC-Wald statistic for
`μ_{≤τ} = μ_{>τ}`; `supF = max_τ F(τ)`; critical values from Andrews (1993, trimming 0.15); report `τ̂`.

**Known-answer tests.** NW t coverage on simulated AR(1) IC series (φ = 0.3, 0.6; 1,000 sims, T = 1,000, within ±2 pp of 95%) and on MA(19) overlapping 20-session sums (≥ 93%); Holm/BH/BHY on the
textbook 10-p-value example; PSR/DSR on the worked example in Bailey & López de Prado (2014, §5); CSCV on the
paper's synthetic random-strategy grid (`PBO ≈ 0.5` for pure noise); SPA `p` uniform under a null family;
Pesaran-Timmermann `p` uniform for independent signs.

## 11. Point-in-time control, end to end
| Layer | Rule | Where enforced |
|---|---|---|
| Dataset | every dataset declares `known_on` (`trade_date`, `ann_date`, `f_ann_date`, `report_date`, `in_date`, …) in `config/datasets.yaml`; a dataset without it cannot be aligned | `DatasetSpec` validators, CODING_STANDARD §2.7 |
| Versions | restatements and forecast revisions are kept (`update_flag`, later `ann_date`); at `t` the visible version is the latest with effective date ≤ `t` (latest period first, then latest restatement, D-036) | `Compactor` keeps versions; `PitAligner` selects |
| Effective date | a value announced on day `d` is visible from the **first trading session strictly after** `d` (announcements can be after the close); the aligner joins on that effective date with an ASOF join, never on `end_date` | `PitAligner`, `TradingCalendar` |
| Prices | `prices_adj` uses `close × adj_factor` (backward-adjusted ratios): returns between two dates are invariant to later corporate actions, so forward returns and momentum are PIT-safe; price *levels* are not compared across dates | `DerivedViews`, `LakeQuery.read_prices` |
| Universe | membership at `t` uses `stock_basic` list/delist dates, `namechange` for ST status as of `t`, suspension = no bar at `t`, ≥ N sessions since listing; delisted stocks stay in history (no survivorship) | `UniverseStep` (plan 04) |
| Industry | Shenwan membership at `t` from `in_date ≤ t < out_date` | `IndustryClassifier` (plan 05) |
| Factor value | `f_{i,t}` uses only rows with effective date ≤ `t`; TTM sums are built from the four latest PIT-visible quarters at `t`, not from calendar quarters | `BaseFactor.compute` receives `FUNDAMENTALS_PIT` already aligned; the contract forbids any other fundamentals input |
| Forward return | starts at the **open of `t+1`** (tradeable), never at the close of `t` | `IcCalculator`, `ExecutionModel` (single owner of the lag) |
| Analyst data | `report_date` is the known-on; a report dated `d` is effective from the next session; consensus is rebuilt as of each `t` from reports with `report_date ≤ t` | FACTOR_LIBRARY §3b |
| Calendar | trading sessions are known 400 days ahead (D-050), so "next session" is always resolvable | `TradingCalendar` |
| Tests | every aligner and factor has a synthetic restatement test proving a value is not visible before its effective date (TC-PA-001..005 exist; each new factor adds one) | CODING_STANDARD §6 |
The rule of thumb baked into the contracts: **known-on column → next session → ASOF join → forward return from
the next open**. Nothing else in the codebase is allowed to join fundamentals or events to prices (§2.7).
