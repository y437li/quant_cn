# 20261115_watch_conditions_bt

Question: 回测一下这组条件 (2026-11-15): do the watchlist buy conditions (RetailGauge ≤ 0.3, large-order weeks positive in the last 4) add return?

| File | Purpose |
|---|---|
| `watch_conditions_bt.py` | quarter-end event study 2022Q1–2026Q3, float cap ≥ 50亿, PIT walk-forward gauge, 20/60/120-session excess vs universe mean, per-quarter differences; panel → `meta/runs/research/20261115_watch_conditions_bt/panel.parquet` |
| `chip_score_bt.py` | backtest of the composite chip score (top 50, quintiles, component rank ICs) |
| `band_controls_bt.py` | 70% cost-band (dispersion) edge under controls: prior return, volatility, turnover, size, overhead; double sorts + Fama-MacBeth |
| `hs300_benchmark.py` | same results re-expressed vs CSI 300 (000300.SH price index) instead of the equal-weight universe |
| `walkforward_opt.py` | walk-forward threshold search (gauge, band, overhead) vs fixed gauge ≤ 0.3; in-sample vs out-of-sample gap |
