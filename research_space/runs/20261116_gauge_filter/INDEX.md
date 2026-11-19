# 20261116_gauge_filter

Whether smoothing the mid-quarter RetailGauge reading improves it. It reads `gauge_paths.parquet` from 20261115_gauge_intraquarter (2022Q1..2026Q3, day 30 and day 45). Logged in `research_space/RESEARCH_LOG.md` (2026-11-16).

| File | Purpose |
|---|---|
| `gauge_filter.py` | compares five forms: raw, quarter-to-date mean, mean incl. last quarter-end, 0.7/0.3 blend, two readings in a row on the same side. Scores holder IC, the share of the ≤0.3 group whose holder count fell, survival to the quarter-end reading, and 60-session excess of the ≤0.3 / ≥0.9 groups → `meta/runs/research/20261116_gauge_filter/filter_summary.csv` |
