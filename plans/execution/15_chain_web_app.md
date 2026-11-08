# 15 — Industry-chain web app (React + Go)

| | |
|---|---|
| Status | approved 2026-11-08 (user: "现在本地demo"), local only; doing phases 1, 3, 4 first |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-08 |
| Notion | pending |
| Decisions | D-116, D-099, D-104, D-115 |
| Depends on plans | 12 (graph, CompanyCard), 13 (broker views) |

## Goal
A local web app replaces the single-file prototype `research_space/prototypes/chain_view`. The React front end calls a read-only Go API, and the API serves tables that the Python pipeline writes. It offers search, company pages, sector networks and product pages, with the same tabs as the prototype.

## Scope
- In:
  - Python step that writes the graph and CompanyCard tables (`derived/graph/*.parquet`). It moves the logic of `build_market_view.py` into classes.
  - Go API (read-only, DuckDB over those parquet files, OpenAPI contract).
  - React + TypeScript front end (Vite, Cytoscape.js).
  - One local binary that serves the built front end.
  - Standards addendum for Go and TypeScript, and `make` targets.
- Out:
  - Any extraction or business logic in Go or TypeScript: all of it stays in Python (no duplication).
  - Writes from the app.
  - Public hosting and user accounts (open question).
  - The US chain.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Decision and standards | D-116 accepted. `plans/standards/` addendum for Go and TS: contracts = OpenAPI plus doc comments, tests, `golangci-lint` / `eslint`, size limits. Folders `apps/chain_api/` and `apps/chain_web/` with INDEX.md. `make app-check` | User approves D-116. `make app-check` runs lint and tests on both empty skeletons and is wired into `make check` | — | todo |
| 2 | Graph export (Python) | `CompanyCardBuilder` (industry_graph) and `GraphExportStep` (pipeline). They write `derived/graph/{companies, revenue_lines, nodes, edges, company_links, counterparties, applications, broker_views, valuation_stats, business, cycle_clock, quarterly_notes}.parquet` with the prototype's logic moved into tested classes | Contract tests per class pass. Row counts match the prototype (5,676 companies, 891 product clocks, ...). `build_market_view.py` reads the tables instead of computing them | 1 | todo |
| 3 | Go API | `apps/chain_api`: an `openapi.yaml` contract, and handlers for `/search`, `/companies/{code}`, `/nodes/{id}`, `/sectors/{l1}/network`, `/views/{scope}/{id}`. DuckDB is opened read-only on the parquet files, never on the catalog file | `go test ./...` passes against fixture parquet. Every endpoint is validated against `openapi.yaml`. p95 latency < 200 ms on the full lake, measured locally | 2 | todo |
| 4 | React shell | `apps/chain_web`: search, company page with all prototype tabs, swim-lane graph, zoom / fullscreen / resizable panel. Typed client generated from `openapi.yaml` | Vitest unit tests pass. A Playwright smoke test opens 5 companies (牧原, 宁德时代, 立讯, 茅台, 中国平安) and every tab without console errors | 3 | todo |
| 5 | Networks and product pages | Sector company network, product / segment pages (makers, valuation view, cycle clock), industry pages | The Playwright smoke test covers 3 sectors and 3 products. Visual parity with prototype v14 is checked by the user | 4 | todo |
| 6 | Package and hand over | `make app` builds the front end and embeds it in one Go binary; `make app-run` starts it. README in `apps/`. The prototype is kept as a reference | `make app-run` serves the app on localhost from a clean checkout. `make check` passes (real output pasted). Registry and INDEX files are current | 5 | todo |

## Classes

| Class / package | Action | Package | Phase |
|---|---|---|---|
| `CompanyCardBuilder` | new | `quant_cn.industry_graph` (L4) | 2 |
| `GraphExportStep` | new | `quant_cn.pipeline` (L6) | 2 |
| `ProductTaxonomy`, `ProductMatcher`, `BrokerViewSynthesizer`, `AnnualReportParser` | reuse | `quant_cn.industry_graph` | 2 |
| `LakeCatalog`, `LakeQuery` | reuse | `quant_cn.lake` | 2 |
| Go packages `api`, `store`, `search` | new | `apps/chain_api` | 3 |
| React feature modules `company`, `network`, `product`, `search` | new | `apps/chain_web` | 4–5 |

## Risks
- **Three languages to maintain.** Mitigation: Go and TS only read and display; one OpenAPI contract; the standards addendum before any code.
- **The exFAT volume** broke the Python venv. `node_modules` and the Go build cache may have the same problem. Mitigation: keep the caches under `$HOME`, as done for the venv.
- **The DuckDB single-writer lock.** Mitigation: the API reads parquet with a separate in-memory DuckDB, never `meta/quant_cn.duckdb`.
- **go-duckdb needs cgo.** Mitigation: pin a version and build on macOS arm64 first. If it blocks, the fallback is Arrow/parquet-go reads.
- **Logic drifting back into the front end** (e.g. similarity or clocks computed in the browser). Mitigation: phase 2 puts every number into a table, and code review checks it.

## Open questions
- Hosting: answered 2026-11-08: local demo on this Mac for now (no auth, localhost only).
- Who uses it besides you? (sharing and accounts)
- Should the front end keep the claude.ai artifact as a shareable snapshot, or retire it after phase 6?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-08 | — | drafted (user: "可以用go来做后端，前端用react", "app的搭建如何了") |
| 2026-11-08 | — | approved for a local demo (user: "现在本地demo"). Order changed to 1 → 3 → 4 → 5 → 2 → 6: for the demo the Go store reads the prototype builder's JSON (view_data.json, co/, views.json) behind a `Store` interface; phase 2 replaces it with `derived/graph` parquet without changing the API. Node 22 arm64 installed via Homebrew (the x86 node cannot run). Front-end deps build in `$HOME/.builds/chain_web` (exFAT has no symlinks) |
| 2026-11-08 | 1, 3, 4 | APP_STANDARD.md; Go API (`JSONStore`, 6 endpoints, TC-ST-001..006, TC-API-001..006, p95 < 40 ms on full data); React app (all prototype tabs + financial table D-117), vitest TC-EL-001..004, Playwright smoke 5 companies / 3 sectors / 3 nodes / search: SMOKE OK; `make app-run`, `app-check` wired into `make check`. Go 1.21 binaries fail on this macOS (missing LC_UUID): Homebrew Go 1.27 used |
| 2026-11-08 | 4 | colour palette per node type (light / dark), lane wrapping; FY2023–25 financial table (D-117) with 年度 / 单季度 switch (last 8 single quarters, YoY); segment leaders (top 5 by mapped revenue; fallback lines only when ≥ 40% of revenue; delisted excluded) on node pages and ranks on company products; DuPont path (asset turnover × ROE, FY2019→2026Q3 annualised, L3 FY2025 cloud) in the 商业模式 tab. All numbers computed in the Python builder. Smoke OK |
| 2026-11-08 | 4–5 | DuPont plane: fixed axes (turnover 0–2, ROE −20–40%, edge markers), whole-market cloud per fiscal year (FY2019–FY2025, from Python), L3 peers highlighted; play / pause / slider per company (cloud follows the year); sector tab 杜邦坐标 (all sector companies, click to open). Smoke OK |
| 2026-11-08 | 5 | dedicated 杜邦坐标 page (#dupont=codes): pick companies (search or click), colour per path, sector highlight, whole-market play FY2019→2025, comparison table; header switch 产业链图谱 / 杜邦坐标. Interaction test + smoke OK |
| 2026-11-08 | 5 | DuPont page: chart fills the panel (viewBox 1200×760, height follows the window), larger labels and points; every point hoverable (tooltip: name, code, sector, L3, year, ROE, turnover) and clickable (DuPont page: add / remove from comparison; company and sector planes: open the company). `names` lookup added to bootstrap. Server restart now `pkill -f "chainapi -data"` (the old pattern also matched queued shell jobs) |
| 2026-11-08 | 5 | DuPont market cloud now ends with the latest quarter (2026Q3, annualised ×4/3; 5,515 companies that reported it) as the final frame of the slider and play; company plane background follows the selected point's period |
| 2026-11-08 | 5 | DuPont driver and warning per point (Python): driver margin / turnover / leverage / mixed; flag thin (multiplier ≥ 5) or gap (npm × turnover × multiplier vs ROE > 30% or sign); flagged points hollow, tooltip shows driver and warning, DuPont page filter by driver and "hide distorted ROE", company DuPont table column. 2025: margin 990, turnover 236, leverage 702, mixed 3,700; thin 316, gap 350 |
