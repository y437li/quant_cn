# 20 — Manual and public cycle series (手工序列)

| | |
|---|---|
| Status | approved 2026-11-12 (user: "把船价指数追踪的计划20批了吧"); phase 1 done; phase 2–4 todo |
| Owner | user (approve, licensed exports) / agent (build, monthly refresh) |
| Created | 2026-11-12 |
| Notion | pending |
| Decisions | D-139, D-120, D-005, D-121 |
| Depends on plans | 11 (sources, `known_on_rule`), 15 ph7f (position notes), 16 ph1 (cycle panel) |

## Goal
Cycle signals that Tushare does not carry are in the lake as point-in-time series, each row with its source, and are shown next to the holdings and watchlist names they drive. Examples: the Clarksons newbuilding price index, TiO2 and ilmenite prices, freight indices.

## Scope
- In:
  - Committed `config/manual_series.yaml` for public data (series definitions plus observations with a source URL).
  - Git-ignored `config/local.manual_series.yaml` for licensed exports (Wind / Choice / iFinD) entered by the user.
  - Curated dataset `alt/manual_series` with PIT `known_on` = publication date.
  - akshare-backed public series where akshare covers them, through the existing `source: akshare` path.
  - Links from series to position notes and the watchlist, and staleness flags.
  - A monthly refresh checklist for the agent.
- Out:
  - Paid subscriptions or terminal APIs (WindPy needs a logged-in terminal; D-005 / plan 16 exclude new paid data).
  - Scraping sites against their terms.
  - Computation in Go / TS (D-116).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Series file and loader | `config/manual_series.yaml`: `series` (id, name, unit, freq, kind = index / price / spread, region, links: [ts_code]) and `observations` (series, date, value, published, source_url, note); same shape in `config/local.manual_series.yaml`. `ManualSeriesLoader` validates (known series id, published ≥ date, no duplicate (series, date) unless `revision: true`), merges both files and writes curated `alt/manual_series` (series, date, value, known_on, source_url, licensed). View `curated.manual_series`; `make manual-series`; runs in `track-daily`. Seed rows: Clarksons NewBuild 2026-02 182.1 … 2026-10 187.2 with URLs from the 2026-11-12 session | TCs: unknown series → ConfigError naming the row; published < date → error; duplicate without revision → error; a revision keeps both rows and the view returns the latest `known_on ≤ as_of`; local file missing → public rows only; licensed rows never leave git-ignored paths (test on the writer's output path). `make check` passes | — | done 2026-11-12 (uncommitted): source "manual" = `data_loading.ManualSeriesClient` (TC-MSC-001..003) on the normal download / compact path (no separate writer); dataset `manual_series` → curated `alt/manual_series`, known_on = published; `make manual-series` (in `track-daily`); real lake: 5 Clarksons rows 182.14 (2026-02-27) … 187.2 (2026-10-31). The latest-`known_on` read is phase 3 (`ManualSeriesReader`); licensed rows only reach the lake, which is outside the repo. make check exit 0: lint_contracts 0, 643 passed, vitest 21, project.stale 0 |
| 2 | Public series from akshare | Check akshare coverage first (BDI / BCI / BPI family, SCFI or CCFI, TiO2 / ilmenite spot if any) and add the covered ones as normal `datasets.yaml` entries with `source: akshare`, mapped into the same series ids. Uncovered series stay manual | Coverage table in this plan (series → akshare function or "manual"). Each added dataset passes the standard fetcher contract tests on a recorded fixture. `make check` passes | 1 | todo |
| 3 | Use in notes, watchlist and morning report | `ManualSeriesReader.read_latest(series, as_of)` and `read_changes(series, as_of)` (1 m / 3 m / YoY). Position notes and watchlist entries may list `series: [id]`; `HoldingsRiskBuilder` / `WatchlistBuilder` attach latest value, change and staleness (older than 1.5 × freq). The 7e morning report shows them under each name. For 中国船舶 the panel also shows HC and EC futures (already in `fut_daily`) | TCs: PIT (a row published after as_of is invisible); staleness boundary; a note naming an unknown series → ConfigError. App shows the Clarksons series next to 中国船舶 and TiO2 next to 龙佰. `go test`, vitest, smoke. `make check` passes | 1, plan 15 ph7f | todo |
| 4 | Refresh routine | `.claude/skills/manual-series/SKILL.md`: which series, where to look (publisher pages, eworldship / xindemarinenews monthly reports, company announcements), how to record (value, published date, URL), and the rule that conflicting sources are recorded as separate rows with a note. The holdings-review session runs it monthly | Skill file exists and is indexed; one refresh run adds the November rows with URLs and flags no stale series | 1 | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `ManualSeriesLoader` | new (name via `naming`) | `quant_cn.data_loading` | 1 |
| `ManualSeriesReader` | new | `quant_cn.lake` | 3 |
| `DatasetSpec`, akshare fetchers | reuse / extend | `quant_cn.core`, `quant_cn.data_loading` | 2 |
| `PositionsBook` (`PositionNote.series`), `WatchlistBuilder`, `HoldingsRiskBuilder` | extend | `quant_cn.core`, `quant_cn.portfolio` | 3 |
| `ParquetWriter`, `DerivedViews` | reuse | `quant_cn.lake` | 1 |

## Risks
- Hand-entered values are wrong or transcribed from secondary sources. Mitigations: every row carries a URL, conflicting sources are kept side by side, and the monthly refresh re-checks the last value.
- Media sources disagree on timing and definitions (e.g. order counts 1,644 vs 1,481 for 2026 H1). Mitigation: a per-row note and one preferred source per series.
- Licensed data leaks into git. Mitigation: a separate git-ignored file, plus a test on the output path and a `licensed` flag.
- Monthly series are too slow for trading decisions. They are context for cycle position, not signals; the plan does not change that.
- akshare endpoints break. Mitigation: phase 2 keeps a manual fallback per series.

## Open questions
- Which series first? Proposed list:
  - Clarksons NewBuild price index (中国船舶);
  - TiO2 rutile domestic price and ilmenite price (龙佰);
  - BDI (dry bulk, context for shipping);
  - lean hog spot vs LH futures basis, plus sow inventory from the 农业农村部 monthly release (牧原 and 回盛).
- Will you export the TiO2 and Clarksons history from Wind once (git-ignored local file), so the series starts with a long history instead of a few months?
- Where should the series appear first: the holdings page (ph3) only, or also as a separate small `#series` page?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-12 | 1 | Done (see phase row). Seed: Clarksons NewBuild 5 points with URLs; uncertain article dates use the capture day as `published` (conservative PIT) |
| 2026-11-12 | all | Approved (user: "把船价指数追踪的计划20批了吧"); phase 1 started. First series: Clarksons NewBuild index (中国船舶). Open questions on the other series stay open |
| 2026-11-12 | all | Drafted, awaiting approval. User: "把手工序列数据集写成计划", after "tushare里面有吗" / "wind里会有这些数据吗". Tushare has no shipbuilding price index or TiO2 price; Wind EDB likely has both but is licensed and terminal-bound |
