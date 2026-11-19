# research_space/runs/20261114_etf_tuning

Walk-forward Optuna (TPE) tuning of the plan 27 book (D-162); question "看看参数，然后optuna，贝恩斯优化怎么放进来？" -> "1" (2026-11-14). Outputs in the lake under `meta/runs/research/20261114_etf_tuning/` (folds.csv, oos_summary.csv, full_sample.json).

| File | Purpose | Contains |
|---|---|---|
| `walk_forward.py` | Train 2014..Y−1, test Y = 2018..2026, 200 TPE trials per fold on a robust objective (mean yearly Sharpe − 0.5 std, dd cap −12%); best and top-20 consensus picks vs fixed base; full-sample 500-trial run with deflated Sharpe and parameter importance |  |
