# 33 — Sector monitor signals: sales trend, price breadth, launches, valuation, revisions, surveys

| | |
|---|---|
| Status | approved 2026-11-17 (user: "可以", for the six indicators proposed in chat); done 2026-11-17 (ph1–4) |
| Owner | agent |
| Created | 2026-11-17 |
| Notion | pending |
| Decisions | D-170, D-168, D-137 |
| Depends on plans | 31 (sector monitor), 19 (App Store charts) |

## Goal
Each 行业监控 sector shows answers, not only levels: is the sector getting better or worse (sales trend, how many cities are still falling, new games breaking out), and where money and valuation stand (valuation percentile, analyst revisions, institutional surveys).

## Scope
- In (all from datasets already in the lake):
  - **房地产**: contracted-sales year-on-year (3-month rolling sum, and year to date in the table); 70-city breadth (cities with a month-on-month fall, new and second-hand);
  - **游戏**: new-game launches (released within `new_game_days`, on the home grossing or free top 100 or any overseas grossing top 100 at the latest capture), every publisher;
  - **both**: valuation and its 5-year percentile (PB for 房地产, PE TTM for 游戏; companies from `daily_basic`, index from `sw_daily`); analyst revision (3-month change of the FY1 median net-profit forecast, `report_rc`); institutional surveys per month (`stk_surv`).
- Out: 统计局 national sales / starts / inventory (a new source, later); paid price data; alerts and trading rules.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | 房地产 trend | `DeveloperSalesReader.read_sales_yoy` (3-month rolling sum yoy %, YTD yoy); `SectorMetricReader.read_house_breadth` (cities with mom < 100 per month, lines 新房 / 二手); metrics `sales_yoy`, `house_price_breadth` | TCs; YTD yoy matches the briefs' printed 1–10月 yoy within 1 pt (招商蛇口 prints none: 保利 / 新城 used); breadth Oct 2026 = 49 新房 / 58 二手 | — | done 2026-11-17 |
| 2 | Game launches | `AppRankReader.read_rankings` adds `new` (games released within `new_game_days`, any publisher, company when mapped) | TC; the list on 2026-11-17 is checked by hand against release dates | — | done 2026-11-17 |
| 3 | Market signals | `MarketSignalReader` (new): `read_valuation` (level and 5-year percentile, index and companies), `read_revisions` (FY1 median net profit, 3-month change), `read_surveys` (survey days per month) | TCs; percentile of a known series; revisions and survey counts spot-checked for 2 companies | — | done 2026-11-17 |
| 4 | Builder and tab | metrics wired in `SectorMonitorBuilder` and `config/sector_monitors.yaml`; table columns (YTD sales yoy, valuation level and percentile, revision, 90-day surveys); 新品上榜 table in the 排行榜 block; notes | `make check` passes; smoke OK; both sectors' screenshots checked | 1–3 | done 2026-11-17 |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `DeveloperSalesReader` | extend (`read_sales_yoy`) | portfolio | 1 |
| `SectorMetricReader` | extend (`read_house_breadth`) | portfolio | 1 |
| `AppRankReader` | extend (`new` block) | portfolio | 2 |
| `MarketSignalReader` | new | portfolio | 3 |
| `RealizedVolCalculator` | reuse (`compute_rank_pct` with a 5-year window) | calculation | 3 |
| `SectorMonitorSettings`, `SectorMonitorBuilder`, `SectorMonitorPage` | extend | core, portfolio, apps | 4 |

## Risks
- PE TTM is meaningless for a loss-maker: a negative or missing PE gives no percentile, not a number.
- FY1 changes at the turn of the fiscal year: a revision is only computed between two windows that forecast the same fiscal year.
- Apple's release_date is the app's first release: a relaunch under an old app id is not counted as new.
- A developer that skips a month has no rolling 3-month yoy for the windows that include it; gaps are not filled.

## Open questions
- (none; windows default to 90 days for launches, revisions and surveys, 5 years for valuation; all in config)

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-17 | 4 | done: builder metrics wired (TC-SMB-005; extras YTD yoy / valuation level / 90-day surveys; in_table flags; companies more than STALE periods behind are left out of the table), config/sector_monitors.yaml, web columns + 新品上榜 table + notes. Revision fixes after review: one value per broker (招商蛇口 −34% → −11.7%) and no value on a loss median (removes −700% spikes). Smoke OK on a test server (2 sectors · 14 charts · 7 rows); both sectors' screenshots checked; make check 1,031 passed. 巨人's revision is −4.7% with broker dedup (−2.8% without) |
| 2026-11-17 | 1 | done: `read_sales_yoy`, `read_ytd_yoy` (TC-DEV-004; stale developers dropped), `read_house_breadth` (TC-SMR-004). Real data: YTD yoy 保利 −10.68% = brief −10.68%, 新城 −40.15% = brief −40.15%, 招商蛇口 +1.73% (its brief prints no yoy); breadth Oct 2026 新房 49 / 二手 58 |
| 2026-11-17 | 2 | done: `read_rankings` `new` (TC-ARR-003); 93 games on 2026-11-17, e.g. 篮球少女：飞跃巅峰 (阿里, 10-21, cn grossing #31), 王者万象棋 (腾讯, 09-08, free #9), 斗破苍穹：异火降世 (星辉, 11-13, free #31); every release_date is inside the 90-day window; the tab shows the first 30 |
| 2026-11-17 | 3 | done: `MarketSignalReader` (TC-MKS-001..003; TC-MSR clashed with MarginSignalReader). Spot checks: 巨人 FY2026 median forecast 42.47亿 vs 43.71亿 90 days earlier = −2.8% (manual SQL agrees); 巨人 surveys 1 day in 90 days (manual count 1). Found: sw_daily (stopped 11-11), report_rc and stk_surv (stopped 09-29) were not in the daily refresh; added to MARKET_DATASETS and backfilled from 20260901. stk_surv is sparse for these names (≤ 5 survey days in 2026) |
| 2026-11-17 | — | approved (user: "可以") after the indicator proposal in chat; D-170 records the definitions |
