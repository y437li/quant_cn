# 16 — Structural deduction pipeline (结构性推演流程)

| | |
|---|---|
| Status | drafted, awaiting approval |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-09 |
| Notion | pending |
| Decisions | D-121 (proposed), D-112, D-118, D-116, D-005 |
| Depends on plans | 11 (statements, fut_daily, report_rc), 12 (taxonomy graph, uses_material edges), 15 (app) |

## Goal
A repeatable, point-in-time pipeline: once per quarter after earnings (and weekly for prices), it computes four dimensions for every SW L3 industry and taxonomy product: price, margins, efficiency and structure. It labels each industry's structural state with explicit rules and traces the moves in material prices to the companies that make and use each material. It ranks the survivors in industries that are clearing and turns target prices into required earnings scenarios. A historical replay checks every label before the app shows it as reliable.

## Scope
- In:
  - Implements BUSINESS_MODEL_DESIGN §4.2 (cycle clock), §4b.4 (competition) and §4b.5 (sensitivity) as classes. Logic is moved out of the prototype (`build_market_view.py` clock and P3 slope) and out of the 2026-11-09 scratch scans (`chain_scan.py`, `structure_scan.py`).
  - Rules live in `config/deduction_rules.yaml`.
  - Outputs: `derived/deduction/*.parquet` plus JSON for the app.
  - New app page 推演.
- Out:
  - LLM narrative.
  - New datasets: freight index, agricultural spot prices (青菜头, 鹌鹑蛋) and lithium makers' mapping gaps go to plan 11 / plan 12 as open items.
  - Trading signals and portfolio construction (plan 06).
  - Any computation in Go or TypeScript (D-116).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Industry metrics (PIT) | **Company TTM panel at each quarter-end as known on `as_of`** (ann_date ≤ as_of; uses the historical SW membership): revenue, GM, NM, asset turnover, ROE, capex/depreciation (annual), loss flag. Aggregated per SW L3 and per taxonomy product (fina_mainbz). Matched sample for changes, plus median alongside the sum. CR3, entrants and exits. Written to `derived/deduction/industry_metrics.parquet` | Contract tests pass. Numbers at as_of 2026-11-06 match the scratch scan within rounding (PCB GM 26.8%, capex/dep 2.6; 硅料硅片 loss share 100%). No row uses a statement announced after as_of (test) | — | todo |
| 2 | Structure classifier | Rules for 新兴扩张 / 进入广泛竞争 / 出清·进行中 / 出清·见底 / 供给锁定 / 格局改善 / 无, with thresholds in `config/deduction_rules.yaml`. Each label stores the rule trace (which conditions fired). The trajectory over the last 8 quarters feeds the cycle clock, replacing the prototype's `clock_l3` | One test per rule edge. Labels for every L3. The user spot-checks 30 labels; the bar is ≥ 85% (BMD §4b.6) | 1 | todo |
| 3 | Price transmission and margin nowcast | Material price index (continuous contracts, `material_prices.yaml`). Maker and user exposure per company from graph edges, weighted by revenue share. Per-company pass-through slope (ΔGM on Δindex, lagged 0–2 quarters). Next-quarter GM nowcast compared with the consensus EPS revision (report_rc, 30 and 90 days) | Tests pass. On 2023Q1–2026Q3 replays the nowcast beats a naive "last GM" forecast for companies with a measured slope (MAE reported). Flag list: costs moved but consensus has not | 1 | todo |
| 4 | Company layer and scenarios | **Survivor ranking** in clearing industries: net cash, cost position (GM rank in L3), capex discipline, loss streak, debt maturity. **Scenario valuer**: price = EPS × PE at the 5-year min / p10 / median, crossed with EPS paths (flat / −10% / −25% / consensus). It also gives consensus-implied profit for the remaining quarters and the scenario needed to reach a target price. `WatchlistBuilder` adds the scenario grid | Tests pass. The 2026-11-06 values reproduce: 盐津 implied Q4 profit ≈ 1.63 亿, 25 元 = 9.3× TTM; 涪陵 10 元 = 16.3× | 1 | todo |
| 5 | Historical replay (validation) | Run phases 1–3 at every quarter-end as_of from 2019 (PIT). For each label measure the next-4-quarter margin change and the return relative to SW L1, with NW t and a block bootstrap (`statistic`). Thresholds are frozen before the replay. Report notebook | Every label has a hit rate and t-stat in the notebook. A label is marked `validated` only if its direction holds with t ≥ 2; otherwise the app shows it as `descriptive` | 2, 3 | todo |
| 6 | Pipeline and app page | `DeductionStep` and `make deduction` (prices weekly, statements after each season) write parquet plus `deduction.json`. Go `GET /api/deduction`. React `#deduction`: industry map (4 dims, label, trajectory), transmission table, survivors, scenarios; links to company pages and the watchlist | `make check` passes (real output). Smoke opens `#deduction` and 3 industries. Registry and INDEX files are current | 2–5 | todo |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `IndustryMetricsBuilder` (company TTM panel + L3 / product aggregates) | new | `quant_cn.industry_graph` (L4) | 1 |
| `PitAligner`, `LakeQuery`, `DateCodec` | reuse | `lake`, `core` | 1 |
| `StructureClassifier` | new | `quant_cn.industry_graph` | 2 |
| `MaterialPriceIndex`, `TransmissionMapper`, `MarginNowcaster` | new (check plan 10 `ContinuousFutures` first; extend it if built) | `quant_cn.industry_graph` | 3 |
| `SurvivorRanker` | new | `quant_cn.industry_graph` | 4 |
| `ScenarioValuer` | new | `quant_cn.portfolio` (L7) | 4 |
| `WatchlistBuilder` | extend (scenario grid) | `quant_cn.portfolio` | 4 |
| `DeductionReplay` | new; uses `statistic` NW t / bootstrap | `quant_cn.back_testing` | 5 |
| `DeductionStep` | new | `quant_cn.pipeline` | 6 |
| Go `store.GetDeduction`, handler; React feature `deduction` | new | `apps/chain_api`, `apps/chain_web` | 6 |

Names and packages are final only after the `naming` skill.

## Risks
- **Look-ahead and survivorship.** Using current SW membership and restated statements would flatter the replay. Mitigation: ann_date ≤ as_of, historical `index_member_all`, and delisted companies kept.
- **Aggregates dominated by giants.** Mitigation: medians and the matched sample shown beside the sums; the product level comes from fina_mainbz.
- **Overfitted thresholds.** Mitigation: freeze the thresholds before phase 5, report all labels, and mark unvalidated labels `descriptive`.
- **Unlisted capacity is invisible** (量贩零食, private PV capacity). Mitigation: shown as a coverage note per industry (listed revenue vs industry revenue where known).
- **Mapping gaps** (lithium makers, freight, farm inputs) leave holes in the transmission layer. Mitigation: a coverage column per material, and the gaps listed in plan 11 / 12.

## Open questions
- Package for phases 1–3: `industry_graph` (proposed) or a new L4 package `industry_structure`?
- Is the product level (fina_mainbz → taxonomy nodes) in phase 1, or a later phase after L3?
- Refresh cadence: prices weekly, statements after each earnings season. Add launchd?
- Should the scenario grid use PE only, or also PB for cyclicals and EV/EBITDA for heavy-asset industries?
- Add the missing data to plan 11 now (SCFI / CCFI freight, agricultural spot)?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-09 | — | drafted (user: "做一套流程，能够做详尽的推演的"); based on the 2026-11-09 scans (chain transmission over 40 materials; four-dimension L3 scan of 255 industries) |
