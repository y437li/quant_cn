# 19 — App Store game charts

| | |
|---|---|
| Status | approved 2026-11-11 (user: "可以track"); ph1 done, ph2 todo |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-11 |
| Notion | pending |
| Decisions | D-137, D-063, D-120 |
| Depends on plans | 01 (lake, fetchers), 15 ph7b (`make track-daily`) |

## Goal
A daily, point-in-time record in the lake of the Apple App Store game charts (top grossing and top free, top 100) for each country / region, linked to listed publishers, so a game's rank path (e.g. 巨人 《超自然行动组》 / 《TombBusters》) can be read next to its quarterly revenue and contract liabilities.

## Scope
- In: Apple's public iTunes RSS feeds (`itunes.apple.com/<cc>/rss/<chart>/limit=200/genre=6014/json`, no key, returns at most 100 rows); charts `topgrossingapplications` and `topfreeapplications`; the markets in `config/app_charts.yaml` (proposed 26: cn us jp kr tw hk sg th id my ph vn in gb de fr it es ca au br mx tr sa ae ru); a publisher → `ts_code` map for A-share and HK-listed game companies; a per-company daily summary view.
- Out: history before the first capture (Apple has no history; 七麦 / 点点 / Sensor Tower need logins or payment); Google Play and Chinese Android stores (no public chart API); download or revenue estimates; an app page (a later plan 15 phase if wanted).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Daily capture | `AppStoreClient(BaseWebClient)` returns one chart as rows (rank, app_id, name, artist, artist_id, bundle_id, release_date, price, country, chart, captured_at); new sweep kind `snapshot` (`SnapshotFetcher`: one key per capture date from `Clock`, values = country × chart, never backfills) registered in `FetcherFactory`; dataset `app_store_charts` in `config/datasets.yaml` (`primary_key` [capture_date, country, chart, rank], `known_on` capture_date, same-session rule); added to `make track-daily` | TCs for paging-free parse, empty or 404 market skipped and logged, rerun on the same date replaces and does not duplicate, past dates never fetched; first real capture: 26 × 2 charts, ≥ 95% of feeds at 100 rows, 《超自然行动组》 found in cn top grossing; `make check` passes | — | done |
| 2 | Publisher link + summary | `config/app_publishers.yaml` (artist_id → ts_code, company, listing: A / HK / US; seeded with 巨人, 三七互娱, 吉比特, 完美世界, 世纪华通, 恺英, 腾讯, 网易, 米哈游 marked unlisted, …); `derived.app_chart_company` view: per (date, ts_code, country, chart) best rank, apps in top 10 / 50 / 100, and a per-app rank series with 7- and 30-day mean ranks | Every top-grossing cn app whose publisher is in the map is linked; unmapped publishers above rank 50 listed in the Log for review; the 巨人 tracker (`meta/runs/track_giant.py`) prints cn + overseas ranks with 7 / 30-day means from the view; `make check` passes | 1 | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `AppStoreClient` | new (subclass `BaseWebClient`, like `CninfoClient`) | `quant_cn.data_loading` | 1 |
| `SnapshotFetcher` | new (`BaseFetcher` subclass for "today only" sweeps) | `quant_cn.data_loading.fetchers` | 1 |
| `FetcherFactory`, `ServiceBuilder` | extend (new kind, new client) | `quant_cn.data_loading`, `quant_cn` | 1 |
| `DerivedViews` | extend (`app_chart_company`) | `quant_cn.lake` | 2 |

## Risks
- Apple may change or retire the legacy RSS endpoint (the newer `rss.applemarketingtools.com` has no grossing chart); the client fails loudly and the Log records the date.
- Charts move within the day; one capture per day at the `track-daily` time (18:30 Beijing) is a snapshot, not an average, and event days spike.
- iOS only: in China Android and mini-game channels (抖音, 微信) are likely the larger share for some titles; ranks are relative, so a weaker field lifts a falling game.
- Publisher names differ by market (Giant Games, Inc. vs 巨人网络); matching is by `artist_id`, and new subsidiaries need manual map entries.

## Open questions
- Market list: the 26 above, or add more (e.g. Latin America beyond br / mx for the 2027 Garena launch)?
- Also capture top paid, or the overall (all-genre) charts? Each adds 26 calls a day.
- Capture time: 18:30 with `track-daily`, or a separate early-morning job (charts at the end of the China day)?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-12 | 1 | done: first capture 20261112 26 stores × 2 charts = 52 feeds, all at 100 rows (5,200 rows, 0 duplicate keys); 《超自然行动组》 cn grossing #60, cn free #37; 《球球大作战》 cn free #40. Bug found and fixed on the way: the client emitted an empty `capture_date` column, so BaseFetcher (fills key_field only when absent) left it null and compact wrote 0 partitions; the client no longer emits the column (TC-ASC-001 asserts it). Re-captured with `--force`. `make check` green: 639 passed, 96% coverage, lint_contracts 0 |
| 2026-11-11 | 1 | built: `AppStoreClient` (TC-ASC-001..003), `SnapshotFetcher` (TC-SNF-001..003), sweep kind `snapshot` + source `apple` (TC-DS-010), factory mapping (TC-FF-001), dataset `app_store_charts` (26 stores in `config/datasets.yaml` sweep values; no separate `AppChartSettings`/`config/app_charts.yaml` needed), `make app-charts` in `track-daily`. `make check` green: 639 passed, 96% coverage, lint_contracts 0. First real capture queued behind the risk-model lock |
| 2026-11-11 | — | approved (user: "可以track"); open questions taken at the defaults: 26 markets, grossing + free only, capture in `track-daily` at 18:30 |
| 2026-11-11 | — | drafted at the user's request ("在湖里 track一下各个国家，各个地区的苹果畅销榜和免费榜游戏"); probe on 18 markets: feeds return 100 rows; 《超自然行动组》 cn top grossing #54; 《TombBusters》 (app id 6755951087, Giant Games, Inc.) absent from the top 100 grossing and free in all 18 |
