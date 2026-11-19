# 20261115_gauge_intraquarter

How the RetailGauge (v5) reading moves inside a quarter, and how much a mid-quarter reading loses. Logged in `research_space/RESEARCH_LOG.md` (2026-11-15).

| File | Purpose |
|---|---|
| `gauge_intraquarter.py` | rebuild v5 features at trading day 15 / 30 / 45 and quarter end, walk-forward refit, write `gauge_paths.parquet` to `meta/runs/research/20261115_gauge_intraquarter/` |
| `gauge_intraquarter_eval.py` | stability vs quarter end, holder IC, threshold flips, 60-session forward excess from each as-of, example paths |
