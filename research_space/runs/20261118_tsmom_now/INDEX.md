# 20261118_tsmom_now

Current time-series momentum across liquid exchange ETFs: which ones are in an up or down trend now. Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `realized_vol.py` | 10/20/60/250-day realised vol of the option ETFs vs volatility_monitor implied VIX |
| `bottom_base_rate.py` | 中证1000 episodes with drawdown ≤ −30% and RV20 in the top 15%: forward returns and further falls |
| `breadth_volume.py` | last 25 sessions: advancers / decliners, > 5% movers, limit-downs / ups, market turnover vs 60 / 250-day medians |
| `scan.py` | ETFs with 20-day mean turnover ≥ 3亿, one per benchmark: 1/3/6/12-month returns, plan-24 blend (10/21/42/252 sessions up), 60-day vol, 12m return / vol, gap to the 52-week high; writes tsmom_now.csv to the lake's meta/runs/research/20261118_tsmom_now |
