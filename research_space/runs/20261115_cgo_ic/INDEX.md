# research_space/runs/20261115_cgo_ic

Plan 29 ph1b: does capital gains overhang (CGO) predict A-share returns beyond reversal, momentum, turnover and size? Plan approved 2026-11-15 ("ok"). Outputs in the lake under `meta/runs/research/20261115_cgo_ic/` (ic.csv, deciles_20d.csv, corr.csv, panel.parquet, run.log).

| File | Purpose | Contains |
|---|---|---|
| `cgo_ic.py` | Turnover-decay mean cost from 2010 (tri / close × a 1 / 1.5), \|CGO\|, our 400-bin winner rate and the vendor winner rate; month-end rank IC 2019-01..2026-10 on derived/universe, raw and net of size, reversal_1m, reversal_intraday_1m, momentum_12_1, turnover_60d; NW t, three sub-periods, CGO deciles, rank correlations |  |
| `long_only.py` | Follow-up "用这个反过来买呗": CGO / \|CGO\| deciles raw and net of controls, long-only books (low \|CGO\|, deep loss, score top 20% with high-CGO names removed) | reads panel.parquet; writes long_only.csv |
| `short_side.py` | Follow-up "我的意思是要short": short the top-10% CGO (raw and net) among all / 两融标的 / names with 融券余量, hedged by the universe; borrow 8%/yr and 0.15% one-way costs; by year | reads panel.parquet; writes short_side.csv, short_side_by_year.csv |
