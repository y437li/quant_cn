# 20261116_cycle_screen

Question: 现金流ETF/因子为什么差 → 对美债利率的敏感度 → 应该看其他的机会，光伏周期反转？猪肉修复会差一些 → 看看其他的弹性行业，看看value chain.

Run from the repo root: `uv run --env-file .env python research_space/runs/20261116_cycle_screen/<file>.py`. Outputs go to `<lake>/meta/runs/research/20261116_cycle_screen/`.

| File | Purpose |
|---|---|
| `cycle_screen.py` | cycle position of cyclical SW L2 / L3 industries: TTM attributable profit vs its 2018+ peak, single-quarter y/y for 2026 Q1–Q3, aggregate PB and its percentile since 2016 (current members) |
| `us10y_beta.py` | partial beta of daily returns on the US 10y yield change (Tushare `us_tycr`, prior US date), CSI 300 controlled, 1y / 2y, for held names, 中钨高新 and ETFs; book beta read from `config/local.positions.yaml` at runtime |
