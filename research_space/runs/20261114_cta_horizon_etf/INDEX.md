# research_space/runs/20261114_cta_horizon_etf/

Question: 不需要调一下每个产品的 horizon 吗？可以从 ETF 上下吗？ (2026-11-14). Reads the lake only; reuses `20261114_cta_portfolio/cta_portfolio.py`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `horizon_etf.py` | A: Sharpe by lookback per sleeve and a walk-forward per-product horizon pick (2020-22 → 2023-26); B: ETF-only book at equal risk (bond-heavy); C: ETF book at 25% capital per group (A股/债券/商品/海外), long-flat, daily vs weekly; writes `horizon_*.csv`, `etf_*.csv` |  |
| `cost_check.py` | Part C at 0 / 5 / 15 / 30 bp per unit traded; writes `etf_cost_check.csv` |  |
| `beta_check.py` | Weekly beta / alpha to 沪深300 for the futures book, sleeves and ETF books; up / down beta; worst 20 weeks; ETF books on the four group hold returns; writes `beta_check.csv` |  |
| `dd_check.py` | Drawdowns of buyable ETF books at 15 bp (trend weekly, fixed mixes monthly, 510300), bootstrap, and the A股 quarter through 2015 / 2018 on index history; writes `dd_check.csv` |  |
