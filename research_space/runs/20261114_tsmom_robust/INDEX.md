# research_space/runs/20261114_tsmom_robust/

Question: 敏感性检验和交易成本；指数期货或者 ETF 层面呢？ (2026-11-14). Reads the lake only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `tsmom_robust.py` | Commodity TSMOM grid (lookback × vol window × cap, gross and net), spread z-reversion grid (window × cap × entry, net of leg costs), TSMOM on 7 A-share indices since 2011, SW L1 industries, CFFEX index and bond futures and 104 liquid ETFs since 2020 against a vol-scaled always-long benchmark; writes `a1_commodity_grid.csv`, `a2_spread_grid.csv`, `b1_indices.csv`, `b2_sw_l1.csv`, `b3_cffex.csv`, `b4_etfs.csv`, `b4_etf_each.csv` |  |
| `avoid_drawdown.py` | 12-month trend rule (hold or cash) on 沪深300 / 中证500 / 中证1000 / 创业板指 since 2011: max drawdown, returns in 2015, 2018, 2021–24 declines and 2019, 2024 rebounds; writes `avoid_drawdown.csv` |  |
| `vol_sizing.py` | 12-month trend rule plus volatility sizing (target 20%, ≤ 100%, daily) with EWMA 60 / 10, rolling 20 / 60 days, Parkinson 20 days and GARCH(1,1) fitted on 2010–2012, on four indices 2013–2026; writes `vol_sizing.csv` |  |
| `crash_check.py` | Position of the trend + volatility rule on day 1 of seven sudden A-share crashes (2015 ×2, 2016 熔断, 2018-10, 2020-02, 2024-01/02, 2025-04) for 沪深300 / 中证1000, and first-5-day and whole-window losses; writes `crash_check.csv` |  |
| `signal_lag.py` | Months from a ≥ 20% decline's peak until the 1/3/6/12-month signal turns down (and drawdown by then), and from the trough until it turns up (rebound missed), 4 indices since 2011; writes `signal_lag.csv` |  |
| `trend_rules.py` | Daily trend rules on 4 indices 2011–2026: TS 1/3/6/12 months, multi-lookback average, MA200, MA50/200, MA200±2%%, each with and without volatility sizing; returns, drawdowns, trades, episodes; writes `trend_rules.csv`, `trend_rules_episodes.csv` |  |
| `short_trend_check.py` | Robustness of the short trend rule: n = 5..252 sessions, halves 2011–18 / 2019–26, costs 5/15/30 bp, per index, ETFs vs index since 2020, blends 10/21/42(/252) with vol sizing; writes `short_trend_check.csv`, `short_trend_etf.csv` |  |
