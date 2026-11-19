# 20261119_volume_selloff

中证1000 high-volume selloff days as an add-on trigger for the small-cap watch (plan 30 ph5). Logged in `research_space/RESEARCH_LOG.md` (2026-11-19).

| File | Purpose |
|---|---|
| `selloff_bt.py` | days with 中证1000 pct_chg ≤ −3 / −4% and turnover ≥ 1.0 / 1.3 / 1.5× its prior 20-day mean (10-session de-dup), forward 5/20/60-day returns, all and with drawdown ≤ −15%; writes 20261119_volume_selloff.csv to the lake's meta/runs/research |
