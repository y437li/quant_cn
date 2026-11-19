# research_space/runs/20261114_mean_reversion/

Question: 跑一下方差比和价差半衰期 (trend vs mean reversion in China commodity futures, 2026-11-14). Reads the lake only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `mean_reversion.py` | Lo-MacKinlay variance ratios (k = 5/21/63/126/252 days, robust z) for 64 futures_monitor families since 2020; AR(1) half-life, ADF p and current z for the futures_monitor spreads plus PP − 3×MA; writes `variance_ratios.csv`, `spread_half_life.csv` |  |
| `out_of_sample.py` | Out-of-sample check: VR class formed 2020–22 vs 2023–26 (stability, TSMOM by class, regime-aware book); rolling 1-year z-score spread reversion backtest; writes `spread_zscore_backtest.csv` |  |
| `references.md` | Literature for TSMOM, variance ratios and spread reversion, checked online |  |
| `mop2012_reading_note.md` | 中文读书笔记：Moskowitz, Ooi & Pedersen (2012) Time Series Momentum — data, formulas, results, TSMOM vs XSMOM decomposition, speculators vs hedgers, links to our runs |  |
