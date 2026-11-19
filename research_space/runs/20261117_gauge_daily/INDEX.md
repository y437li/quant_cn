# 20261117_gauge_daily

RetailGauge v5 read every 3rd trading day inside each quarter (2023Q1..2026Q3), to test short smoothing filters for a daily gauge. Logged in `research_space/RESEARCH_LOG.md` (2026-11-17).

| File | Purpose |
|---|---|
| `gauge_daily.py` | runs slices of 20261115_gauge_intraquarter's feature / chip / label / fit code; adds rows at day 3, 6, 9, …; walk-forward fit per as-of date (≈ 300 fits, ≈ 1 h) → `meta/runs/research/20261117_gauge_daily/gauge_daily.parquet` |
| `gauge_daily_filter.py` | scores raw vs mean of 2/3, EMA α 0.5/0.33, median of 3, and 2/3/5 readings in a row on the same side, at day 30, day 45 and pooled from day 15. Scores: holder IC, holder-fell share and quarter-end survival of the ≤0.3 group, 60-session excess of the ≤0.3 / ≥0.9 groups → `filter_summary.csv` |
| `gauge_ema_grid.py` | EMA α grid 0.1..1.0 (1.0 = raw), tuned on 2023–24 and checked on 2025–26: holder IC and ≥0.9-group 60-session excess |
