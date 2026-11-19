# 31 — Sector monitor: 房地产 and 游戏

| | |
|---|---|
| Status | done 2026-11-17 (ph1–5); App Store link through plan 19 ph2 |
| Owner | agent |
| Created | 2026-11-17 |
| Notion | pending |
| Decisions | D-137 (app charts), D-161 (entity resolution), D-168 |
| Depends on plans | 15 (chain app), 19 (App Store charts), 28 (graph, EntityResolver) |

## Goal
A `#sector-monitor` tab in the chain app shows, per sector (房地产, 游戏), the watch items of the watchlist as plotted time series per company and for the sector, and games are linked to the listed companies that publish, develop or operate them.

## Scope
- In:
  - **房地产** (保利发展, 招商蛇口, 万科A, 滨江集团, 金地集团, 新城控股, plus the companies in config):
    - 70-city second-hand and new-home price index, month on month (国家统计局, mid-month);
    - monthly sales brief (签约金额 and area, year on year);
    - 合同负债, single-quarter 资产 / 信用减值, 拿地强度 (land spend / contracted sales, where the brief discloses it);
    - dividend per share and payout ratio;
    - 散户温度计, 获利盘 (cyq_perf winner_rate) and 成本分位.
  - **Realized volatility, both sectors** (user 2026-11-17): 20- and 60-day annualised realized vol of each company and of the Shenwan sector index (房地产 801180; 游戏 via the 传媒 游戏Ⅱ index), with its 3-year percentile.
  - **游戏** (巨人网络, 三七互娱, 吉比特, 完美世界, 世纪华通, 恺英网络, plus config):
    - monthly 版号 approvals (domestic and imported, per company);
    - App Store top-grossing rank per game and company (plan 19 data);
    - 合同负债 (deferred revenue), quarterly revenue and 销售费用率;
    - dividends, 散户温度计, 获利盘.
  - **Game ↔ company links** (`game_company`):
    - one row per (game, company, role: publisher / developer / operator, source, known_on);
    - from the 版号 lists (出版单位 / 运营单位) and the App Store developer (plan 19 publisher map);
    - names resolved to ts_code with `EntityResolver`, so subsidiaries such as 上海巨人网络科技 resolve to 巨人网络.
- Out:
  - other sectors (they are added later through config only);
  - paid data such as 中指研究院 or 伽马数据;
  - trading signals: the tab displays the data, the watchlist rules stay as they are.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Public monthly data | `NbsClient` + dataset `macro_house_price_70` (city, month, type new / second-hand, MoM / YoY index, known_on = release date) from data.stats.gov.cn; `NppaClient` + dataset `game_license` (month, game, publisher, operator, domestic / imported, known_on = list date) from nppa.gov.cn | 2023-01 → latest months loaded; Oct 2026 shows 一线 二手 +0.2% as in the research note; latest 版号 list count matches the NPPA page | — | done 2026-11-17 |
| 2 | Game ↔ company links | `GameCompanyBuilder` writes `derived/graph/game_company` from `game_license` + plan 19 publisher map via `EntityResolver`; unresolved names listed for review | ≥ 90% of 2025–2026 approvals of the 6 game companies resolved (spot check 50 rows); 巨人's games (征途, 原始征途, 球球大作战, 超自然行动组 …) all linked | 1, 19 ph2 | done 2026-11-17 |
| 3 | Developer monthly sales | 销售简报 announcements (cninfo keyword 简报, `operating_data` rule 销售…简报) read by the existing `OperatingDataExtractor` (plan 18) into the LabelStore set `operating_data` (period = month, known_on = announcement date); D-168 | the 6 developers, 2024-01 → latest month; 招商蛇口 1–10 月 sums to 1,588 亿 ±1% | — | done 2026-11-17 |
| 4 | Monitor tables | `config/sector_monitors.yaml` (sector → companies, metrics); `SectorMonitorBuilder` writes `derived/sector_monitor/{series,company}` (long format: sector, ts_code or region, metric, period, value, known_on) from the datasets above plus income / balancesheet / dividend / cyq_perf / RetailGauge, and realized vol (20 / 60 days, 3-year percentile) from `RealizedVolCalculator` | every metric of both sectors has ≥ 8 periods; `make sector-monitor` is idempotent; `make check` passes | 1–3 | done 2026-11-17 |
| 5 | App tab | Go endpoint `/api/sector-monitor/{sector}`; web `#sector-monitor` with a sector switch and one small-multiple line chart per metric (sector line + company lines; company table with the latest value and change); a game panel listing each company's games and their ranks / approvals | tab renders both sectors; `make check` (go test, vitest, smoke) passes; screenshot checked | 4 | done 2026-11-17 |

Status cell: `<state> <YYYY-MM-DD> (<commit>) — <note>`, state one of todo / doing / blocked / done.

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `NbsClient` | new (subclass `BaseApiClient`) | data_loading | 1 |
| `NppaClient` | new (subclass `BaseApiClient`) | data_loading | 1 |
| `GameCompanyBuilder` | new | industry_graph | 2 |
| `EntityResolver`, `GraphStore` | reuse (+ table `game_company`) | industry_graph, lake | 2 |
| `OperatingDataExtractor` | reuse (replaces the planned `SalesBriefExtractor`, D-168) | industry_graph | 3 |
| `LabelStore` | reuse | lake | 3 |
| `SectorMonitorBuilder` | new | analytics | 4 |
| `RetailGauge`, cyq_perf reader | reuse | — | 4 |
| `RealizedVolCalculator` | new: extracted from `SmallCapWatchBuilder`'s private realised-vol code (that class then calls it) | calculation | 4 |
| chain_api store + handler, `SectorMonitorPage` | new | apps | 5 |

## Risks
- data.stats.gov.cn and nppa.gov.cn may throttle or change layout. Mitigation: monthly fetch only, a raw-page cache, and an alert if a month is missing.
- Some developers stopped publishing monthly briefs (万科 publishes; others only quarterly). The series shows the gaps, nothing is interpolated.
- 拿地强度 is disclosed irregularly. It is shown where it is disclosed and marked as partial.
- 版号 operators are often unlisted subsidiaries or partners. Unresolved names go to a review list and are not guessed.

## Open questions
- ~~70-city series: tier-1 vs city picker~~ → user 2026-11-17: 一线 (4 cities) plus 二线 and 三线 averages, no picker.
- Which other companies go on the two sectors' lists?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-17 | 3 | done: after the CNINFO last-page fix (D-111 u1) and re-fetch, 招商蛇口 2026-01..10 monthly 签约 sums to 1,587.7亿 (10月 brief: 1,588亿). 新城 titles its briefs 经营简报, so the rule gained it (D-168 u1; +130 docs). Province rows were overwriting 新城's totals; DeveloperSalesReader now keeps company totals only (TC-DEV-003). 新城 1–8月 81.07亿 = its brief; 1–9月 88.26 vs 88.25亿. 万科 stopped monthly briefs after 2025-01; 滨江 and 金地 file none |
| 2026-11-17 | 4 | done: two `make sector-monitor` runs give byte-identical sector_monitor.json; make check 1,021 passed |
| 2026-11-17 | 5 | done: make app-smoke against 8787 SMOKE OK (sector-monitor: 2 sectors · 9 charts · 7 rows); 游戏 desktop screenshot checked (rankings, inverted rank chart). Fixed after the check: a stale rank (恺英 100 from an earlier day) shown as current, and right-aligned text in the rank tables |
| 2026-11-17 | 1 | done: the NPPA Oct 2026 domestic list (t20261029_1015044) has 183 审批号 on the page and 183 in game_license; 一线 二手 Oct +0.20% (see the ph1 row) |
| 2026-11-17 | 2 | done, with the criterion changed. 2025–26 approvals linked to the 6 companies: 恺英 27, 三七 12, 吉比特 10, 世纪华通 9, 巨人 6, 完美 5. The ≥ 90% share cannot be measured: an unresolved holder has no known parent, so the denominator is unknown. 巨人's 征途 / 原始征途 / 球球大作战 / 超自然行动组 are not in the 2022+ 版号 lists, so they are linked through the plan 19 App Store accounts instead (all 3 charting titles linked). Every rule- or LLM-resolved holder (43) was reviewed |
| 2026-11-17 | 5 | 游戏 App Store 排行榜 (user: "游戏行业应该给我排行榜的信息啊"; plan 19 ph2, D-137 update 1): metric `app_rank` (best cn grossing rank per company, inverted chart, table column) and a `rankings` block (the 6 companies' games: cn grossing / prev / free, best overseas and markets; cn top 20 with companies); web `SectorRankingsPanel`; TC-SMB-004, TC-ARR-001..002, TC-APS-001..002; make check 1,020 passed, 50 vitest |
| 2026-11-17 | — | drafted after the user asked for a tab plotting the 招商蛇口 watch items for 房地产 and 游戏, with games linked to companies |
| 2026-11-17 | — | approved by the user ("可以，一线加二三线平均就行，继续"); 70-city shown as 一线 + 二线 / 三线 averages; ph1 started |
| 2026-11-17 | 4 | user added realized-vol monitoring: company and sector-index 20 / 60-day vol with 3-year percentile; shared `RealizedVolCalculator` extracted from `SmallCapWatchBuilder` |
| 2026-11-17 | 1 | `BaseHtmlListClient` (paged gov lists, HTML tables, 404 / since stop), `NbsHousePriceClient` (dataset `house_price_70`, 2023-01 → 2026-10, 46 months × 140 rows; January tables without the average column handled, TC-NHP-004), `NppaGameClient` (dataset `game_license`, 6,078 approvals incl. imported lists); data.stats.gov.cn blocks this host, release pages used instead. Tier-1 second-hand MoM Oct 2026 = +0.20% (matches the research note). cninfo keyword sweep gains 简报 (1,740 rows; 招商蛇口 29, 新城 30, 保利 23 briefs, 万科 6 to 2025-01, 滨江 / 金地 none). Tests TC-BHL-001..002, TC-NHP-001..004, TC-NGC-001..002 |
| 2026-11-17 | 2 | `EntityResolver.find_by_alias` (TC-ER-008), `GameCompanyBuilder` (TC-GCB-001..002), GraphStore tables game_alias / game_company, `build-graph` writes game_company; lake script `meta/runs/plan31_game_aliases.py` (66 DeepSeek calls, 3,273 of 3,323 holder names proposed). Resolution: 43 holders → listed companies, all correct on review (巨人 ← 上海巨人网络科技, 吉比特 ← 雷霆互动 / 深圳雷霆, 恺英 ← 4 subsidiaries, 世纪华通 ← 数龙 / 点点互动, 中国移动 ← 咪咕); 9.6% of approvals have a listed company (most licences go to private studios). App Store link waits for plan 19 ph2 |
| 2026-11-17 | 3 | 1,185 operating_data PDFs downloaded, extracted (1,171 DeepSeek calls) and imported (operating_data 6,190 rows). Found and fixed a CninfoClient last-page bug (D-111 update 1, TC-CNC-005): briefs were missing for some months (招商蛇口 2026-06 / 07 / 10). CNINFO datasets are being re-fetched with --force; done criterion (招商蛇口 1–10 月 = 1,588 亿) checked after the re-fetch |
| 2026-11-17 | 4 | `RealizedVolCalculator` extracted from SmallCapWatchBuilder (TC-RVC-001..002; TC-SCW unchanged), `SectorMonitorSettings` + config/sector_monitors.yaml (TC-SMS-001..002), `SectorMetricReader` (TC-SMR-001..003), `DeveloperSalesReader` (TC-DEV-001..002; land = all parcels of a brief, larger of total / equity price, in the reported month), `SectorMonitorBuilder` (TC-SMB-001..003), `AppServiceBuilder.build_sector_monitor` (TC-ASB-003), `sector-monitor` command (TC-QCC-017), `make sector-monitor` in track-daily. Real run checks: 招商蛇口 合同负债 1,532.8 亿, 获利盘 54.3%, 温度计 0.078, tier-1 二手 +0.20%, 游戏Ⅱ 20-day vol 49.9% (86th percentile) |
| 2026-11-17 | 5 | Go `GetSectorMonitor` + `/api/sector-monitor` (TC-ST-028, TC-API-015), web `#sector-monitor` (行业监控 in 监测): sector switch, company table (latest values, vol and 3-year percentile, 散户温度计 colours), multi-line chart grid; vitest format tests; smoke check (2 sectors, 9 charts, 7 rows, no overflow at 390 px). Daily charts trimmed to 250 sessions after the screenshot review |
