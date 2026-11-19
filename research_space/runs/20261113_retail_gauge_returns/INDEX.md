# research_space/runs/20261113_retail_gauge_returns/

Question: 测一下散户温度计的预测值 — 因为我们也不知道散户的人数 (2026-11-13). Does the RetailGauge v5 prediction, known at the quarter-end close, predict returns better than the last announced holder change?

## Run order
1. `gauge_walkforward.py` (needs `uv run --all-extras --with lightgbm --with scikit-learn`; reads the prototype's feature panels in `meta/runs/holder_nowcast/`)
2. `gauge_returns.py`
3. `gauge_long_short.py`

## Files
| File | Purpose | Contains |
|---|---|---|
| `gauge_walkforward.py` | v5 expanding walk-forward predictions for every quarter 2022Q1–2026Q3 plus the 2026-11-12 nowcast; panel code copied from `research_space/prototypes/holder_nowcast/holders_v5_compare.py` | |
| `gauge_returns.py` | rank IC and deciles of the prediction vs open(d+1)→close(d+H) excess, H = 20/40/60, against the last announced change and the realised change; net of size / reversal / turnover / momentum | |
| `gauge_long_short.py` | quarterly equal-weight portfolios on the gauge decile, 60-session hold: long D1–4, short D10, index-hedged long, name turnover | |
