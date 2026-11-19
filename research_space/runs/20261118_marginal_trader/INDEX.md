# 20261118_marginal_trader

Who is the marginal trader in the 2026-08 → 11 decline: weekly margin financing balance, market-wide net flow by order size (Tushare moneyflow), turnover and index closes, read next to the national-team ETF proxy (`etf_proxy.json`). Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `margin_turn_bt.py` | event study: financing balance turning up after a ≥ 5/10/15% drawdown (5/10/20-day change) vs 中证1000 / 沪深300 forward 20 / 60 days; event list for the 10% / 5-day rule |
| `marginal_trader.py` | weekly table since 2026-08-01: financing balance and buys (亿), extra-large / large / medium / small order net (亿), average daily turnover, 沪深300 / 中证1000 / 创业板指 closes |
| `margin_turn_ma.py` | mean vs median of the 5-day rule and moving-average versions (crossing MA10 / 20 / 60 after a ≥ 10% drawdown) |
| `margin_level.py` | absolute level: financing balance vs float market cap and turnover, percentiles since 2019 and at past bottoms |
