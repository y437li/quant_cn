# 16 — Opportunity discovery and market-implied deduction (机会发现与推演流程)

| | |
|---|---|
| Status | approved 2026-11-09 (user: "都行"); doing phase 1 |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-09 |
| Notion | pending |
| Decisions | D-121, D-112, D-118, D-116, D-005 |
| Depends on plans | 11 (statements, fut_daily, report_rc, margin_detail), 12 (chain graph), 15 (app) |

## Goal
A repeatable pipeline that finds opportunities without being given ideas. For every A-share company and industry it answers, point in time, three questions:
- **Where is it in its own cycle?**
- **How much does today's price already pay for?** This is updated daily from prices and futures curves.
- **Where does that disagree with consensus and the chain evidence?**

It then hands the ranked gaps to a standard, source-tagged deep-dive workflow (industry agents plus chain deduction), verifies the agents' numbers against the lake, and shows the result in the app.

## What v1 got wrong (2026-11-09 sessions)
- **Industry description is not discovery.** v1 started from L3 labels.
- **YoY alone misled.** Memory modules looked like an inflection; Q3 profit had already halved QoQ.
- **"Low PE" was read as an opportunity.** For cyclicals at peak margins it is the opposite (周期股卖便宜买贵).
- **"Cheap" is the wrong question; "priced in" is the right one.** Aluminium at PE 6.4 already pays for about 7.6 years of excess profit.
- **Each agent used its own profit base,** which gave opposite answers on the same stock (中远海能: 0 vs 32 years priced).
- **Claims mixed computed facts, broker views, news and assumptions without labels.** 4 of 17 checked numbers needed correction (VERIFY.md).

## Scope
- In:
  - Company cycle panel (PIT, deducted profit).
  - Market-implied expectations: years priced, the commodity price implied against the futures curve, and reverse DCF.
  - Idea screens, with rules in `config/discovery_rules.yaml`.
  - Financial-sector metrics: NIM, asset quality, turnover, premiums.
  - Deep-dive workflow: brief templates, source-tag schema, and an automatic recheck of [自算] claims.
  - Historical replay.
  - App page and watchlist fields.
- Out:
  - Trading and portfolio construction (plan 06).
  - New paid data. Gaps go to plan 11: memory contract prices, freight index, agricultural spot, sulphur and coal spot series.
  - Any computation in Go / TS (D-116).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Company cycle panel | **Per company and quarter-end as known on `as_of`** (ann_date ≤ as_of): single-quarter and TTM revenue, GM, net and deducted profit (`profit_dedt`), YoY **and QoQ**, 10-year median profit, 10-year max margin, `margin_peak`, ROE and turnover. The SW L3 four-dimension aggregates are kept as context columns. Financials get their own block: NIM, NPL, provision coverage, credit cost, turnover share, premiums and NBV where available. Writes `derived/discovery/company_panel.parquet` | Contract tests pass. No row uses a statement announced after as_of (test). The 2026-11-06 values match VERIFY.md (e.g. 江波龙 Q3 QoQ −44%, 药明 deducted TTM 202 亿) | — | done 2026-11-09 (uncommitted): make check green — ruff, mypy 149 files, layers KEPT, lint_contracts 0, 513 passed, Go ok, vitest 12; 6,504 companies in 26 s on the lake; 江波龙 Q3 QoQ −44%, 药明 deducted TTM 202 亿 reproduced. Financial block deferred (NIM / NPL / premiums not in the lake; see Log) |
| 2 | Market-implied expectations (daily) | **Years priced:** excess profit over three fixed bases (10-year median × normal PE, pre-cycle market cap, and the industry median PE), all shown. **Commodity-implied price:** profit sensitivity per company (disclosed volumes or a regression on the material index) is solved for the price that justifies the market cap, then compared with the back-month futures curve (`fut_daily`). **Reverse DCF** implied growth compared with the consensus path (report_rc) | Tests pass. Today's values reproduce: 云铝 ≈ 7.6 years, 中国铝业 ≈ 10.8, 中远海控 ≈ 4.5; lithium-carbonate curve flat at about 92k against 天齐 ≈ 30 years. Base sensitivity reported per stock | 1 | todo |
| 3 | Idea screens and ranking | Rules in `config/discovery_rules.yaml`: inflection with QoQ confirmation, turnaround, de-rated quality, demand acceleration, crowded deterioration, cleared-industry price turn, cost move not in consensus, zero coverage, peak-margin warning. Ranked by the **gap between what is priced and the evidence**; output per industry, including small caps (≥ 20 亿) and financials | Tests per rule edge. On 2026-11-06 the screen returns the round-1 picks with their warnings (memory = peak trap, aluminium = largely priced). Run time < 5 min | 1, 2 | todo |
| 4 | Deep-dive workflow and claim verification | Versioned brief templates (`research_space/briefs/`, from BRIEF / INDUSTRY / SMALLCAP.md). A claims table schema (claim, value, source type [自算/研报/新闻/假设], query or URL, sensitivity). `ClaimVerifier` recomputes every [自算] claim from the lake and flags mismatches. A Workflow script runs one agent per 产业大类 plus small caps plus financials, then a synthesis pass. Reports are stored with as_of | The verifier reproduces VERIFY.md (4 mismatches flagged out of 17). One full run produces reports for all groups, a cross-industry synthesis and a verified claims table | 3 | todo |
| 5 | Historical replay | Phases 1–3 run at every quarter-end from 2019 (PIT; historical SW membership; delisted companies kept). For each screen and for the priced-in gap, measure the next-4-quarter excess return against SW L1 and the margin change, with NW t and block bootstrap. Thresholds are frozen before the run | Each screen is labelled `validated` (t ≥ 2, right sign) or `descriptive`. Report notebook | 3 | todo |
| 6 | Pipeline, app and watchlist | `DiscoveryStep` with `make discovery` (prices and futures daily, statements after each season). Go `GET /api/discovery`. React `#discovery`: ranked gaps, cycle position, years priced, implied price against the futures curve, report links with source tags. `WatchlistBuilder` adds years priced and cycle position | `make check` passes (real output); smoke test opens `#discovery`; registry and INDEX files are current | 2–5 | todo |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `CompanyCyclePanel` | new | `quant_cn.calculation` (L4) | 1 |
| `StatementVersionReader` (statement values known on as_of; keeps the panel pure) | new | `quant_cn.lake` (L2) | 1 |
| `DiscoverySettings` (base.yaml `discovery`) | new | `quant_cn.core` (L1) | 1 |
| `PitAligner`, `LakeQuery`, `DateCodec` | reuse | `lake`, `core` | 1 |
| `FuturesCurve` (back-month curve per material; plan 10 `ContinuousFutures` is not built, so a new class) | new | `quant_cn.calculation` | 2 |
| `ImpliedExpectations` (years priced, implied price, reverse DCF) | new | `quant_cn.calculation` | 2 |
| `IdeaScreener` | new | `quant_cn.portfolio` (L7) | 3 |
| `ClaimVerifier` | new | `quant_cn.portfolio` | 4 |
| Workflow script and brief templates | new (not package code) | `research_space/briefs/`, `.claude/workflows/` | 4 |
| `DiscoveryReplay` | new; uses `statistic` | `quant_cn.back_testing` | 5 |
| `DiscoveryStep` | new | `quant_cn.pipeline` | 6 |
| `WatchlistBuilder` | extend | `quant_cn.portfolio` | 6 |
| Go `store.GetDiscovery`, handler; React feature `discovery` | new | `apps/chain_api`, `apps/chain_web` | 6 |

Names and packages are final only after the `naming` skill.

## Risks
- **The definition of "normal" drives "years priced".** Mitigation: three fixed bases always shown side by side, and no single number is presented as the truth.
- **Look-ahead and survivorship in the replay.** Mitigation: ann_date ≤ as_of, historical membership, delisted companies kept.
- **Agent hallucination and unverifiable news.** Mitigation: source tags are mandatory; [自算] claims are rechecked automatically; [新闻] claims need two sources or are marked unverified; [假设] claims carry a sensitivity.
- **Cost of the agent runs** (about 1.6M tokens for 10 agents on 2026-11-09). Mitigation: the deep-dive runs only on the ranked top gaps; a quarterly cadence; the user approves each run.
- **Data gaps** (memory prices, freight, farm and sulphur spot, bank NIM fields). Mitigation: a coverage column per screen; the gaps are listed in plan 11.

## Open questions
- ~~Replay before the app page~~ answered 2026-11-09: yes (phase order 1 → 2 → 3 → 4 → 5 → 6 kept).
- ~~Normal PE~~ answered 2026-11-09: both shown. The fixed 12 is the primary base; the stock's own 10-year median PE is the second base, next to the pre-cycle market cap.
- ~~Deep-dive cadence~~ answered 2026-11-09: after each earnings season, plus a trigger when a top-ranked gap crosses the threshold; each run is approved by the user (cost).
- ~~Financials~~ answered 2026-11-09: kept in plan 16 (phase 1 block, phase 3 screens).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-09 | — | v1 drafted (user: "做一套流程，能够做详尽的推演的") |
| 2026-11-09 | — | v2 rewrite (user: "改写计划16"): from industry labels to discovery → priced-in → deep dive → verify; lessons from round 1 (QoQ, 卖便宜买贵, priced-in, common base, source tags); classes and phases replaced |
| 2026-11-09 | — | approved (user: "都行"); open questions answered with the proposed defaults; D-121 accepted; phase 1 doing |
| 2026-11-09 | 2 | `FuturesCurve` + `CurveSummary` (calculation, TC-FCV-001..005) built in parallel by the chain-graph session (agreed with the phase-1 session): curve per family / material from fut_daily + fut_basic, slope from the most-held month; 2026-11-06 check: 碳酸锂 flat at ~91.9k (+0.2%), 沪铝 −1.9%, 原油 −11.9% backwardation |
| 2026-11-09 | 1 | Done. `core.DiscoverySettings` (TC-C-017), `lake.StatementVersionReader` (TC-SVR-001..004), `calculation.CompanyCyclePanel` (TC-CCP-001..009). Deviations: (a) the panel is pure (calculation has no I/O), so the lake read is the new `StatementVersionReader`; (b) writing `derived/discovery/company_panel.parquet` moves to `DiscoveryStep` (phase 6); (c) the financial block (NIM, NPL, provision coverage, premiums, NBV) is not in fina_indicator_vip, so it moves to phase 3 and needs a plan 11 dataset (bank / insurer indicators). make check green, 513 passed |
| 2026-11-09 | 2 | `ImpliedExpectations` (TC-IE-001..005): years priced on three bases (normal PE 12, own median PE, pre-cycle cap) on net and deducted profit, premium to normal value, reverse-DCF implied growth; DiscoverySettings gains normal_pe, discount_rate, dcf_years, max_years (TC-C-018). 2026-11-06 full market (5,573 companies): 云铝 7.6, 中国铝业 10.8, 中远海控 4.5, 天齐 30.4 years — check values reproduced. Commodity-implied price vs the futures curve still open (needs per-company quarterly profit history and a material price series) |
| 2026-11-09 | 2 | Commodity-implied price: `FuturesCurve.build_dominant_series` (TC-FCV-006), `ImpliedExpectations.compute_sensitivity` (OLS of single-quarter profit from `CompanyCyclePanel.list_quarters` on the quarter's mean dominant futures price, x4; n ≥ 8, R² ≥ 0.3) and `compute_implied_price` (TC-IE-006..007). 2026-11-06 check vs the 12-month futures price: 云铝 R² 0.82, implied AL 20.1k vs 22.6k (−11%); 中国铝业 20.7k (−8%); 紫金 R² 0.90, implied CU 99.4k vs 102.3k (−3%); 天齐 R² 0.33, implied LC 85.8k vs 92.1k (−7%); 赣锋 and 山东黄金 below R² 0.3 → NaN. make check green, 523 passed. Reverse DCF vs consensus path (report_rc) still open |
