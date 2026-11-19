# 20261117_all_industries

Question: 搜索全部行业做loop.

Run from the repo root, in order (`uv run --env-file .env python research_space/runs/20261117_all_industries/<file>.py`). Outputs: `<lake>/meta/runs/research/20261117_all_industries/` (industries.csv, leaders.csv, shortlist.csv).

| File | Purpose |
|---|---|
| `all_industries.py` | loop over every SW L3 industry: cycle position, PB percentile, returns, median gauge, bucket A–E/N; then loop over the top-3 leaders of buckets A/B (cap ≥ 300亿): 2027E PE and revision, PB pct, gauge, winner and chip cost, oil and US 10y betas |
| `shortlist.py` | filter leaders: gauge < 0.9 veto, gauge ≤ 0.3, 2027E PE ≤ 15, no 3m cut, price ≤ chip-cost median |
| `leaders_loop.py` | same leader checks for other buckets (argv N C E), adds 2027E growth and PEG; writes leaders_NCE.csv (question: 其他行业没有机会呗) |
| `smallcap_screen.py` | stock-level small-cap screen (20–150亿, turnover ≥ 0.5亿): Q2/Q3 growth > 20%, TTM profit and OCF > 0, PE ≤ 25 or PEG ≤ 0.8, gauge veto, PB pct, chip cost; writes smallcap_screen.csv (question: 看看小盘股里的机会) |
