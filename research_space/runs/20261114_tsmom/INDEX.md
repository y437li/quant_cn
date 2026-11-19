# research_space/runs/20261114_tsmom/

Question: 有没有 time series momentum (China commodity futures, 2026-11-14). Reads the lake only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `tsmom.py` | Monthly TSMOM on the 73 futures_monitor families (main contract, roll-free returns, 40% vol target), lookbacks 1/3/6/12 months, 2020-01 to 2026-10; per-family Sharpe; current signals; writes `tsmom_monthly_pnl.csv`, `tsmom12_by_family.csv`, `current_signals.csv` |  |
