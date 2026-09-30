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

### 1b. Datasets added by the new project (lake coverage as of 2026-09-28)

| Dataset | Endpoint | Primary key | "Known on" date (PIT) | Lake coverage | Rows | Decision |
|---|---|---|---|---|---|---|
| Shenwan 2021 tree | `index_classify` (`src=SW2021`) | `index_code` | — (reference) | L1 31, L2 134, L3 346 | 511 | D-068 |
| Shenwan membership | `index_member_all` (`is_new` Y + N) | `ts_code, l3_code, in_date` | `in_date` (member while `in_date <= d < out_date`) | in_date 1984 → 2026-09-24 | 7,920 | D-068 |
| Index weights | `index_weight` (300/500/1000/50) | `index_code, con_code, trade_date` | `trade_date` (month-end snapshot) | 2010-01-29 → 2026-08-31 | 313 k | D-069 |
| Shenwan index bars | `sw_daily` | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-09-28, 439 indices | 930 k | D-068 |
| Option contracts | `opt_basic` (SSE/SZSE/CFFEX) | `ts_code` | `list_date` | listed 2015-02-09 → 2026-09-24 | 31 k | plan 03 |
| Option bars | `opt_daily` | `ts_code, trade_date` | `trade_date` close | 2026-08-03 → 2026-09-28 | 1.03 M | plan 03 |
| SHIBOR | `shibor` | `date` | `date` (11:00 fixing) | 2015-01-04 → 2026-09-28 | 2,907 | D-070 |
| Exchange fund bars | `fund_daily` (all ETFs/LOFs, by date) | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-09-28 | 2.21 M | D-074 |
| Exchange fund list | `fund_basic` (`market=E`) | `ts_code` | `list_date` | 2,961 funds (L 2,238 / D 677) | 2,961 | D-074 |
| Fund NAV | `fund_nav` (`market=E`, by `nav_date`) | `ts_code, nav_date` | next session after `nav_date` | 2019-01-02 → 2026-09-28 | 2.33 M | D-074 |
| Fund shares | `fund_share` (by date) | `ts_code, trade_date` | next session after `trade_date` | 2019-01-02 → 2026-09-28 | 1.67 M | D-074 |
| Margin-eligible list | `margin_secs` (SSE/SZSE/BSE) | `trade_date, ts_code` | `trade_date` (before the open) | 2019-01-02 → 2026-09-28 | 6.50 M | D-074 |
| Futures bars (6 exchanges) | `fut_daily` | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-09-28 | 1.65 M | D-077 |
| Futures contracts | `fut_basic` (6 exchanges) | `ts_code` | `list_date` | listed 1995 → 2026 | 11,287 | D-077 |
| Main / continuous mapping | `fut_mapping` | `ts_code, trade_date` | `trade_date` | 2019-01-02 → 2026-09-28 | 312 k | D-077 |
| SGE spot contracts | `sge_basic` | `ts_code` | — (reference) | 13 contracts | 13 | D-077 |
| SGE spot bars | `sge_daily` | `ts_code, trade_date` | `trade_date` close | 2019-01-02 → 2026-09-28 | 53 k | D-077 |
| Futures top-20 holdings | `fut_holding` (all exchanges) | `trade_date, exchange, symbol, broker` | `trade_date` evening | 2019-01-02 → 2026-09-28 | 15.2 M | D-076, D-077 |
| CPI | `cn_cpi` | `month` | month end + 12 days (next session on/after) | 2015-01 → 2026-08 | 140 | D-080 |
| PPI | `cn_ppi` | `month` | month end + 12 days | 2015-01 → 2026-08 | 140 | D-080 |
| PMI (NBS) | `cn_pmi` | `MONTH` | month end + 1 day | 2015-01 → 2026-08 | 140 | D-080 |
| Money supply | `cn_m` | `month` | month end + 15 days | 2015-01 → 2026-08 | 140 | D-080 |
| LPR | `shibor_lpr` | `date` | `date` (09:15 fixing) | 2015-01-04 → 2026-08-20 | 1,234 | D-080 |
| FX, metals, CFDs (FXCM) | `fx_daily` (14 codes) | `ts_code, trade_date` | next session after `trade_date` | FX/metals 2015 →, CFDs 2022-07 → 2026-09-28 | 27 k | D-080 |
| Analyst forecasts | `report_rc` (by `report_date`, all days) | `ts_code, report_date, org_name, report_title, quarter` | next session after `report_date` | 2019-01-01 → 2026-09-28 | 1.72 M | D-081 |
| Investor visits | `stk_surv` (all days) | `ts_code, surv_date, rece_org, fund_visitors` | **surv_date + 2 sessions** (rule, conservative: no disclosure date) | 2021-08-05 → 2026-09-28 | 905 k | D-081, D-082 |
| Broker monthly picks | `broker_recommend` | `month, broker, ts_code` | **month start (rule `period_start_lag` 0, not an observed date)** | 2020-03 → 2026-09 | 18 k | D-081 |
| Stock Connect holdings | `hk_hold` (all days) | `code, trade_date, exchange` | next session after `trade_date` | 2019-01-02 → 2026-09-28 | 5.76 M | D-081, D-082 |
| Earnings guidance | `forecast_vip` (by period, all versions) | `ts_code, end_date, ann_date, update_flag` | `ann_date` | ann 2018-12-28 → 2026-08-24 | 48 k | D-081 |
| Preliminary results | `express_vip` (by period, all versions) | `ts_code, end_date, ann_date, update_flag` | `ann_date` | ann 2019-04-10 → 2026-08-25 | 12 k | D-081 |
| Insider trades | `stk_holdertrade` (all days) | none (exact duplicate rows dropped) | `ann_date` | 2019-01-02 → 2026-09-28 | 119 k | D-081 |
| Lock-up expiries | `share_float` (by `ann_date`, all days) | `ts_code, ann_date, float_date, holder_name, share_type` | `ann_date` | ann 2016-01-01 → 2026-09-28 | 6.66 M | D-081 |
| Disclosure schedule | `disclosure_date` (param `end_date`) | `ts_code, end_date` | `ann_date` (latest schedule, not PIT) | periods 2019 → 2026Q2 | 145 k | D-081 |
| Shareholder count | `stk_holdernumber` (param `enddate`) | `ts_code, end_date, ann_date` | `ann_date` | ann 2016-07 → 2026-08 | 153 k | D-081, D-082 |
| Derived: futures holdings | `derived.fut_holding_brokers` | `trade_date, exchange, symbol, broker` | as `fut_holding` | contract rows, no category totals | 13.65 M | D-079 |
| Derived: one-sided futures | `derived.fut_daily_one_sided` | `ts_code, trade_date` | as `fut_daily` | vol/amount/oi halved pre-2020 (SHF/DCE/ZCE/INE) | 1.65 M | D-079 |
| Derived: Shenwan L1 intervals | `derived.industry_l1` | `ts_code, valid_from` | `valid_from` (back-filled rows flagged) | 1984 → open | ~10 k | D-071 |
| Margin totals | `margin` | `trade_date, exchange_id` | `trade_date` (published next morning) | 2025-01-02 → 2026-09-28 | 1,266 | plan 09 |
| Margin by stock | `margin_detail` | `ts_code, trade_date` | `trade_date` (published next morning) | 2024-01-02 → 2026-09-28 | 2.73 M | plan 09 |

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

## 3b. Traps found in the 2026-09 rebuild (added by the new project)

- **Code changes double-list a company.** Tushare keeps the retired code's bars *and* back-fills the same
  history under the new code (000043→001914, 000022→001872, 300114→302132: identical closes on 7,637 bars).
  `curated.daily` keeps both; `derived.prices_adj` / `LakeQuery.read_prices` keep only codes present in
  `stock_basic` (D-053). A backtest must never read `curated.daily` directly. An old→new alias map is planned
  (plan 04) so the old code's full history and limits can be attached to the surviving code.
- **Beijing exchange history.** `daily` includes NEEQ-era bars for `.BJ` stocks (58k bars) that have no
  `stk_limit` or `daily_basic`. Exclude `.BJ` from backtest universes or start each at its BJ `list_date` (D-054).
- **001914.SZ** has 221 bars in 2019 without `stk_limit`; the limits sit under the old code 000043.
- **Moves above 31%** on ~150 SH/SZ bars after a stock's first five sessions are resumptions after long
  suspensions, not errors; `stk_limit` does not apply on the resumption day for some regimes.
- **`stock_basic(list_status='P')`** returned empty in 2026-09: no currently paused listings; keep requesting it.
- **Tushare row caps.** `shibor` returns at most 2,000 rows per call and does not page (lake silently started
  2018-08 instead of 2015; D-070). Paged endpoints refuse `offset > 100000` (`index_weight` for CSI 1000 since 2014;
  D-069). Sweep long ranges by yearly `date_window`; treat a round-number row count as truncated until checked.
- **Shenwan 2021 history is reconstructed.** The scheme was published in 2021-07; earlier `in_date`s are vendor
  back-fills, and ~2% of listed SH/SZ stocks have no membership before their first record (36 of 49 such stocks on
  2019-06-28 start exactly at 2021-07, the rest at a July annual review). 0 unmapped on 2026-09-24. Grouping before
  2021-07 is usable but not PIT (D-068).
- **`sw_daily` weighting.** Member returns weighted by previous-day free-float cap (`close × free_share`) match the
  Shenwan L1 indices within 2.5 bp median, 90% of L1-days within 10 bp, 98% within 25 bp (2024–2026); weighting by
  `circ_mv` is off by 9.5 bp median. Shenwan uses tiered free-float weights.
- **Fund fields that look useful but are empty.** `fund_share.fund_type` is mostly NULL before 2026 (0 "ETF" labels
  at end-2019, 1,686 at 2026-09): identify ETFs by `fund_basic.name LIKE '%ETF%'` (269 at end-2019 → 1,705 at
  2026-09-28). `fund_nav.net_asset` / `total_netasset` are filled on ~1–2% of rows: size an ETF as `fd_share` (万份)
  × 1e4 × `unit_nav`. Close vs NAV: 98–99% of ETFs within 2%, median |premium| ~10 bp; 510300.SH median −4.3 bp.
- **`margin_secs` SSE history is frozen.** The SSE list has exactly 1,956 names from 2019-01 to 2024-03 apart from
  one-day blips (SZSE grows 819 → 2,105 over the same years), so SSE eligibility before 2024-04 is not reliable; use the
  official exchange lists (plan 11 phase 10). On a holiday the endpoint returns the SSE list only.
- **Holidays in date checks.** A by-date call on a non-session (2026-09-25, Mid-Autumn) returns 0 rows or a partial
  list; always check against `trade_cal` before calling a result "missing".
- **Commodity OI and volume were two-sided before 2020.** SHFE, DCE, CZCE (and INE) reported `oi` and `vol` as
  long + short until 2019-12-31 and one-sided from 2020-01-02 (CU2003.SHF oi 210,762 → 111,621 overnight;
  M2005.DCE 3.39 M → 1.68 M); CFFEX was always one-sided. Halve pre-2020 commodity `oi`/`vol` before comparing
  across the break (top-20 coverage looks like ~30% in 2019 and ~60–70% after for this reason alone).
- **`fut_holding` mixes category totals with brokers.** Rows whose `broker` is a member category, not a firm:
  CFFEX `期货公司` / `非期货公司` (to 2020-03), `非期货公司结算会员` (2020-09 → 2023-04); DCE `期货公司会员` (to 2024-05);
  SHFE `期货公司` / `非期货公司` (to 2025-08-12), then `期货公司会员/境外特殊经纪参与者` /
  `非期货公司会员/境外特殊非经纪参与者`. Exclude them before summing brokers (with them DCE "top-20 long" exceeds
  total OI, 141% in 2021). Product-level symbols (`AG`, `AL` …) sit beside contract symbols. Top-20 share of OI
  after exclusion, 2020–2026: long 60–80%, short 64–86% (CFFEX highest). On 2020-03-18 CZCE rows are labelled `ZCE`.
- **No top-20 data for INE crude and EC.** INE rows are filed under SHFE for bc/lu/nr; `sc` and `ec` have none, so
  holding-based positioning must not assume every product has holdings.
- **`SCTAS.INE`** (crude trade-at-settlement) trades on 24 sessions without a main-contract mapping; every other
  product has one on every session it trades. SGE Au99.99 vs SHFE AU main contract: median gap 0.29%, 95.9% of days
  within 1% (the gap is carry on a months-out contract: 0.6% in 2019–20, ~0.15–0.35% since).
- **`yc_cb` is not permitted** on this account (tier); China yield curves come from ChinaBond (plan 11 phase 10).
- **FXCM dating.** `fx_daily` bars carry the Beijing date of the New York 17:00 close: Friday's bar is dated Saturday
  and a short Sunday bar opens the week. Use `next_session`; never align FX by weekday. The CFDs (UKOIL, USOIL,
  COPPER, 10USNOTE, USDOLLAR, SPX500, NAS100, HKG33, CHN50) only start in 2022-07.
- **`cn_pmi` ignores `fields`** and always returns `ID`, `CREATE_BY`, `CREATE_TIME`, `UPDATE_BY`, `UPDATE_TIME`;
  its month column is upper-case `MONTH`.
- **Amount was two-sided too.** Before 2020 `amount / (vol × close)` is unchanged across the break, so
  `derived.fut_daily_one_sided` halves `amount` and `oi_chg` as well as `vol` and `oi`.
- **More per-call caps (not multiples of 1,000).** `stk_surv` 400, `stk_holdernumber` 5,500, `hk_hold` 4,200 per
  call; with a 1,000-step paging rule 760 `stk_surv` days lost more than half their rows (D-082). Paging now continues
  on any multiple of 100. `share_float` ignores `offset` per the handbook, but paged correctly by `ann_date` in 2026-09;
  the client raises if a page ever repeats.
- **Event data publishes on weekends.** `report_rc` (69–155 rows on a weekend day), `stk_surv`, `stk_holdertrade`,
  `share_float` have Saturday/Sunday rows: sweep every calendar day, not weekdays.
- **`report_rc`**: `tp` is total profit (10k CNY), not a target price (targets: `max_price`/`min_price`); 3,486
  rating-only reports carry no `quarter` (stored as ""). A one-month range stops at 5,000 rows: sweep by `report_date`.
- **`stk_holdertrade` repeats rows.** 65,459 rows fall in 20,023 (ts_code, ann_date, holder, direction, volume) groups
  but only 24,517 are distinct; ~4.5 k groups are genuine second trades the same day. No unique key exists; keep all
  distinct rows. `after_share` and `avg_price` are often NULL.
- **`share_float` is big since 2021**: IPO lock-up notices list every offline placement investor (up to 44 k rows on one
  announcement day). Filter by `share_type` / holder before aggregating.
- **`hk_hold` after 2024-08**: daily northbound disclosure ended; ~900 rows/day remain (southbound + partial), full
  lists only at quarter-ends.
- **Statements** carry an original and a corrected version per filing (`update_flag`); it must be requested and
  is part of the primary key (D-038), otherwise compaction drops real data.

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
