# research_space/notebooks/

Dated one-off notebooks, `YYYYMMDD_<topic>.ipynb`; each row states the question it answers.

## Files
| File | Purpose | Contains |
|---|---|---|
| `20260927_vix_calculation.ipynb` | CBOE-method VIX for all 12 equity-option underlyings (SSE/SZSE ETFs, CFFEX indices), latest value for the 300 family, four checks | method, checks 1-4, 300-family chart |
| `20260929_positioning_flows.ipynb` | Where forced or mechanical flows concentrate for CSI 300 (plan 09): dealer gamma by strike, index-futures OI regime and top-20 broker net, margin-financing liquidation ladder | data reconciliation, gamma map and flip, futures regimes, margin ladder |
| `20260930_lake_coverage.ipynb` | Plan 11 phase 9: every lake dataset with source, known-on rule, first/last date and rows; start-date and per-call-cap checks; release-lag and cross-source quality results; derived digests | coverage table, late starts, cap scan, release lags, quality views, digests |
| `20260930_factor_campaign_01.ipynb` | Plan 04 phase 6: factor campaign 01 (six library factors + composite score, 2019-01 onward) read from derived/reports; FACTOR_TESTING_DESIGN §6 verdicts at h = 20; D-095 horizon profiles; raw vs neutralised IC for the fundamentals | verdict table, ICIR bars, IC by horizon, rolling IC, quantile ladders, raw vs neutral IC |
| `20261111_risk_model_validation.ipynb` | Plan 05: the A-share Barra model (`cne5_v2_spx`, real lake run 24e0c12dfcdb) read from derived/risk_* and its validation report; acceptance, factor and benchmark bias, R² by year, style factor returns, correlations, CSI 300 attribution and CSI 500 active risk | acceptance, factor bias, R² and factor returns, correlation heatmap, attribution |
