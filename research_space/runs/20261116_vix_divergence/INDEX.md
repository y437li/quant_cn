# 20261116_vix_divergence

Gap between small-cap / tech and large-cap A-share VIX, its history and what followed. Logged in `research_space/RESEARCH_LOG.md` (2026-11-16).

| File | Purpose |
|---|---|
| `vix_divergence.py` | full option-history VIX lines via VolatilityMonitorBuilder; 中证1000−300 and 科创50−50 gaps, percentiles, next 5 / 20-day ETF returns by gap bucket |
| `realized_gap.py` | 2016–2026 test with the realized-vol gap (中证1000 − 沪深300, 20-day): buckets, era split, distinct episodes, a 300/1000 switching rule; implied vs realized gap correlation |
| `realized_gap_horizons.py` | the same gap at 20 / 40 / 60 / 120 / 250 sessions: buckets, distinct episodes (≥ 20 sessions apart), a hold-H switching rule |
| `exit_rules.py` | exit rules for a 中证1000 position bought at a 90th-percentile gap: fixed 20 / 60 / 120 days, gap percentile back below 50% / 70%, combined with 60 days, each with and without a −10% stop; live gap thresholds |
| `high_vol_entry.py` | buy 中证1000 / 科创50 when their own realized vol (3-year pct) or option VIX (history pct) is ≥ 90%: per-episode 20 / 60 / 120-day returns and worst point within 60 days |
| `joint_signal.py` | 中证1000 buy points where two volatility conditions hold together (own realized vol + gap, own realized vol + option VIX) vs each alone: per-episode returns and the exit-rule result |
