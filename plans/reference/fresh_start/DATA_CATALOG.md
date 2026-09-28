# Data Catalog

What each dataset is, how to key it, when it becomes knowable, and what went wrong with it before.
For how to download each one, see [TUSHARE_API.md §5](TUSHARE_API.md#5-endpoint-reference).

"Old coverage" = what `data/market_data.sqlite` held as of 2026-08-28. It's a guide to how much
history is realistic to pull, not something the new project reads.

---

## 1. Summary

| Dataset | Endpoint | Primary key | "Known on" date (PIT) | Old coverage | Old rows |
|---|---|---|---|---|---|
| Trading calendar | `trade_cal` | `cal_date` | — | (not stored) | — |
| Universe | `stock_basic` | `ts_code` | `list_date` / `delist_date` | snapshot, L+D+P | 5,890 |
| Name history | `namechange` | `ts_code, start_date` | `ann_date` | full | 13,827 |
| Daily bars | `daily` | `ts_code, trade_date` | `trade_date` close | 2010-01-04 → 2026-08-28 | 14.3 M |
| Adj. factor | `adj_factor` | `ts_code, trade_date` | `trade_date` | **never fetched** | — |
| Valuation / size | `daily_basic` | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-08-28 | 8.8 M |
| Money flow | `moneyflow` | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-08-28 | 8.6 M |
| Limit prices | `stk_limit` | `ts_code, trade_date` | before open on `trade_date` | 2019-01-02 → 2026-08-28 | 11.1 M |
| Chip distribution | `cyq_perf` | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-08-28 | 8.7 M |
| Margin | `margin_detail` | `ts_code, trade_date` | `trade_date` | 2019-01-02 → 2026-08-28 | 5.4 M |
| Index bars | `index_daily` | `ts_code, trade_date` | `trade_date` close | 2010-01-04 → 2026-08-28, 7 indices | 28 k |
| Financial indicators | `fina_indicator_vip` | `ts_code, end_date` (+ `ann_date` for restatements) | `ann_date` | 2017Q1 → 2026Q2 | 352 k |
| Income | `income_vip` | `ts_code, end_date, report_type` | `f_ann_date` | 2016Q1 → 2026Q2 | 213 k |
| Balance sheet | `balancesheet_vip` | `ts_code, end_date, report_type` | `f_ann_date` | 2016Q1 → 2026Q2 | 209 k |
| Cash flow | `cashflow_vip` | `ts_code, end_date, report_type` | `f_ann_date` | 2016Q1 → 2026Q2 | 213 k |
| Earnings guidance | `forecast` | `ts_code, end_date, ann_date` | each row's own `ann_date` | 2016Q1 → 2026Q2 | 75 k |
| Preliminary results | `express` | `ts_code, end_date, ann_date` | `ann_date` | 2016+ | 18 k |
| Disclosure schedule | `disclosure_date` | `ts_code, end_date` | `ann_date` (for plan), `actual_date` | 2023+ | 74 k |
| Insider trades | `stk_holdertrade` | `ts_code, ann_date, holder_name, in_de, change_vol` | `ann_date` | 2019+ | 94 k |
| Lock-up expiries | `share_float` | `ts_code, float_date, holder_name` | `ann_date` | 2018 → ~2035 | 13 k |
| Shareholder count | `stk_holdernumber` | `ts_code, end_date` | `ann_date` | 2018Q1+ | 162 k |

Rough size: one full-market daily table since 2019 ≈ 9 M rows ≈ 400–600 MB as zstd parquet.

## 2. Units (Tushare conventions — easy to get wrong)

| Field | Unit |
|---|---|
| `daily.vol` | 手 (lots of 100 shares) |
| `daily.amount` | 千元 (thousand CNY) |
| `daily_basic.total_mv`, `circ_mv` | 万元 (10k CNY) |
| `daily_basic.total_share`, `float_share`, `free_share` | 万股 (10k shares) |
| `daily_basic.turnover_rate*`, `pct_chg`, `dv_ratio` | percent (1.5 = 1.5%) |
| `moneyflow.*_amount` | 万元 |
| `moneyflow.*_vol` | 手 |
| Financial statement amounts | 元 (CNY) |

Verify any unit you rely on against the endpoint's doc page before building on it.

## 3. Traps (all hit by the old project)

### Look-ahead in fundamentals
- **Never align financial data on `end_date`.** Reports come out a mean of **58.9 days** (max **860**)
  after the period ends. Make a row visible from `f_ann_date` (first announcement) or `ann_date`,
  and only from the **next trading day** if the announcement may be after the close.
- Restatements: the same `(ts_code, end_date)` can appear again with a later `ann_date` and
  `update_flag=1`. Keep every version; at date *t* use the latest version with `ann_date <= t`.
- **Forecast revisions**: a revised forecast (`update_flag=1`) is only public on its own `ann_date`.
  Using `first_ann_date` for it moves the revision 1–2 months early.
- Never merge statements on `ts_code` alone — always include `end_date` (the old project produced
  cartesian products across periods this way).
- `report_type`: `1` = consolidated, the one you normally want. Filter on it before de-duplicating.

### Universe
- **Survivorship bias**: fetch `stock_basic` with `L`, `D` and `P`. Delisted stocks still have
  historical bars in `daily`; backfill them.
- Use `namechange` to know when a stock was ST/*ST (names starting with `ST` / `*ST`).
- Beijing exchange (`.BJ`) and newly listed stocks have different limit rules; filter deliberately.

### Prices & trading
- `daily` is **unadjusted**. Fetch `adj_factor` for back-adjusted prices. (`pct_chg` is computed
  against an adjusted `pre_close`, so cumulating it also works — that's what the old project did.)
- Suspended days have **no row** — reindex against `trade_cal` if you need a dense panel.
- Limit-up/down: use `stk_limit` to decide whether a fill was even possible.
  A board-prefix guess (10%/20%/30%) missed 33.5% of one-word limit-ups and 63.1% of limit-downs.
- Features computed at close of day *T* can only trade at open of *T+1*.

### Event data
- `stk_holdertrade`: `ann_date` is the only date exposed and the correct one. Don't join in the
  actual trade date from elsewhere.
- `share_float`: future `float_date`s are **not** look-ahead — the schedule is announced in
  advance (`ann_date`). Filter on `ann_date <= t`.
- Some event data (e.g. surveys) is published a day or two after the event date; assume
  `event_date + 2 trading days` when unsure.

### Operational
- Rate-limit errors are normal on long sweeps — retry after ~65 s.
- `share_float` ignores `offset`; page by month.
- The old volume/disk silently corrupted `.venv` and `.git`. Keep downloaded data somewhere
  reliable and back it up; the raw data is expensive (days) to re-pull.

## 4. Storage suggestion for the new project

The old project ended up with SQLite as a landing zone plus a parquet copy for analysis. Simpler for
a fresh start: write straight to **parquet**, one folder per dataset, partitioned by year:

```
data/<dataset>/year=YYYY/part.parquet     # daily tables, partitioned on trade_date
data/<dataset>.parquet                    # small tables (stock_basic, namechange, ...)
```

Keep all date columns as `YYYYMMDD` strings (same as the API) so joins never hit type mismatches.

Existing parquet exports in the old repo (`data/parquet/`: `klines_daily`, `daily_basic`,
`moneyflow`, `index_daily`, `stock_basic_full`) use this layout, if you want to reuse them
rather than re-download.
