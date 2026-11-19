# 23 — Buybacks and shareholder yield (回购与股东回报率)

| | |
|---|---|
| Status | done 2026-11-13 (all six phases; display-only shareholder yield per D-154 update 2) |
| Owner | user (approve) / agent (build, daily refresh) |
| Created | 2026-11-13 |
| Notion | pending |
| Decisions | D-154, D-148, D-151, D-086 |
| Depends on plans | 11 (datasets, `known_on`), 05 (risk model, dividend style D-148), 15 ph7f (conditions), ph7e (morning report) |

## Goal
Every stock's buyback programmes (plan, approval, progress, completion) are in the lake point-in-time, a daily shareholder yield (cash dividends + executed buybacks over 12 months ÷ market cap) exists next to the dividend yield, its predictive power is measured, and the app and morning report show buyback progress for held and watched stocks.

## Scope
- In: Tushare `repurchase` (ts_code, ann_date, end_date, proc 预案 / 股东大会通过 / 实施 / 完成 / 停止, exp_date, vol, amount, high_limit, low_limit) from 2015; per-programme ledger; trailing-12-month executed amount; shareholder yield view; research on announcement events and yield; watchlist / holdings display and condition metrics; morning-report line for held and watched stocks.
- Out: buyback purpose (注销 vs 员工持股 / 库存股) beyond what announcement titles say (open question); major-holder 增持 (already in `stk_holdertrade`); changing the risk model's dividend style before the research shows an effect (a later decision).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Dataset `repurchase` | `config/datasets.yaml` entry (sweep by `ann_date` windows, `known_on: ann_date`, curated `events/repurchase`), backfill 2015–now, added to `make market-data` (D-151) | contract test on a fixture (one row per ts_code × ann_date × proc × end_date); backfill row count and a 2026-11-12 spot check (宁德时代 实施 2,005.9 万股 / 54.70 亿 cumulative) match a direct API call | — | done 2026-11-13 |
| 2 | `BuybackLedger` | groups announcements into programmes (one 预案 → later 股东大会通过 / 实施 / 完成 / 停止 of the same stock until completion or expiry); per programme: planned amount, price cap, executed amount and shares (cumulative `amount` of 实施 / 完成), state; per stock and date: executed buyback in the last 12 months, PIT by `ann_date` | TCs on hand rows: cumulative 实施 amounts are not double counted; a 停止 closes the programme; an expired 预案 without 实施 counts 0; nothing is used before its `ann_date` | 1 | done 2026-11-13 |
| 3 | Shareholder yield | derived view `shareholder_yield` (trade_date, ts_code: dividend_ttm, buyback_ttm, shy_ttm = (cash dividends + buybacks over 12 months) ÷ total market cap) refreshed by `curate` | TCs: a stock with only dividends equals `dv_ttm` within rounding; a buyback enters on its 实施 announcement date; real lake: 2026-11-13 cross-section summary (count with buybacks, median and top decile) recorded in the log | 2 | done 2026-11-13 |
| 4 | Research: does it predict? | research run (RESEARCH_LOG): (a) event study after 预案 (size as % of market cap, price cap vs close) and after 完成, 20 / 60-session excess, PIT; (b) month-end rank IC of `shy_ttm` vs `dv_ttm` alone, raw and after size / value, split pre / post 2024 (市值管理 policy) | results written with sample counts, IC t-stats and quintile spreads; a decision entry if `shy_ttm` should replace or join the dividend style (else D-154 notes "display only") | 3 | done 2026-11-13 |
| 5 | App and conditions | watchlist cards and the holdings notes table show shareholder yield and any active programme (executed / planned, price cap, expiry); `ConditionEvaluator` metrics `shy_ttm`, `buyback_active` (0 / 1), `buyback_done_pct`; Go fields and React display | TCs for the metrics and formats; smoke shows the block for a watched stock with an active programme; `make check` passes | 3, 15 ph7f | done 2026-11-13 |
| 6 | Morning report | `ReportSection` subclass adds a line when a held or watched stock announces a 预案, passes 股东大会, or completes / stops a programme since the last report | TC on hand documents (new events only, once); real dry run lists the day's events for the book | 5, 15 ph7e | done 2026-11-13 |

Status cell: `<state> <YYYY-MM-DD> (<commit>) — <note>`, state one of todo / doing / blocked / done.

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `DatasetSpec` (`repurchase`) | reuse (config only) | `quant_cn.data_loading` | 1 |
| `BuybackLedger` | new (name via `naming`) | `quant_cn.lake` | 2 |
| `DerivedViews` | extend (`shareholder_yield`) | `quant_cn.lake` | 3 |
| `ConditionEvaluator`, `Condition.METRICS` | extend (kind `capital`) | `quant_cn.portfolio`, `quant_cn.core` | 5 |
| `WatchlistBuilder`, `PositionReviewer` | extend (fields) | `quant_cn.portfolio` | 5 |
| `BuybackReportSection` | new (`ReportSection` subclass) | `quant_cn.visualization` | 6 |

## Risks
- `amount` semantics differ by stage (预案 = planned upper or lower bound; 实施 = cumulative to date): phase 2 must read each stage correctly or double count; checked on hand rows and spot checks.
- Programmes have no id in Tushare: grouping by stock and dates can merge two overlapping programmes; overlapping cases are listed and checked by hand.
- Purpose is missing: buybacks for employee plans do not reduce shares; the yield may overstate shareholder return for those.
- Tushare point / rate limits on a 10-year backfill (window size chosen in phase 1).
- 2024+ policy (回购增持再贷款) changes the base rate: research splits the sample.

## Open questions
- Count buybacks funded by 回购再贷款 the same as own cash? (Tushare does not say; titles may.)
- Net of share issuance (增发 / 股权激励 exercises) for a "net" shareholder yield, or gross only?
- Include major-holder 增持 (from `stk_holdertrade`) as a separate "support" line?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-13 | 5, 6 | Done. Real run: buybacks.json lists 5 new plans ≥ 2% (英搏尔 4.8%, 交控科技 4.0%, 硅宝科技 3.2%, 星帅尔 2.7%, 耐普矿机 2.4%) and a 巨人网络 预案 (20261110) for the book; watchlist cards carry 股东回报率 / 回购计划. make check exit 0 (796 passed, lint 0, Go ok, vitest 43, project.stale 0) |
| 2026-11-13 | 5, 6 | Phase 5 built: `ShareholderYieldReader.read_metrics` / `compute_plans` (TC-SYR-002) as condition kind `capital` (shareholder_yield, buyback_yield, buyback_plan_pct, buyback_done_pct; TC-CE-007) wired by `AppServiceBuilder`; watchlist entries and holdings chips gain 股东回报率 and 回购计划 (Go `WatchlistEntry`, React card and chip columns). Phase 6 built, widened after the research: `portfolio.BuybackEventsBuilder` (TC-BEB-001..002) writes buybacks.json with the market's new plans ≥ 2% of market cap and the book's events of the last 7 days; `visualization.BuybackReportSection` (TC-BRS-001..002) in the 持仓监测 e-mail; CLI `buyback-events` (TC-RPC-010), `make buyback-events` in track-daily. Waiting: real run and `make check` after the cyq_perf backfill releases the catalog |
| 2026-11-13 | 1, 2, 4 | Phase 1 done: backfill 60,878 rows, 3,726 stocks, 2018-01..2026-11-13; spot check 宁德时代 实施 2,005.9 万股 / 54.70 亿 on 20261112 matches the API. Phase 2 fixed after the real data: the vendor labels most progress reports 完成 (36k of 61k rows), so 完成 no longer closes a programme; progress rows go to the newest open programme whose planned amount covers them (small 回购注销限制性股票 plans run beside large buybacks); 预案 without expiry live one year. 宁德: 2023 plan 30 亿 → 27.1 executed, 2025 plan 80 亿 → 43.9, 2026 plan → 54.7 so far; market total executed in 12 months 1,734 亿 across 1,276 stocks. Phase 4 done (research 20261113_buyback_yield): plans ≥ 2% of market cap predict +2.0% (60 days, t 3.6), +4.6% since 2024; executed buyback yield adds nothing to the dividend yield (IC 0.011 vs 0.072); D-154 update: shareholder yield is display-only, the signal for conditions is the plan size |
| 2026-11-13 | 1–3 | Phase 1: `repurchase` in datasets.yaml (start 2018, not 2015: other datasets start 2019 and a 2018 start covers 2019's trailing 12 months; no unique key, exact duplicates dropped like stk_holdertrade), in base.yaml and `make market-data`; backfill running. Phase 2: `lake.BuybackLedger` (TC-BBL-001..004). Phase 3: `lake.ShareholderYieldReader` (TC-SYR-001) computes on demand (latest day for the app, month-ends for research) instead of a daily derived table; dividends from daily_basic dv_ttm |
| 2026-11-13 | — | Approved (user: "全部同意，按顺序开工"); D-154 accepted |
| 2026-11-13 | — | Drafted (user: "dividend和回购算回去了吗？" → "起草回购数据的计划吧"). API probe 2026-11-01..12: 520 rows, proc 实施 321 / 预案 101 / 完成 77 / 股东大会通过 21; fields ts_code, ann_date, end_date, proc, exp_date, vol, amount, high_limit, low_limit |
