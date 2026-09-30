# Factor Library Catalogue (v0.4, 2026-09-28; D-055; analyst family; testing protocol per D-060; commodity/sector family per D-062)

Candidate factors for `factor/library/`, grouped by family, with construction, data mapping and point-in-time
notes. This is the shopping list for plan 04; each factor becomes one `BaseFactor` subclass only after it is
selected. Conventions: value at date T uses data knowable by the close of T; prices are adjusted
(`derived.prices_adj`); fundamentals via `FUNDAMENTALS_PIT`; TTM = trailing four quarters summed from PIT
statements; "yoy" = same quarter previous year. Sign: **higher raw value = expected higher return** unless
marked (−), in which case the factor is negated before standardisation.

## 1. Value
| Factor | Construction | Data | Notes |
|---|---|---|---|
| EP (earnings yield) | net profit TTM / total_mv | `income_vip.n_income_attr_p` (TTM), `daily_basic.total_mv` | or `1/pe_ttm` from `daily_basic` as a cheap variant |
| BP (book to price) | total equity attributable / total_mv | `balancesheet_vip` (total_hldr_eqy_exc_min_int, add field), `daily_basic` | `1/pb` variant available |
| SP (sales yield) | revenue TTM / total_mv | `income_vip.revenue` (add field) | `1/ps_ttm` variant |
| CFP (cash-flow yield) | operating cash flow TTM / total_mv | `cashflow_vip.n_cashflow_act` | |
| FCFP | free cash flow TTM / total_mv | `cashflow_vip.free_cashflow` | sparse before 2019 |
| DP (dividend yield) | `dv_ttm` | `daily_basic.dv_ttm` | percent units |
| EBITDA/EV | ebitda TTM / (total_mv + interest debt − cash) | `fina_indicator_vip.ebitda`, `interestdebt`, `balancesheet_vip.money_cap` | |
| Long-term reversal (−) | 3-year return excl. last 12 months | `prices_adj` | value-adjacent |

## 2. Quality
| Factor | Construction | Data | Notes |
|---|---|---|---|
| ROE | net profit TTM / average equity | `fina_indicator_vip.roe` (single quarter) or TTM built | prefer TTM build |
| ROA | `fina_indicator_vip.roa` TTM | | |
| ROIC | `fina_indicator_vip.roic` | | |
| Gross margin | `grossprofit_margin` TTM | `fina_indicator_vip` | |
| Net margin | `netprofit_margin` TTM | | |
| Accruals (−) | (net profit − operating cash flow) TTM / total assets | `income_vip`, `cashflow_vip`, `balancesheet_vip.total_assets` | Sloan accruals |
| Cash-flow to profit | operating cash flow TTM / net profit TTM | | earnings quality |
| Earnings stability | −sd(quarterly EPS yoy growth, 12 quarters) | `fina_indicator_vip.eps` | |
| ROE stability | −sd(quarterly ROE, 12 quarters) | | |
| Leverage (−) | `debt_to_assets` | `fina_indicator_vip` | |
| Asset turnover | `assets_turn` TTM | | |
| Goodwill / assets (−) | `goodwill / total_assets` | `balancesheet_vip` | impairment risk |
| Receivables growth (−) | yoy growth of accounts_receiv minus yoy revenue growth | `balancesheet_vip.accounts_receiv`, `income_vip.revenue` | |
| Piotroski F-score | 9 binary signals (profit, cash flow, ROA Δ, accruals, leverage Δ, liquidity Δ, no issuance, margin Δ, turnover Δ) | statements + `total_share` | composite |

## 3. Growth (fundamental)
| Factor | Construction | Data | Notes |
|---|---|---|---|
| Net profit growth | `netprofit_yoy` (single-quarter yoy) and TTM yoy | `fina_indicator_vip.netprofit_yoy`, `dt_netprofit_yoy` | deducted-non-recurring variant preferred |
| Revenue growth | `or_yoy`, TTM yoy | `fina_indicator_vip.or_yoy` | |
| Operating cash-flow growth | TTM yoy | `cashflow_vip` | |
| Growth acceleration | Δ of quarterly yoy growth vs previous quarter | derived | |
| Earnings surprise (SUE) | (actual quarterly EPS − expected) / sd; expected from seasonal random walk (4 quarters ago + drift) | `fina_indicator_vip.eps` | no analyst data; PEAD driver |
| Earnings-announcement return | cumulative abnormal return in [−1, +1] sessions around `f_ann_date` | `prices_adj`, PIT dates | event factor, plan 07 |
| Forecast revision | change in `p_change_min/max` midpoint between forecast versions | `forecast` (plan 07) | plan 07 |
| Long-term growth | 5-y (fallback 3-y) regression slope of revenue and EPS scaled by mean | statements | same as CNE5 SGRO/EGRO |

## 3b. Analyst revisions and expectations (needs `report_rc`; permission tier to verify)
Source: Tushare `report_rc` (券商研报盈利预测: per report `ts_code, report_date, org_name, author_name, report_title,
classify, quarter, op_rt, op_pr, tp, np, eps, pe, rd, roe, ev_ebitda, rating, max_price, min_price`), swept by
`report_date` on all calendar days (weekend reports exist). **`tp` is total profit (10k CNY), not target price**;
target prices are `max_price`/`min_price`. Each report carries ~3 forecast rows (quarters, e.g. 2026Q2…2028Q2);
rating-only reports have no quarter. Coverage 2019+: 90–107 brokers, 2.5–3.5k stocks per year, 60–175 stocks per day.
Known-on = `report_date` (publication day; treat as after-close, effective next session). Build a **consensus
snapshot per stock per day**: for each fiscal year, the mean/median of each broker's latest forecast within a
trailing 90-day window (one vote per broker, latest report wins). Complements: `stk_surv` (机构调研, survey
visits), `broker_recommend` (monthly broker picks), `ccass_hold`/`hk_hold` (northbound holdings, flow proxy).

| Factor | Construction | Notes |
|---|---|---|
| EPS revision 1M / 3M | (consensus FY1 EPS today − consensus 21/63 sessions ago) / |consensus 63 sessions ago| | core revision factor; also FY2 |
| Revision breadth | (# brokers raising FY1 − # lowering) / # brokers with two reports in the window | diffusion index, robust to outliers |
| Revision momentum | 3-month EW sum of monthly consensus changes, half-life 1 month | |
| Target-price implied return | median of (max_price + min_price)/2 across brokers / close − 1 | (+); shrink when coverage < 3; `tp` is NOT a target price |
| Target-price revision | change in median target over 63 sessions | |
| Rating change | Δ of mean numeric rating (买入 = 5 … 卖出 = 1) over 63 sessions; upgrades − downgrades | |
| Coverage | ln(1 + # brokers in window); Δ coverage over 63 sessions | (+) for Δ; low coverage = neglected-stock premium (−) |
| Forecast dispersion (−) | sd / |mean| of FY1 EPS across brokers | uncertainty |
| Forward EP | consensus FY1 EPS (time-weighted FY1/FY2 to a 12-month horizon) / price | replaces the missing EPIBS in CNE5 Earnings Yield (RISK_MODEL_DESIGN §3) |
| Forward growth | consensus FY2 EPS / FY1 EPS − 1 | |
| Surprise vs consensus | (actual EPS − consensus before announcement) / sd of forecasts | replaces the seasonal-random-walk SUE when coverage exists |
| Survey intensity | # institutional survey visits in 63 sessions, ln(1 + n) | `stk_surv` |
| Northbound flow | 20-session change in northbound holding ratio | `hk_hold`; regime-sensitive |

Data to add (plan 07 events, or earlier if the tier allows): `report_rc` (sweep `report_date`, large: ~300k
reports/year), `stk_surv`, `broker_recommend`, `hk_hold`. Check `report_rc` permission with one live call before
scheduling the backfill; if unavailable, the analyst family stays documented but unbuilt and CNE5 Earnings Yield
keeps ETOP/CETOP only.

## 4. Momentum and reversal
| Factor | Construction | Data | Notes |
|---|---|---|---|
| 12-1 momentum | return over [T−252, T−21] | `prices_adj` | classic |
| 6-1 momentum | return over [T−126, T−21] | | |
| 1-month reversal (−) | return over last 21 sessions | | strong in A-shares |
| Short-term reversal (−) | 5-session return | | |
| Residual momentum | 12-1 momentum of residuals from a market (and later risk-model) regression | `prices_adj`, index return; `FACTOR_RETURN` later | |
| Momentum consistency | share of positive months in last 12 | | |
| 52-week high proximity | close / max(high, 252) | | |
| Volume-weighted momentum | return weighted by turnover rank | `daily_basic.turnover_rate_f` | |
| Industry momentum | industry cap-weighted 6-1 momentum assigned to members | `IndustryClassifier` (plan 05) | |
| Moneyflow momentum | 20-session sum of `net_mf_amount` / circ_mv | `moneyflow`, `daily_basic.circ_mv` | A-share specific |
| Large-order flow | 20-session sum of (buy_lg + buy_elg − sell_lg − sell_elg) amount / amount | `moneyflow` | |

## 5. Size, volatility, liquidity (risk-style, also used by the risk model)
| Factor | Construction | Data | Notes |
|---|---|---|---|
| Size (−) | ln(total_mv) | `daily_basic` | small-cap premium historically strong, regime-dependent |
| Non-linear size | cube of standardised size, orthogonalised | derived | |
| Beta (−) | 252-session beta to cap-weighted market, hl 63 | `prices_adj` | |
| Idiosyncratic volatility (−) | sd of residuals from market model, 20/60 sessions | | low-vol anomaly |
| Total volatility (−) | sd of daily returns, 20/60/252 | | |
| Max daily return (−) | max return over last 20 sessions | | lottery |
| Turnover (−) | mean `turnover_rate_f` 20/60/252 | `daily_basic` | strong (−) in A-shares |
| Turnover change (−) | 20-session / 252-session turnover | | |
| Amihud illiquidity | mean(|ret| / amount) 20 sessions | `daily.amount` (千元) | (+) premium |
| Amount volatility | sd(ln amount) 20 sessions | | |
| Limit-hit frequency | share of last 60 sessions closed at up/down limit | `stk_limit`, `daily.close` | A-share specific |
| Chip concentration | `winner_rate`, `cost_95pct/cost_5pct` | `cyq_perf` (higher tier, not yet fetched) | optional |

## 5b. Commodity, macro and sector (plan 10, MACRO_COMMODITY_DESIGN §3.2)
| Factor | Construction | Data | Notes |
|---|---|---|---|
| Commodity spillover momentum | 20/60-session return of the stock's linked commodity (`commodity_links.yaml`: industry → products) | `CONTINUOUS_PANEL` | applies to linked industries only; zero/neutral elsewhere |
| Commodity term-structure carry | annualised front/next basis of the linked product | `TERM_STRUCTURE` | backwardation (+) for producers |
| Sector momentum | Shenwan L1/L2 index 6-1 momentum assigned to members | `SECTOR_PANEL` | replaces stock-aggregated industry momentum |
| Sector relative strength | sector index 20-session return minus market | `SECTOR_PANEL` | |
| Macro betas (as factors) | 252-session beta to market-orthogonalised oil / gold / metals / 10y / USDCNY returns | `MACRO_PANEL`, `CONTINUOUS_PANEL` | also candidate risk descriptors (RISK_FACTOR_LIST §4b) |
| Regime variables | gold and oil 60-session momentum, term-structure state, 10y yield change | `MACRO_PANEL` | conditioning, like `VIX_PANEL.regime` |

## 6. Composite and conditioning
| Composite | Construction |
|---|---|
| Value composite | mean z of EP, BP, SP, CFP |
| Quality composite | mean z of ROE, gross margin, −accruals, −leverage, earnings stability |
| Growth composite | mean z of net profit growth, revenue growth, SUE |
| Momentum composite | mean z of 12-1 momentum, residual momentum, −1-month reversal |
| Low-risk composite | mean z of −idio vol, −beta, −turnover |
| Expectations composite | mean z of EPS revision 3M, revision breadth, target-price implied return (when `report_rc` is available) |
| Regime conditioning | `VIX_PANEL.regime` (low / normal / high / panic) as a conditioning variable for weights, not a stock factor |

## 7. Evaluation protocol (what plan 04's `FactorEvaluator` must report per factor)
IC series and mean IC / ICIR (Spearman default; 1/5/10/20/60-session horizons) **with significance**: Newey-West
t, block-bootstrap confidence intervals, Pesaran-Timmermann directional test, sub-period and regime sign
consistency, structural-break check, decay half-life; quantile ladder (10 groups, equal-weight, monthly
rebalance), long-short return and Sharpe, turnover, coverage, correlation with size and industry before and
after neutralisation. Across the whole campaign: Holm / BHY / Romano-Wolf adjusted p-values, Harvey-Liu-Zhu
t ≥ 3 hurdle, White/Hansen SPA for the best factor; for traded variants the Deflated Sharpe Ratio against the
campaign's trial log and CSCV probability of backtest overfitting. Methods, classes and the acceptance bar:
`FACTOR_TESTING_DESIGN.md` §2–§6. **Acceptance** = that design's §6 (NW t ≥ 3 and BHY p ≤ 0.05 at 20 sessions,
sign stable across sub-periods, bootstrap CI of ICIR excludes 0; DSR ≥ 0.95 and PBO ≤ 0.10 for traded variants).

## 8. Selection for plan 04 phase 4 (first six, recommendation)
EP or BP (value), ROE TTM (quality), net profit TTM yoy (growth), 12-1 momentum, 1-month reversal, turnover
(low-liquidity). Size and volatility are built with the risk model (plan 05) and shared through frames.

## 9. Data additions implied
`income_vip.revenue`, `balancesheet_vip.total_hldr_eqy_exc_min_int` added to `datasets.yaml` fields before
the next fundamentals refetch (config-only). `cyq_perf` optional (permission tier). Analyst family: `report_rc`,
`stk_surv`, `broker_recommend`, `hk_hold` (§3b; verify `report_rc` tier first).

## 10. Campaign 01 status (plan 04 phase 6, 2026-09-30; D-095)
Verdicts under FACTOR_TESTING_DESIGN §6 criteria 1–3 at h = 20, universe members 2019-01 → 2026-09, processed
values (winsorise → standardise → Shenwan L1 + log mcap neutral, D-093). Reports: lake
`derived/reports/factor_campaign_01/`; TrialLog `meta/trials/factor_campaign_01.parquet` (35 trials); notebook
`research_space/notebooks/20260930_factor_campaign_01.ipynb`. Criterion 4 (DSR, PBO, OOS) belongs to plan 06.

| Factor | Status | Mean IC | NW t | BHY p | Sub-period t (19–21 / 22–24 / 25–) | ICIR [95% CI] | Horizon profile (D-095) | Note |
|---|---|---|---|---|---|---|---|---|
| `turnover_60d` (−) | **accepted** | 0.079 | 4.85 | < 0.001 | 3.26 / 3.48 / 1.65 | 0.81 [0.64, 0.99] | rising, IC60/IC20 1.44 | criteria 1–3; criterion 4 pending plan 06 |
| `reversal_1m` (−) | **accepted** | 0.052 | 4.90 | < 0.001 | 3.19 / 3.07 / 2.12 | 0.57 [0.42, 0.72] | peak 20, half-life beyond peak ≈ 127 sessions | criteria 1–3; criterion 4 pending plan 06 |
| `score` (equal weight) | **composite-input** | 0.061 | 3.59 | 0.003 | 3.58 / 1.47 / 2.01 | 0.71 [0.53, 0.93] | rising, 1.19 | criterion 2 missed by 0.03 in 2022–24 |
| `ep_ttm` | archived at h = 20 | 0.036 | 1.86 | 0.39 | 1.51 / 1.02 / 1.00 | 0.41 [0.23, 0.60] | rising, 1.37 | neutralisation helps: raw IC 0.026 (t 0.92) → neutral 0.036 (t 1.86) |
| `roe_ttm` | archived at h = 20 | 0.017 | 0.96 | 1.00 | 0.94 / 0.21 / 1.14 | 0.22 [0.04, 0.40] | rising, 1.20 | raw IC 0.003 (t 0.09) |
| `profit_growth_ttm` | archived at h = 20 | 0.009 | 0.77 | 1.00 | 0.81 / 0.12 / 0.49 | 0.19 [0.01, 0.36] | rising, 1.04 | raw IC 0.004 (t 0.21) |
| `momentum_12_1` | archived at h = 20 | −0.005 | −0.24 | 1.00 | 0.03 / −0.06 / −0.43 | −0.05 [−0.21, 0.12] | (IC ≈ 0) | no 12-1 momentum in A-shares (reversal-dominated) |
