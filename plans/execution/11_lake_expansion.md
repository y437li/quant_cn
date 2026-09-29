# 11 — Lake expansion: every dataset the research asks need

| | |
|---|---|
| Status | doing — phases 1–4 done (5e7c06f, 962d603, 4f54772, 6062881); phase 5 next — approved 2026-09-28 by user instruction ("design the data_loading lake for my asks and assign to the executor"); assigned to quant-cn-b7 (Opus) |
| Owner | executor quant-cn-b7 (build) / quant-cn-a1 (design, record, monitor) |
| Created | 2026-09-28 |
| Notion | pending |
| Decisions | D-047, D-049, D-050, D-053, D-062, D-063, D-065 |
| Depends on plans | 01, 02 (done); 03 ph1 leftovers folded in here |

## Goal
The lake holds, curated and PIT-annotated, all datasets required by plans 04–10 and the ETF pairs track:
sector classification and index composition, ETFs and funds, commodity futures and gold, domestic macro,
international benchmarks from FRED, analyst and event data, and the extra statement fields; the data-loading
layer is multi-source and every new endpoint is permission-checked before any backfill.

## Scope
- In: DATA_LOADING_DESIGN §3c in full: `DatasetSpec.source`, `FredClient`, `DateWindowFetcher`, `values_from_dataset`, `release_lag_days`, `known_on_rule`; all dataset groups; curated schemas; DATA_CATALOG rows; plan 03 phase-1 leftovers (curated option/rate schemas, `download.order`); reconciliations; a data-coverage notebook.
- Out: derived series and factors on this data (plans 04, 05, 10), `cyq_perf` and `margin_detail` 2019+ unless requested.

## Phases (run in this order; each ends with `make lake-rebuild` byte-identical, DATA_CATALOG §1 rows, lake INDEX, and a report)

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Loader features | `DatasetSpec.source`, `known_on_rule`, `release_lag_days`, `values_from_dataset`; `DateWindowFetcher`; `FetcherFactory` source-aware; curated schemas for the plan-03 option/rate datasets and `download.order` completed | tests for each new kind/rule (incl. a FRED-style next-session rule and a monthly release lag); `make check` green | — | done (5e7c06f) |
| 2 | Sectors and composition | `index_classify` (SW2021 L1–L3), `index_member_all`, `index_weight` (300/500/1000/50, 2010+), `sw_daily` after a one-call tier check (fallback: member-computed L1 returns as a derived view) | every universe stock maps to one L1 industry on 3 sample dates; membership PIT test on an `out_date`; `sw_daily` vs member-computed within 10 bp/day or fallback documented | 1 | done (962d603); criterion 3 restated per D-072 |
| 3 | ETFs and funds | `fund_basic` (E), `fund_daily` by `trade_date` (drop the `option_etfs` enum, keep raw), `fund_nav`, `fund_share`, `margin_secs` (verify endpoint name; if absent, document) | ETF count per date plausible; `fund_share × nav` vs `fund_daily` market value within 2% on a sample; premium/discount computable for 510300 | 1 | done (4f54772); criterion 1 = name-based ETF count (D-075) |
| 4 | Futures and gold | `fut_basic` all exchanges; `fut_daily`, `fut_holding` for INE/SHFE/DCE/CZCE 2019+; `fut_mapping`; `sge_basic`, `sge_daily` | every product has a main-contract mapping each session; top-20 coverage share per exchange reported; SGE Au99.99 vs SHFE AU front within 1% on a sample | 1 | done (6062881); cleaning views per D-079 |
| 5 | Domestic macro | `yc_cb`, `fx_daily`, `shibor_lpr`, `cn_cpi`, `cn_ppi`, `cn_pmi`, `cn_m` with `release_lag_days` | PIT test: a CPI print is not visible before period end + lag; yield curve has every session | 1 | todo |
| 6 | FRED | `FredClient`, `FRED_API_KEY` in `.env.example`, five series 2010+, next-session visibility | five series curated; a US Friday observation is visible from the following China session; raw copies kept | 1 | todo |
| 7 | Analysts and events | one-call tier check for `report_rc`; then `report_rc` 2019+ if allowed, `stk_surv`, `broker_recommend`, `hk_hold`, `forecast`, `express`, `stk_holdertrade`, `share_float` (month windows), `disclosure_date`, `stk_holdernumber` | tier result recorded as a decision; per dataset: known-on column set, PIT test on one announcement; `report_rc` consensus snapshot computable for one stock-date if fetched | 1 | todo |
| 8 | Statement fields + refetch | seven fields added (DATA_LOADING_DESIGN §3c); `--force` refetch of 30 quarters for the three statements | curated row counts unchanged ±0.1%; new columns populated ≥ 95% where applicable; `update_flag` handling intact (D-038) | 1 | todo |
| 10 | Third source and verification | `AkShareClient` (gap-filler: LME copper if needed, official macro release calendars replacing lag rules, exchange member position files), SSE/SZSE margin-target lists into `external/` + a `margin_targets` dataset, `BaoStockClient` verification of closes/adj_factor as a nightly quality view (`quality.price_crosscheck`), NBS/PBOC release dates | release dates replace `release_lag_days` for CPI/PPI/PMI/M2; lending list loaded with provenance; cross-check view shows mismatch rate (< 0.1% expected) and never overwrites Tushare data | 5, 6 | todo |
| 9 | Coverage notebook | `YYYYMMDD_lake_coverage.ipynb`: per dataset first/last date, rows, sessions covered, known-on rule, reconciliation results; outputs committed | runs top to bottom; DATA_CATALOG §1 updated for every new dataset | 2–8 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `DatasetSpec` (source, known_on_rule, release_lag_days, values_from_dataset) | extend | core | 1 | `FetcherFactory`, `PitAligner`, `Compactor` |
| `DateWindowFetcher` | new (`BaseFetcher`) | data_loading | 1 | `FetcherFactory`: `share_float`, `fund_nav`, FRED series |
| `AkShareClient`, `BaoStockClient` | new (`BaseApiClient`) | data_loading | 10 | `FetcherFactory` for `source: akshare` / `baostock`; quality view |
| `FredClient` | new (`BaseApiClient`) | data_loading | 6 | `FetcherFactory` for `source: fred` |
| `FetcherFactory` | extend (source-aware, values_from_dataset) | data_loading | 1 | `DownloadPipeline` |
| `PitAligner` | extend (`known_on_rule`, `release_lag_days`) | lake | 1, 5 | `DerivedViews`, factors |
| `DerivedViews` | extend (member-computed Shenwan L1 returns fallback) | lake | 2 | `SectorIndexPanel` (plan 10) |

## Risks
- Permission tiers (`sw_daily`, `report_rc`, `cyq_perf`, `fut_holding` for commodity exchanges): every new endpoint is checked with one call before scheduling; a denied endpoint becomes a recorded decision, not a silent gap.
- Lake write lock: downloads block `make check` and queries for hours; phases 4 and 7 are the long ones (estimate 6–10 h each at ~32 keys/min). Sequence them overnight; announce "lake busy/free".
- FRED terms of use: research use permitted; key in `.env`; raw copies kept; no redistribution.
- Monthly macro release dates are approximated by lag rules; flagged in `known_on`.
- `fund_daily` by date replaces the enum: existing raw files stay; the raw key changes from `ts_code=` to `trade_date=`, so the catalog view must union both or the old files move to `external/`.

## Open items
- ~~`report_rc` 66 rows~~ explained: 20260925 was the Mid-Autumn holiday; 20260924 returns 177 rows (66 stocks, 21 brokers). Coverage per day still to be sized on a normal week before the phase-7 backfill.
- `FRED_API_KEY` missing from `.env`; needed before phase 6 (user).

## Open questions
None at assignment; DATA_LOADING_DESIGN §3c recommendations adopted (FRED first, AkShare only on proven need; small commodity set first, all exchanges' `fut_daily` anyway since it is one sweep).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-29 | 4 | Phase 4 done (6062881, 751a94e). Through 2026-09-28: fut_basic 11,287; fut_daily 1,647,698; fut_mapping 312,037; fut_holding 15,207,156; sge_basic 13; sge_daily 52,687. Run 335a3cbedc56 failed on one fut_holding key (20240520, timeout after 5 attempts); resumed run ad9c64160506 ok. Old CFFEX-only files were exact subsets (26,992 / 306,369 rows) and were deleted. Criteria: (1) main-contract mapping 100% of product-sessions on CFX/DCE/GFE/SHF/ZCE, INE 99.67% (only SCTAS.INE, 24 days); (2) top-20 OI coverage 2020–26 after excluding category rows: long 0.60–0.80, short 0.64–0.86 by exchange; (3) SGE Au99.99 vs SHFE AU main over 1,877 days: median gap 0.29%, 95.9% within 1% (2019–20 lower from carry on a months-out main contract). Digests unchanged, 0 orphans; make check 264 passed, 33 datasets, stale 0 |
| 2026-09-29 | 4 | Traps (DATA_CATALOG §3b): (a) commodity-exchange oi/vol two-sided before 2020-01-02, halving overnight (CFFEX unaffected); (b) fut_holding mixes member-category totals (期货公司/非期货公司 etc., exchange- and period-specific) and product-level symbols with broker/contract rows — DCE "top-20 long" reaches 141% of OI if included; (c) no top-20 rows for INE sc/ec, bc/lu/nr filed under SHFE; (d) 721 CZCE rows labelled "ZCE" on 2020-03-18. D-079: cleaning as lake derived views (`fut_holding_brokers`, `fut_daily_one_sided`) |
| 2026-09-29 | 4 | Phase 4 started: fut_basic, fut_daily, fut_mapping, fut_holding (all exchanges, 2019+), sge_basic, sge_daily; lake busy ~5 h (D-077, appended by executor). INE has no top-20 holding data: bc/lu/nr appear under SHFE, sc and ec missing. Old CFFEX-only 2025–26 files to be verified as a subset before deletion |
| 2026-09-29 | 1 | **Paging bug (D-076, accepted by execution):** `TushareClient` stopped at the first page shorter than limit 6000, so endpoints with a lower per-call cap (fut_holding 4,000; fund_share 2,000) looked complete after one page. Fetch-log scan: only fund_share affected (21 quarter-end dates at exactly 2,000 rows; true sizes 8,400–26,000), refetched with --force; every other dataset's row counts sit below a page size that endpoint has already exceeded. Fix: keep paging while a page is full or a multiple of 1,000, advance offset by rows received (TC-TC-008). Side effect: one no-exchange fut_holding call now returns all exchanges (10,259 rows on 09-24 = per-exchange sum) |
| 2026-09-29 | 3 | Phase 3 done (4f54772, 1832d35). Run 5cb7264da7da via Prefect, all keys ok: fund_basic 2,961; fund_daily 1,878 sessions, 2,211,795 rows; fund_nav 2,325,598; fund_share 1,667,752; margin_secs 6,498,423. Old per-ETF fund_daily files: all 15,993 rows identical in the new curated table; moved to external/tushare_fund_daily_option_etfs/ with PROVENANCE.md. Criteria: (1) ETF count per year-end 269 → 1,705 (2019 → 2026-09-28) by name match (fund_share.fund_type unusable, mostly NULL before 2026; D-075); (2) shares × NAV vs shares × close within 2% for 98.2–99.1% of ETFs on three dates, median gap 9–12 bp (fund_nav.net_asset filled on ~1–2% of rows only → size = shares × NAV); (3) 510300.SH premium/discount over 1,878 days median −4.3 bp, p5 −18.8, p95 +13.3. D-073 on the real lake removed exactly the 12 expected orphans (manifest fetch_log_orphans.json). Digests unchanged; make check 262 passed, 29 datasets, stale 0 |
| 2026-09-29 | 3 | Traps (DATA_CATALOG §3b): margin_secs SSE list frozen at 1,956 names 2019-01 → 2024-03 (SZSE grows 819 → 2,105), so SSE lending eligibility before 2024-04 is unreliable → phase 10 official lists matter; by-date calls on holidays return 0 rows or partial lists |
| 2026-09-28 | 3 | Phase 3 started: fund_basic, fund_daily (by trade_date; option_etfs enum removed), fund_nav (new `nav_date` kind, 2,116 rows/session, next_session known-on), fund_share (next_session), margin_secs (exists; one call covers SSE/SZSE/BSE, 4,479 rows; as_is) — backfill 2019+ ~7,500 calls, lake busy ~4 h (D-074, appended by executor). D-073 implemented (remove_orphans keeps empty keys; manifest fetch_log_orphans.json; TC-FL-006, TC-QCC-007), uncommitted. Old per-ETF fund_daily raw files to be verified as a subset then moved to external/tushare_fund_daily_option_etfs/ with PROVENANCE.md. report_rc 66-row puzzle explained by the holiday |
| 2026-09-28 | 2 | Phase 2 done (962d603, da69eb2). Run 747880eac2d8 via Prefect (first run 0c6841f828de failed on the CSI 1000 offset cap, fixed by D-069): index_classify 511 rows (L1 31 / L2 134 / L3 346); index_member_all 7,920; index_weight 68 keys, 64 fetched, 4 empty (CSI 1000 pre-2014), 313,000 rows; sw_daily 1,878 sessions, 930,263 rows. D-070: shibor had been silently capped at 2,000 rows (started 2018-08-21); yearly windows now give 2,907 rows from 2015-01-04. Criteria: (1) no stock ever maps to two L1s; unclassified SH/SZ stocks 70/3,612 on 2019-06-28, 6/4,898 on 2022-12-30, 0/5,210 on 2026-09-24 (pre-2021-07 gaps documented, DATA_CATALOG §3b); (2) PIT membership test on 603466.SH passes; (3) sw_daily vs member-computed L1 over 20,553 industry-days: free-float weights median 2.5 bp, 89.7% within 10 bp, 98.1% within 25 bp (Shenwan tiered weights explain the residual). lake-rebuild digests unchanged; make check 257 passed, 25 datasets, stale 0 |
| 2026-09-28 | 2 | Decisions: D-071 first-known L1 backfill as a flagged non-PIT grouping variable for neutralisation before 2021-07; D-072 criterion (3) restated (median ≤ 5 bp, ≥ 85% within 10 bp, ≥ 95% within 25 bp on free-float weights); D-073 FetchLog.remove_orphans() run by rebuild |
| 2026-09-28 | 2 | Phase 2 started: index_classify, index_member_all, index_weight, sw_daily (1,878 sessions from 2019) downloading; tier checks all OK; new sweep kinds is_new / index_code; SW2021 classification PIT caveat before 2021-07 (D-068, appended by quant-cn-b7). D-067 implemented (PREFECT_ENV precedence shell > .env > default, doctor row TC-QCC-006), uncommitted |
| 2026-09-28 | 7 | report_rc tier check (one call, report_date=20260925): ACCESS OK, 66 rows, columns ts_code, name, report_date, org_name, quarter, eps, np, tp, rating. 66 rows for one Friday is suspiciously low: check per-call row capping / paging and coverage before any backfill (open item) |
| 2026-09-28 | 1 | Phase 1 done and committed (5e7c06f): `DatasetSpec.source/known_on_rule/release_lag_days`, `DateWindowFetcher` (`date_window` sweep), `values_from_dataset`, source-aware `FetcherFactory`, `lake.EffectiveDateResolver` (as_is / next_session / period_end_lag), plan 09 datasets in `download.order` with explicit starts, `FRED_API_KEY` in `.env.example`. `make check`: ruff/mypy clean, lint_contracts 0, 251 passed; project-catalog step blocked only by the margin_detail download lock (475/~665 sessions). Lake busy |
| 2026-09-28 | 10 | Phase 10 added (D-065): AkShare gap-filler, official lending lists, BaoStock verification, official release dates; DATA_SOURCES.md reference |
| 2026-09-28 | — | Designed and assigned to quant-cn-b7 by user instruction; monitored by quant-cn-a1 |
