# research_space/runs/20261115_cgo_reproduce

Plan 29 ph1a: can a turnover-decay chip model reproduce Tushare `cyq_perf`? Question "先考虑能不能复现" (2026-11-15). Outputs in the lake under `meta/runs/research/20261115_cgo_reproduce/` (match.csv, ours_<variant>.parquet, last_variant_rows.parquet).

| File | Purpose | Contains |
|---|---|---|
| `reproduce.py` | Chips on a 400-bin log hfq grid per stock from 2010, daily decay by a × turnover, session volume spread over [low, high] (triangular at VWAP, uniform or at close); match winner rate, cost shape and mean cost against cyq_perf 2021+ on a seeded random sample; vendor grid step inferred per stock for bin-edge winner definitions | args: sample size, variant list |
