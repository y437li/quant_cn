# research_space/runs/20261113_minute_factors/

Question: 分钟级数据我们有什么因子可以挖掘吗 / 试一试 (2026-11-13). Fetch needs baostock: run with `uv run --all-extras` (`--extra sources` alone re-syncs the env and drops prefect).

## Run order
1. `overnight_split.py` (daily data only)
2. `index_intraday_momentum.py` (legacy index 5-minute cache)
3. `fetch_5min.py [workers]` → `minute_features.py` → `evaluate.py 20 20` and `evaluate.py 5 5`

## Files
| File | Purpose | Contains |
|---|---|---|
| `overnight_split.py` | split each plan-04 factor's day-1 decile long-short into overnight and intraday legs | |
| `index_intraday_momentum.py` | first half-hour / mid-day return vs last half-hour return on 6 indices, 2015–2026 | |
| `fetch_5min.py` | resumable BaoStock 5-minute pull, CSI 300 + 500 members 2025-05 → 2026-11, one parquet per stock in the lake | |
| `minute_features.py` | daily stock features from 5-minute bars (realized skew/kurt, up-variance share, price-volume corr, smart money, open/close 30-min volume share and return, 5-min Amihud) | |
| `evaluate.py` | rank IC of 20-day-mean features vs open(t+1)→close(t+20), raw and net of size + existing factors; correlation with existing factors | |
