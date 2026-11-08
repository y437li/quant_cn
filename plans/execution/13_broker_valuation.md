# 13 — Broker valuation logic from research reports

| | |
|---|---|
| Status | phase 3 waiting for the stock-report PDFs — approved 2026-11-07 (user: "计划13批准，可以开始") |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-07 |
| Notion | pending |
| Decisions | D-100, D-102, D-104, D-105 |
| Depends on plans | 12 (taxonomy, CompanyCard, DeepSeek client, quote check) |

## Goal
For every A-share company with broker coverage, the CompanyCard holds how brokers value it: the method, the multiple and its base year, the target price, DCF inputs, the comparable set, and the segment volume / price / margin assumptions linked to taxonomy products. For every Shenwan industry there is an induced summary of the valuation logic and how much brokers disagree.

## Scope
- In:
  - Eastmoney stock reports (D-100) and `report_rc`.
  - Sections: valuation, earnings forecast and investment advice, the comparable-company table, key assumptions; the first two pages plus pages whose headings or tables match the valuation keywords.
  - DeepSeek flash extraction with quote check.
  - Rules for the `report_rc` numeric fields: EPS, PE, target price, rating.
  - Cross-broker dispersion; per-industry induction.
- Out: building our own valuation model; price-target backtests (a later research plan).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Pilot | 3 recent reports × 10 companies, extracted with quote check; per-company and per-industry summary | Valuation method, multiple and target price agree with the report text in ≥ 90% of a hand check | 12 ph4a | done (hand check pending user) |
| 2 | ValuationExtractor | class in `industry_graph` (prompt file, pydantic shape with `multiple_kind` (D-109), shared `QuoteChecker`, comparables resolved to ts_codes) + tests | `make check` passes; pilot re-run through the class (prompt changed, ~¥0.2) and spot-checked | 1 | done |
| 3 | Full run | all stock reports of the last 12 months, newest first, cost logged in `meta/llm_usage.jsonl` | ≥ 95% of covered companies have a valuation record; cost reported before and after | 2 | todo |
| 4 | Industry valuation cards | Per SW L1/L3 and archetype: method mix (LLM extraction), multiples by base year from `report_rc` (`max_price`/`min_price` = target price; `tp` is total profit, DATA_CATALOG), implied vs target split (D-109), PEG, upside, broker dispersion, trend; the KPIs the assumptions bet on (assumption metrics → `sector_kpis.yaml` ids) | Card for every L1; the user reviews 3 industries | 3 | todo |
| 5 | Implied parameters (reverse engineering) | Mature archetypes: single-stage PB-ROE / Gordon → implied required return r (g fixed). Growth archetypes: r from CAPM (ChinaBond 10y in the lake + beta from lake prices × ERP), two-stage model → implied high-growth years and terminal growth. The same computed at the market price → "market-implied" vs "broker-implied" gap per company and industry. CompanyCard.valuation + the view's 估值 tab | Reproduces known cases (banks: implied r 10–13%); prototype table recomputed with both models | 4 | todo |
| 6 | Consensus + forward multiples (D-114) | `ConsensusStep` → `derived/consensus/year=YYYY` (per stock per session, FACTOR_LIBRARY §3b rules) and view `derived.forward_valuation` (forward EP/PE, PEG, upside, forward PB, coverage, dispersion); PDF forecasts fill report_rc gaps | PIT test (a report is invisible on its date, visible next session); lake-rebuild byte-identical; prototype values reproduced | 2 | todo |

## Risks
- Broker PDFs put tables in images: keep text-layer only; list misses.
- Base-year confusion (2026E vs 2027E multiples): the extraction must return the year explicitly; the check rejects records without it.
- Cost: about 50k stock reports a year; pages are filtered to the valuation sections first, and the cost is reported per run.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-07 | 1 | drafted; pilot started at the user's request ("还有research paper的估值逻辑的归纳") |
| 2026-11-07 | 1 | pilot run: 28 reports, ¥0.200; methods / multiples / assumptions with page quotes; finding D-109 (A-share brokers mostly give implied multiples, not targets); results in the view's 估值 tab and `research_space/prototypes/chain_view/valuations.json` |
| 2026-11-07 | 2 | approved; phase 2 started |
| 2026-11-07 | 2 | done: `QuoteChecker` (shared with ApplicationExtractor), `ValuationExtractor` (+ `ValuationItem`/`ValuationReply`/`ValuationResult`), prompt file, 5 tests; pilot re-run ¥0.197: `multiple_kind` right in 28/28 (domestic = implied, 招银/交银/东吴国际 = target), comparables resolved 6/6, 东吴 on 天岳 corrected to EV/Sales 26x 2027E (pilot said EV/EBITDA); EV_SALES added to the prompt. Broker text names anonymous customers (英飞凌, 芯联集成 for 天岳) → D-102 |
| 2026-11-07 | 4–5 | user: industry valuation conventions, multiples and reverse-engineered parameters. Prototype over report_rc (12 months): target PE 26E from ~60 (计算机, 电子) to ~8 (银行); PEG 0.9 (电力设备) to 2.1 (计算机); upside 17–35% (broker optimism); single-stage implied r 4–12% — implausible for growth sectors, hence a two-stage model with CAPM r there (D-113). Mistake caught: `tp` is total profit, not target price (DATA_CATALOG) |
| 2026-11-07 | 6 | user: forward PE belongs to the architecture — phase 6 added (D-114); prototype as of 2026-09-30 matches FACTOR_LIBRARY §3b definitions |
| 2026-11-08 | 4 | `BrokerViewSynthesizer` (TC-BVS-001..003): 2,902 synthesized views (927 product/segment, 292 L3, 1,683 company), 0 failed, ¥19.58; loss-year rerun of 140 groups with forecasts in digests (D-109 amendment), ¥0.89 |
