# 20261119_margin_share

融资余额 / 流通市值 since 2019 and its level at 中证1000 bottoms. Logged in `research_space/RESEARCH_LOG.md` (2026-11-19).

| File | Purpose |
|---|---|
| `margin_share_history.py` | Σ margin_detail rzye / Σ daily_basic circ_mv per session (days under 90% of the 20-day median stock count dropped), yearly range, share at six 中证1000 bottoms and its low within ±30 sessions; writes 20261119_margin_share.csv to the lake's meta/runs/research |
| `margin_share_long.py` | monthly 融资余额 / 流通市值 since 2010 from Tushare margin + daily_info (SZ_MARKET minus fund / bond rows), checked against the 2019+ series (mean diff 0.04 pp); writes 20261119_margin_share_long.csv |
