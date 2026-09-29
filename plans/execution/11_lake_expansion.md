# 11 — Lake expansion: every dataset the research asks need

| | |
|---|---|
| Status | doing (phase 1 code complete) — approved 2026-09-28 by user instruction ("design the data_loading lake for my asks and assign to the executor"); assigned to quant-cn-b7 (Opus) |
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
| 1 | Loader features | `DatasetSpec.source`, `known_on_rule`, `release_lag_days`, `values_from_dataset`; `DateWindowFetcher`; `FetcherFactory` source-aware; curated schemas for the plan-03 option/rate datasets and `download.order` completed | tests for each new kind/rule (incl. a FRED-style next-session rule and a monthly release lag); `make check` green | — | doing: code complete, uncommitted; commit + catalog refresh pending lake free |
| 2 | Sectors and composition | `index_classify` (SW2021 L1–L3), `index_member_all`, `index_weight` (300/500/1000/50, 2010+), `sw_daily` after a one-call tier check (fallback: member-computed L1 returns as a derived view) | every universe stock maps to one L1 industry on 3 sample dates; membership PIT test on an `out_date`; `sw_daily` vs member-computed within 10 bp/day or fallback documented | 1 | todo |
| 3 | ETFs and funds | `fund_basic` (E), `fund_daily` by `trade_date` (drop the `option_etfs` enum, keep raw), `fund_nav`, `fund_share`, `margin_secs` (verify endpoint name; if absent, document) | ETF count per date plausible; `fund_share × nav` vs `fund_daily` market value within 2% on a sample; premium/discount computable for 510300 | 1 | todo |
| 4 | Futures and gold | `fut_basic` all exchanges; `fut_daily`, `fut_holding` for INE/SHFE/DCE/CZCE 2019+; `fut_mapping`; `sge_basic`, `sge_daily` | every product has a main-contract mapping each session; top-20 coverage share per exchange reported; SGE Au99.99 vs SHFE AU front within 1% on a sample | 1 | todo |
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

## Open questions
None at assignment; DATA_LOADING_DESIGN §3c recommendations adopted (FRED first, AkShare only on proven need; small commodity set first, all exchanges' `fut_daily` anyway since it is one sweep).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-28 | 1 | Executor: phase 1 code complete, uncommitted: `DatasetSpec.source/known_on_rule/release_lag_days`, `DateWindowFetcher` (`date_window` sweep), `values_from_dataset`, source-aware `FetcherFactory`, `lake.EffectiveDateResolver` (as_is / next_session / period_end_lag), plan 09 datasets in `download.order` with explicit starts, `FRED_API_KEY` in `.env.example`. `make check`: ruff/mypy clean, lint_contracts 0, 251 passed; project-catalog step blocked only by the margin_detail download lock (475/~665 sessions). Lake busy |
| 2026-09-28 | 10 | Phase 10 added (D-065): AkShare gap-filler, official lending lists, BaoStock verification, official release dates; DATA_SOURCES.md reference |
| 2026-09-28 | — | Designed and assigned to quant-cn-b7 by user instruction; monitored by quant-cn-a1 |
