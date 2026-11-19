# 20261118_gauge_risk_style

Plan 21 phase 6: the 散户温度计 RetailGauge as a candidate risk style (`retail_crowding`) next to the fitted cne5_v4 model, and as a score input. Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `gauge_style_fit.py` | daily 2022-06 → latest: the model's constrained WLS rerun on the stored exposures with retail_crowding added (FactorReturnEstimator.compute_monitor; the base R² matches the model): share of days \|t\| > 2, vol, mean return, bias, R² gain, correlation with the styles, by year |
| `score_tests.py` | month ends 2022-06 → last full month: score vs score + retail_gauge factor (IC 20 / 60, decile LS), and the score's style-residual IC20 with and without retail_crowding; all and large caps |
