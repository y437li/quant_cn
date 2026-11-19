# research_space/runs/20261114_gold_us_rates

Gold (黄金ETF 518880, CNY) against US 10-year nominal and real (TIPS) yields; question "黄金也在跌 / 看一下跟美债利率的相关性？" (2026-11-14). Outputs in the lake under `meta/runs/research/20261114_gold_us_rates/` (us_tycr.csv, us_trycr.csv fetched once from Tushare; gold_us_rates.csv).

| File | Purpose | Contains |
|---|---|---|
| `gold_us_rates.py` | Weekly correlation and beta of gold returns to US 10y nominal / real yield changes, by 2-year block, rolling 52 weeks, levels now, quarterly moves 2024– |  |
| `gold_curve.py` | Gold vs the US curve: Δ 3m / 2y / 10y / 30y nominal, 10y real, breakeven, 10-2 and 30y-3m slopes; blocks, betas, regression, 4-week steepener / flattener regimes, curve now; writes `gold_curve_corr.csv` |  |
| `gold_timing.py` | Gold timing rules G0..G7 (own trend, real 10y / 2y 13-week direction, mixes) inside the plan 27 book (60/40, 5y+30y), 2014-01..2026-11; book and gold-sleeve stats by period, by year; writes `gold_timing.csv` |  |
