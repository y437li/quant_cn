# Risk Model Factor List (v0.1 draft, 2026-09-28; D-061 proposed)

Style factors and descriptors of the public Barra-family equity models, with the Tushare mapping and the sets
we adopt for plan 05. Sources: MSCI Barra CNE5 (China Equity Model, 2012, descriptor weights published in the
model handbook), MSCI CNE6 (China Equity Model, 2016; descriptor list published in the model insight, weights
not fully public), MSCI Barra USE4 (US Equity Model, 2011) as the US cross-reference. Industry factors: CNE5/6
use a 32-industry China scheme; we use Shenwan L1 (31) per RISK_MODEL_DESIGN. Descriptors are winsorised and
standardised (cap-weighted mean 0, equal-weighted sd 1) before weighting; factor = Σ w_d · descriptor_d, then
re-standardised.

## 1. CNE5 — 10 style factors, 21 descriptors (weights as published)
| Factor | Descriptor | Weight | Definition | Tushare data | Status |
|---|---|---|---|---|---|
| **Size** | LNCAP | 1.00 | ln(total market cap) | `daily_basic.total_mv` | ok |
| **Beta** | BETA | 1.00 | slope of 252-d excess-return regression on cap-weighted market, half-life 63 | `prices_adj`, universe return | ok |
| **Momentum** | RSTR | 1.00 | Σ_{t=L}^{T+L} w_t ln(1+r_t) over 504 d, half-life 126, lag L = 21 | `prices_adj` | ok |
| **Residual Volatility** | DASTD | 0.74 | sd of daily excess returns, 252 d, half-life 42 | `prices_adj` | ok |
| | CMRA | 0.16 | ln(1+max cum. return) − ln(1+min cum. return) over 12 monthly points | `prices_adj` | ok |
| | HSIGMA | 0.10 | sd of residuals from the BETA regression | derived | ok |
| **Non-linear Size** | NLSIZE | 1.00 | cube of standardised LNCAP, orthogonalised to LNCAP (weighted), winsorised | derived | ok |
| **Book-to-Price** | BTOP | 1.00 | common equity (latest) / total market cap | `balancesheet_vip.total_hldr_eqy_exc_min_int` (add), `daily_basic` | field to add |
| **Liquidity** | STOM | 0.35 | ln(Σ 21-d share turnover) | `daily_basic.turnover_rate_f` | ok |
| | STOQ | 0.35 | ln(mean of last 3 monthly STOM exp) | | ok |
| | STOA | 0.30 | ln(mean of last 12 monthly STOM exp) | | ok |
| **Earnings Yield** | EPFWD | 0.68 | forecast 12-m earnings / price (analyst consensus) | `report_rc` (tier check) | pending |
| | CETOP | 0.21 | trailing 12-m operating cash flow / price | `cashflow_vip.n_cashflow_act` TTM | ok |
| | ETOP | 0.11 | trailing 12-m earnings / price | `income_vip.n_income_attr_p` TTM, or `1/pe_ttm` | ok |
| **Growth** | EGRLF | 0.18 | long-term (3–5 y) forecast earnings growth (analyst) | `report_rc` | pending |
| | EGRSF | 0.11 | short-term (1 y) forecast earnings growth (analyst) | `report_rc` | pending |
| | EGRO | 0.24 | 5-y regression slope of annual EPS / mean |EPS| | `fina_indicator_vip.eps` (annual, PIT) | history-limited (2019+) |
| | SGRO | 0.47 | 5-y regression slope of annual revenue per share / mean | `income_vip.revenue` (add), `total_share` | field to add |
| **Leverage** | MLEV | 0.38 | (market cap + preferred + long-term debt) / market cap | `balancesheet_vip.lt_borr` (+ bonds payable, add), `daily_basic` | partial |
| | DTOA | 0.35 | total liabilities / total assets | `fina_indicator_vip.debt_to_assets` | ok |
| | BLEV | 0.27 | (book equity + preferred + long-term debt) / book equity | `balancesheet_vip` | ok |
Without analyst data the Earnings Yield and Growth weights are renormalised over the available descriptors
(CETOP 0.66 / ETOP 0.34; EGRO 0.34 / SGRO 0.66) and the factor is flagged `no_analyst` in `RISK_VALIDATION.notes`.

## 2. CNE6 — 9 factor groups, ~20 style factors, ~46 descriptors (list public, weights estimated)
| Group | Factor | Descriptors | Tushare status |
|---|---|---|---|
| Size | Size | LNCAP | ok |
| | Mid Capitalization | MIDCAP (cubic size orthogonalised; replaces NLSIZE) | ok |
| Volatility | Beta | HBETA (hist. beta, 252 d, hl 63) | ok |
| | Residual Volatility | HSIGMA, DASTD, CMRA | ok |
| Liquidity | Liquidity | STOM, STOQ, STOA, ATVR (annualised traded value ratio, 252 d, hl 63) | ok |
| Momentum | Momentum | RSTR (as CNE5), HALPHA (intercept of the beta regression) | ok |
| | Short-Term Reversal | STREV (1-m return, hl 5–10 d, lag 3 d) | ok |
| | Seasonality | SEASON (avg of same-calendar-month returns over past 5 y) | ok (2010+ prices) |
| | Industry Momentum | INDMOM (industry cap-weighted RSTR minus own, √cap weighted) | needs Shenwan (plan 05 ph1) |
| Quality | Leverage | MLEV, BLEV, DTOA | ok / partial |
| | Earnings Variability | VSAL (sd of annual sales / mean), VERN (earnings), VFLO (cash flow), ETOPF_STD (analyst dispersion) | 3 ok (history-limited), 1 pending |
| | Earnings Quality | ABS (accruals, balance-sheet), ACF (accruals, cash-flow) | ok |
| | Profitability | ATO (asset turnover), GP (gross profit / assets), GPM (gross margin), ROA | ok |
| | Investment Quality | AGRO (asset growth), IGRO (issuance growth), CXGRO (capex growth) | ok (`cip`, `fix_assets`, `total_share`) |
| Value | Book-to-Price | BTOP | field to add |
| | Earnings Yield | ETOP, ETOPF (fwd), CETOP, EM (EBITDA / EV) | 3 ok, 1 pending |
| | Long-Term Reversal | LTRSTR (−RSTR-style over 1040 d, lag 273), LTHALPHA | ok |
| Growth | Growth | EGRO, SGRO, EGIB (analyst LT growth), EGIB_S (analyst ST growth) | 2 ok, 2 pending |
| Sentiment | Analyst Sentiment | RRIBS (revision ratio), EPIBSC (fwd EPS change), EARNC (target-price / rating change) | pending (`report_rc`) |
| Dividend Yield | Dividend Yield | DTOP (trailing), DPIBS (forecast) | DTOP ok (`dv_ttm`), DPIBS pending |

## 3. USE4 cross-reference (US, 12 style factors)
Beta, Momentum, Size, Non-linear Size, Earnings Yield, Residual Volatility, Growth, Dividend Yield,
Book-to-Price, Leverage, Liquidity, **Non-linear Beta** (the only factor absent from CNE5). Descriptor
definitions match CNE5 with US data; industries 60 (GICS-based) + Country. Axioma AXUS4 adds Profitability,
Exchange-Rate Sensitivity and Short-Term Momentum. Academic public factors for sanity checks: Fama-French 5
(Mkt, SMB, HML, RMW, CMA) + UMD; AQR QMJ (quality), BAB (low beta).

## 4. Sets adopted for plan 05
| Set | Factors | When |
|---|---|---|
| **v1 (phase 2)** | Size, Beta, Momentum, Residual Volatility, Book-to-Price, Liquidity | price/turnover descriptors plus one book field; no growth/analyst dependence |
| **v2 (phase 6)** | + Non-linear Size, Earnings Yield (CETOP, ETOP; EPFWD if `report_rc`), Growth (EGRO, SGRO; analyst if available), Leverage | completes CNE5's ten |
| **v3 (later plan)** | CNE6 additions: Mid Cap, Short-Term Reversal, Seasonality, Industry Momentum, Earnings Variability, Earnings Quality, Profitability, Investment Quality, Long-Term Reversal, Dividend Yield, Analyst Sentiment | after v2 validation; each addition must not lower the bias-statistic quality and must raise adjusted R² |
Descriptor weights: CNE5 published weights for v1/v2; for v3 (CNE6, unpublished) equal weights within a factor
until the `RiskModelValidator` estimates them by regressing forward returns on descriptors (decision when done).

## 4b. Optional macro-sensitivity factors (plan 10, gated)
`OilBeta`, `GoldBeta`, `MetalsBeta`, `RatesBeta`, `CnyBeta`: 252-session (hl 63) betas of stock excess returns to
market-orthogonalised commodity / macro returns from `CONTINUOUS_PANEL` and `MACRO_PANEL`. Not in CNE5/CNE6
(Axioma-style). They enter the model only if `RiskModelValidator` shows higher adjusted R² and bias statistics
inside the band with them than without (same gate as v3). Industry factors absorb most commodity exposure; these
capture within-industry differences.

## 5. Data additions implied
`balancesheet_vip`: `total_hldr_eqy_exc_min_int`, `bond_payable`, `st_borr`; `income_vip`: `revenue`,
`operate_profit`, `oper_cost`; `cashflow_vip`: `c_pay_acq_const_fiolta` (have), `c_recp_cap_contrib`;
`report_rc` for every "pending" descriptor. All config-only plus one refetch of the 30 quarters.
