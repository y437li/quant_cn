# research_space/runs/20261114_tsmom_single/

Question: 可以对每个期货做 time series momentum 分析吗？还有个股？ (2026-11-14). Reads the lake only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `tsmom_single.py` | TSMOM asset by asset: each futures family (L = 1/3/12 months, Sharpe, t, stability 2020–22 vs 2023–26) and each SH/SZ stock 2010–2026 (own 12-1m and 1m sign, long-short / long-flat vs buy-and-hold, halves stability, pooled up-minus-down, equal-weight index timing); writes `futures_by_family.csv`, `stocks_12-1m.csv`, `stocks_1m.csv` |  |
| `decompose.py` | Stock TSMOM split into market-timing (net long share × market) and cross-sectional parts, against classic decile and rank-weighted XSMOM, 12-1m and 1m; writes `decompose.csv` |  |
