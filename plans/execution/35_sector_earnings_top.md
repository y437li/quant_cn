# 35 — Sector earnings-season top signal (好消息涨不动)

| | |
|---|---|
| Status | done 2026-11-18 (ph1–3); approved 2026-11-18 (user: "可以") |
| Owner | agent |
| Created | 2026-11-18 |
| Notion | pending |
| Decisions | D-172, D-092, D-170 |
| Depends on plans | 31 (sector monitor tab), 33 (sector signals) |

## Goal
During every earnings season, each Shenwan L2 sector shows whether its best-surprise companies still get paid for good news. A sector that has rallied and whose good news no longer lifts the price is flagged in the 行业监控 tab and the morning e-mail, together with its past firings and their outcomes.

## Scope
- In:
  - **Earnings events, all A shares, from 2019:**
    - one event per (company, fiscal quarter), dated at the first disclosure (业绩预告, 快报 or report);
    - SUE = the single-quarter net profit yoy change ÷ std of the prior 8 yoy changes (≥ 4);
    - SUE decile within each quarter;
    - excess vs the equal-weight market over pre60 [-60,-1], reaction [0,+1], post20 [+2,+21].
  - **Sector signal per SW L2 (point-in-time membership) and quarter:**
    - the best-surprise events (deciles 8–9, ≥ 5): mean pre60 and reaction;
    - the share of the sector already reported;
    - prior 120-session sector excess (rally ≥ 20%);
    - median shareholder-count change.
    - Fires when pre60 ≥ 15% and reaction ≤ 1% once ≥ 80% of the sector has reported. Before that a provisional reading is shown.
  - **History:** every past firing with forward 60 / 120-session sector excess, so the record is visible next to the live reading.
  - **Display:** a 财报季信号 table in `#sector-monitor` (all L2 sectors, firing ones first, red); one line in the 持仓监测 e-mail when a sector fires; app and e-mail only, no phone alert.
- Out:
  - trading rules or automatic position changes;
  - consensus-based surprise (report_rc coverage is too thin outside large caps);
  - the 白酒-type top, which is a de-rating before the reports. This signal does not see it, and the notes say so.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Earnings events | `EarningsEventBuilder` computes the events in memory on every run (5.5 s for 2019 → today, so no `derived/earnings_events` and no incremental target): ts_code, end_date, first_ann, day0, SUE, decile, pre / react / post excess, NaN until the window is complete | TCs; on 2019-01 → 2026-11 it matches the research run: 140k ± 2% events; top–bottom decile spread pre60 8.9 ± 0.3%, reaction 5.4 ± 0.2%, post20 within ± 0.3% | — | done 2026-11-18 — 141,404 events with a SUE decile (research 140,461); spread pre 8.90%, reaction 5.40%, post 0.13% (research 8.94 / 5.43 / 0.15) |
| 2 | Sector signal | `SectorEarningsSignalBuilder` (SW L2 point-in-time × quarter: n, reported share, top-SUE pre60 / reaction, back120, holder change, status firing / provisional / none; past firings with fwd60 / fwd120); thresholds in `config/sector_earnings_signal.yaml`; writes `sector_earnings_signal.json` | TCs; reproduces the research run: 25 rally + signal cells, fwd60 −6.1 ± 0.3%; 光伏设备 2021Q2 / Q3 and 能源金属 2022Q2 fire; 白酒Ⅱ 2020Q4 does not | 1 | done 2026-11-18 — record after a rally: n 25, fwd60 −6.10%, fwd120 −4.89% (research −6.10 / −4.89); 光伏 2021Q2 / Q3 and 能源金属 2022Q2 fire, 白酒Ⅱ does not; 2026Q3: 轨交设备Ⅱ and 国有大型银行Ⅱ fire |
| 3 | App and e-mail | Go endpoint `/api/sector-earnings`; web table in `#sector-monitor` (latest quarter: sector, reported %, back120, pre60, reaction, holders, status; expandable past firings and outcomes; notes with the definition and its known misses); e-mail line on a new firing; `make sector-earnings-signal` in track-daily | `make check` (pytest, go test, vitest, smoke) passes; screenshot checked; e-mail DRY=1 shows the line on a fixture firing | 2 | done 2026-11-18 — make check 1,063 passed, go ok, vitest 57 passed, lint 0; SMOKE OK (sector earnings: 12 rows); screenshot checked; e-mail line covered by TC-SER-001 |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `EarningsEventBuilder` | new (own single-quarter rule on first versions; no derived table) | calculation | 1 |
| `SectorEarningsSignalSettings` | new | core | 2 |
| `SectorEarningsSignalBuilder` | new | portfolio | 2 |
| `AppServiceBuilder`, `ResearchCommands` | extend (`sector-earnings-signal`) | cli | 3 |
| `SectorEarningsReportSection` (new), `SectorMonitorPage`, `MorningReportBuilder`, chain_api store | extend | visualization, apps | 3 |

## Risks
- 25 historic firings: t −2.9 is real but thin. The tab shows the record, not a promise.
- Early firing in long bull runs (通信设备 2025Q2 / Q3 fired 8 months before the top): the display shows back120 and repeat firings so a first firing is not read as the top.
- Q4 and Q1 are reported together in April: the 2025Q4 and 2026Q1 events share dates, and the first-disclosure date may come from an annual 预告 in January.
- A preview dated before its quarter end (the H1 preview inside the Q1 report) is a real disclosure and counts as the first one, as in the research.
- The signal date is sensitive to the share's denominator: counting all members instead of the events with a SUE moved 能源金属 2022Q2 from 07-15 to 08-15 and the rally record from −6.1% to −5.1%. The research basis (events with a SUE decile) is kept.
- The full build reads ~8M price rows each run (about 6 s).

## Open questions
- (none; defaults: thresholds pre60 15%, reaction 1%, rally 20%, 80% reported, deciles 8–9, ≥ 5 events; all in config)

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-18 | 1–3 | done. Events computed in memory (5.5 s), not a derived table. Definitions aligned with the research after a first build drifted (rally record −1.1%): previews before the quarter end count; deciles only among events with a pre window; share and signal date on events with a decile; signal date = day 0. The command lives in `ResearchCommands` through `AppServiceBuilder` (ReportCommands at its size limit). `MorningReportBuilder` reads the new document; the e-mail block is `SectorEarningsReportSection` |
| 2026-11-18 | — | approved (user: "可以") |
| 2026-11-18 | — | drafted from research runs 20261118_priced_in, 20261118_priced_in_tech and 20261118_sector_peak_signal (user: "可以，写个计划做进") |
