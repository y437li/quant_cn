# Fresh Start — Data & API Handbook

Everything needed to rebuild the A-share dataset from scratch, **without** the old
`data/market_data.sqlite`. Distilled from the old project's downloaders
(`scripts/data/*.py`, `src/data/fetcher.py`) and the data problems it already hit.

| File | What's in it |
|---|---|
| [TUSHARE_API.md](TUSHARE_API.md) | How to call Tushare: auth, request/response format, paging, rate limits, a minimal client, and every endpoint with its parameters |
| [DATA_CATALOG.md](DATA_CATALOG.md) | Every dataset: key, fields, units, which date makes it "known" (point-in-time), how much history the old project had, known traps |

## Where to start

1. Put your token in an env var: `export TUSHARE_TOKEN=...` (never hard-code it — see note below).
2. Copy the ~40-line client from [TUSHARE_API.md §4](TUSHARE_API.md#4-minimal-client-stdlib-only).
3. Download in this order (each step depends on the previous one):
   1. `trade_cal` → the trading-day calendar that drives every date sweep
   2. `stock_basic` with `list_status` L, D **and** P → full universe (avoids survivorship bias)
   3. Daily market data by `trade_date`: `daily`, `adj_factor`, `daily_basic`, `moneyflow`, `stk_limit`
   4. Fundamentals by `period`: `fina_indicator_vip`, `income_vip`, `balancesheet_vip`, `cashflow_vip`
   5. Anything else from the catalog you need

## Five rules the old project learned the hard way

1. **Sweep by date, not by stock.** One `daily(trade_date=...)` call returns the whole market (~5.5k rows).
   Per-stock loops need ~5,000× more calls.
2. **Include delisted stocks.** `stock_basic(list_status='D')` and `'P'`, or backtests only see survivors.
3. **Align fundamentals by `f_ann_date`/`ann_date`, never `end_date`.** The report is published on average
   ~59 days (max 860) after the period ends. Using `end_date` is look-ahead.
4. **Fetch `adj_factor`.** `daily` prices are unadjusted. The old project never downloaded it and
   rebuilt adjusted prices from `pct_chg` instead.
5. **Make downloads resumable.** Log each finished (endpoint, date) key so a crash just resumes.

## Security note

The old repo has the Tushare token and Gemini/DeepSeek API keys hard-coded and committed in
`src/common/config.py` and several `scripts/data/*.py` files. Consider rotating them, and keep
the new project's keys in environment variables or an untracked `.env`.
