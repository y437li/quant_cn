# research_space/runs/20261114_etf_universe/

Question: 我们都有什么 ETF 可以选择 (2026-11-14). Reads the lake only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `etf_universe.py` | Listed exchange funds (fund_basic market E) with 60-session mean amount, grouped by name keywords; writes `etf_universe.csv` (premiums vs same-day NAV were checked ad hoc in the session) |  |
| `systematic.py` | Systematic exposure rules on the liquid ETF book (fixed mixes, risk parity, vol target, trend switches, plan-24 A股 position, stock-bond ERP tilt, stacks), 15 bp, 2020-02..2026-11 and halves; writes `systematic.csv`, `systematic_daily.csv` |  |
| `risk_parity_variants.py` | Risk-parity ETF book variants without leverage (gold split out, long bonds, covariance ERC, group trend on/off, plan-24 A股, half bond risk budget); writes `risk_parity_variants.csv` |  |
| `risk_budget.py` | 4-group risk budgets with A股 + 港股 merged (股票 / 债券 / 黄金 / 商品), naive and ERC, bond cap, plan-24 and trend overlays, realised risk shares; writes `risk_budget.csv` |  |
| `oil_metals.py` | Risk-budget book with oil (161129 原油 LOF) in the 商品 basket or a separate 有色 / 能源 split; with and without plan-24 A股; writes `oil_metals.csv` |  |
| `fixed_vs_rb.py` | Fixed mixes (股40/债60, 60/40, 20/80, with gold and commodities) vs risk budget 1:1:1:1, with plan-24, and at equal volatility; writes `fixed_vs_rb.csv` |  |
| `timing_by_group.py` | Trend timing on one group at a time in the risk-budget book, and each group alone hold vs trend switch; writes `timing_by_group*.csv` |  |
| `bond_stress.py` | Bond group proxy from the 中债 curve 2010-, bear episodes, hold vs trend switch, risk-budget bond weight response to vol, 2016-17 replay on today's 80% bond weight |  |
| `vol_timing.py` | Volatility timing of the total exposure on the risk-budget book (portfolio target, per-group short/long vol, Moreira-Muir 1/variance, equities only), with plan-24; writes `vol_timing.csv` |  |
| `full_scheme.py` | Full ETF scheme step by step (risk budget, plan-24 A股, bond trend switch, no 30-year, bond cap 65%) and today's ETF weights; writes `full_scheme.csv`, `full_scheme_daily.csv` |  |
| `full_scheme_long.py` | Plan 27 ph1: the ETF CTA variants ①..⑤ from 2014 on backfilled ETF history (D-159), commodity ETFs proxied by main futures before listing; sub-periods, 2015 crash, 2016-17 bond bear, 2018, by year; writes `full_scheme_long*.csv` |  |
| `duration_return.py` | Higher return / lower duration variants on the long history (5-year bonds only, no bonds, 股金商 60% + bonds 40%, bond budget 0.5 / 0.25), with today's duration and +1 pt rate shock; RAW=1 reads raw fund_daily; writes `duration_return.csv` |  |
| `split_sweep.py` | 股金商 risk budget (1−b) + 5-year bonds b with switch, b = 0..0.7, 2014-01..2026-11; writes `split_sweep.csv`, `split_sweep_daily.csv` |  |
| `no_bond_contrib.py` | Where the 100/0 (no bond) book's return comes from: group weights and contributions by year, and the book without gold |  |
| `oil_check.py` | Oil LOF 161129 in the 100/0 book: contribution by year, book without oil, stand-alone stats, premium and amount by year |  |
| `bond_mix.py` | Bond sleeves (5y, 5y+10y, 5y+30y, 5y+10y+30y, 30y, ⑤ set) at 80/20 and 60/40, bond ETFs before listing from the 中债 curve (NOPROXY=1: ETFs join when listed); writes `bond_mix.csv`, `bond_mix_daily.csv` |  |
| `param_sensitivity.py` | One-at-a-time parameter sensitivity of the plan 27 book (vol window, trend windows, vol target, bond switch, 港股 share, rebalance, budgets), 2014-01..2026-11; `book(R, cash, params)` is the objective for a later Optuna walk-forward; writes `param_sensitivity.csv` |  |
