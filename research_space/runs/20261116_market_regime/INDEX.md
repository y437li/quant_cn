# 20261116_market_regime

Is the market trending or range-bound, how deep are the drawdowns, and how a long-1000 / short-300 pair would have fared. Logged in `research_space/RESEARCH_LOG.md` (2026-11-16).

| File | Purpose |
|---|---|
| `regime_snapshot.py` | broad ETFs: 5 / 20 / 60-day and YTD returns, drawdown from the 250-day high, position vs 20 / 60 / 120-day averages, efficiency ratio (trend straightness) and its percentile, up-day share; all-stock breadth |
| `drawdowns.py` | 中证1000 / 沪深300 largest drawdowns since 2015 and by year since 2019; worst point after each vol-gap entry, long-only and as a long-1000 / short-300 pair |
| `capitulation_check.py` | margin balance, market turnover, limit-down / limit-up counts since 2026-10 vs past panic lows |
| `low_volume_bottom.py` | 地量见地价 test: market turnover / float cap, 20-day mean at a 1-year low or bottom 10% of 3 years, forward 沪深300 / 中证1000 returns and drawdown still to come; turnover at past lows |
| `bottom_types.py` | past 中证1000 major lows (≥ 20% down, ≥ 15% rally within 60 days) typed as 恐慌底 / 地量底 / 混合 by limit-downs and turnover, with vol, margin and breadth; today's reading on the same features |
| `bottom_signals_bt.py` | backtest of panic (≥ N limit-downs, ≥ 70% at 60-day lows) and drought (turnover bottom 10-20% of 3 years, vol ≤ 25, ≥ 15% down) signals as 中证1000 buy rules: 5 / 20 / 60 / 120-day returns, worst points, near-the-low rate |
| `breadth_thrust_bt.py` | confirmation signals for bottoms without a panic day: breadth thrust (> 60 / 70% above MA20 within 10 days of < 20%) and 中证1000 back above its 60-day average after ≥ 15% down; returns, worst points, cost above the 60-day low |
| `panic_in_bear.py` | panic-day buys inside the 2021-12..2024-02 bear market and the 2025-04 tariff crash: peak within 250 days, 250-day return, later undercuts; calendar-year returns |
