# research_space/runs/20261114_vix_vs_trend/

Question: A股 VIX 逢高买比较有参考性，看看和短期趋势信号有没有重叠 (2026-11-14). Reads the lake and volatility_monitor.json only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `vix_vs_trend.py` | 20-day realised volatility as the fear proxy (checked against the real A-share VIX 2025–26), overlap with the 10/21/42/252 trend blend, next 20/60-session returns by fear × trend, backtests of trend blend, fear-buy and both; writes `panel.csv`, `backtest.csv` |  |
| `real_vix.py` | Real A-share VIX (monitor building blocks) over the full option history from the 2026-11-14 opt_daily backfill; VIX vs realised vol, next 20/60-session return by VIX state × trend, VIX-buy rules vs trend blend; writes `vix_history.csv`, `real_vix_panel.csv`, `real_vix_results.csv` (REAL_VIX_SRC=raw / REAL_VIX_TAG for a pre-compaction run) |  |
| `vix_trend_assist.py` | Real VIX as a helper for the plan-24 position (implied-vol sizing, blow-off cut, spike cut, calm-only step-ups) on 上证50 / 沪深300 / 中证500 / 中证1000; writes `vix_trend_assist.csv` |  |
