# research_space/runs/20261114_cta_portfolio/

Question: 看 portfolio 的方式 — combine the 2026-11-14 sleeves (commodity trend, spread reversion, A-share index trend, bond trend) as one CTA-style book (2026-11-14). Reads the lake only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `cta_portfolio.py` | Daily net P&L per sleeve, each scaled to 10% vol (trailing 120 d), equal-risk book and leave-one-out variants, 2020-04..2026-11; writes `sleeves_daily.csv`, `portfolio_daily.csv`, `portfolio_stats.csv`, `portfolio_by_year.csv` |  |
