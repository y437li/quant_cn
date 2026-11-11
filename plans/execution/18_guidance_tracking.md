# 18 — Company guidance tracking

| | |
|---|---|
| Status | approved 2026-11-11 (user: "两个都批准，先做plan 18第一阶段"); phase 1 done |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-11 |
| Notion | pending |
| Decisions | D-124 (proposed), D-122, D-102, D-105 |
| Depends on plans | 12 (CNINFO documents, SectionDetector, QuoteChecker), 13 (report_rc consensus) |

## Goal
Every quantitative statement a company makes about its own future (earnings previews, annual-report business plans, IR statements, equity-incentive and restructuring targets) is one point-in-time row with its quote, matched to the actual outcome, so each company has a guidance track record and a credibility score.

## Scope
- In:
  - Earnings previews and flash reports (`forecast_vip`, `express_vip`, already in the lake) vs actuals, all versions since 2018.
  - LLM extraction on the Ark API (D-122, `deepseek-v4-1-flash`) of: annual-report 经营计划 / 未来发展展望 (FY2023–FY2025), IR activity records, equity-incentive performance targets, restructuring profit guarantees; every item quote-checked.
  - New CNINFO keyword 股权激励 and doc type `incentive_plan`; fix the inquiry-reply misclassification (问询函 / 回复 titles filed as semiannual).
  - Matching to actuals (statements, fina_mainbz, annual-report 产销量) and comparison with broker consensus (`report_rc`).
- Out: qualitative tone or sentiment scoring; guidance from news or media interviews; trading signals built on guidance (a later research plan, e.g. under plan 16).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Earnings-preview tracker | `ForecastTracker` → `derived/guidance/forecast_outcomes.parquet`: per (company, period, version) the range, the actual (first statement known after it), in / above / below, distance in range widths, revision path; per company a hit rate and bias since 2018 | 2026 H1 reproduces the probe (1,878 matched, 84.1% in range). PIT test: an outcome is invisible before the actual's `f_ann_date` next session. No LLM | — | done |
| 2 | Acquisition fixes | `cninfo_keyword_announcements` gains 股权激励; `config/documents.yaml` gains `incentive_plan` and excludes 问询函 / 回复 from periodic rules; existing misfiled manifest rows re-typed; Q&A gap fixed (`irm_qa_sh` stops 2024-07-11, `irm_qa_sz` has no curated files) | Incentive drafts since 2023-11 downloaded (count in the Log); 0 inquiry replies left under `semiannual`; both Q&A datasets current to the last session | — | todo |
| 3 | Guidance extraction (pilot) | `SectionDetector` extended to locate 经营计划 / 未来发展展望; `GuidanceExtractor` (prompt per doc type, pydantic `GuidanceItem`: metric, period, value or range, unit, kind target / expectation / commitment, condition, quote, page) | 50 companies × (annual plan, IR record, incentive draft): Opus hand check ≥ 85% precision on metric + period + value; every kept item's quote found on its page | 2 | todo |
| 4 | Full extraction | Same class over all FY2023–FY2025 annual reports, IR records, incentive drafts, restructuring reports since 2023-11 → `derived/guidance/items.parquet` (`known_on` = ann_date, next session) | Run complete with failures < 1%; items per source and per metric in the Log; Ark calls and tokens recorded in `meta/llm_usage.jsonl` | 3 | todo |
| 5 | Outcome tracking | `GuidanceTracker`: map each item's metric to an actual (revenue, net profit, deducted profit, volume / capacity from fina_mainbz or 产销量), outcome hit / miss / beat with the gap; per company credibility (hit rate, mean bias, n) next to the `report_rc` consensus gap | 10 named companies hand-checked by the user; items with no measurable actual flagged `unmatched`, share reported; `make check` passes | 1, 4 | todo |
| 6 | Wire in | `GuidanceStep` (pipeline) in `make curate`; company page shows guidance vs actual and credibility; plan 16 reads guidance vs priced-in expectations | Page shows 5 companies (宁德时代, 牧原, 立讯, 茅台, 中国平安) without errors; registry and INDEX current | 5 | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `ForecastTracker` | new | `quant_cn.calculation` (L4) | 1 |
| `SectionDetector` | extend (经营计划 / 未来发展展望 section) | `quant_cn.industry_graph` | 3 |
| `GuidanceExtractor` (+ `GuidanceItem`, `GuidanceReply`) | new (uses `BaseLlmClient`, `QuoteChecker`) | `quant_cn.industry_graph` | 3 |
| `GuidanceTracker` | new | `quant_cn.industry_graph` | 5 |
| `GuidanceStep` | new (`BaseStep`) | `quant_cn.pipeline` (L6) | 6 |
| `DeepSeekClient`, `PdfTextExtractor`, `QuoteChecker`, `PitAligner`, `DocumentDownloader` | reuse | data_loading / industry_graph / lake | 1–4 |

## Risks
- Metric matching: "营收增长 20%" vs a target in 亿元 vs a segment volume; items whose metric cannot be mapped are kept but `unmatched`, never forced.
- Look-ahead: actuals are restated; the outcome uses the first statement known after the guidance, not the latest restated value.
- Previews are mandatory only for large changes, so the sample is biased toward volatile companies; the credibility score reports n and source mix.
- Ark Coding Plan rate limits and terms for a run of ~50k documents; the pilot measures throughput before the full run.
- Conditional targets (incentive targets are thresholds, not forecasts) are tagged `kind: commitment` and scored apart from forecasts.

## Open questions
- Credibility score: proposed hit rate and mean bias over the last 3 years with n ≥ 3; other weighting?
- Include the full investor Q&A text (hundreds of thousands of rows) in phase 4, or only IR activity records?
- Annual-plan history: FY2023–FY2025 is proposed; go further back for longer track records?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-11 | — | drafted at the user's request ("我们有企业的guidance吗？我们可以track他们吗" → "可以，label相关的用方舟的api"); probe: 2026 H1 previews 1,878 matched, 84.1% in range, 7.7% above, 8.1% below; `irm_qa_sh` last row 2024-07-11 |
| 2026-11-11 | — | approved (user: "两个都批准，先做plan 18第一阶段") |
| 2026-11-11 | 1 | done: `ForecastTracker` (TC-FT-001..008), `GuidanceSettings` (TC-C-019, base.yaml `guidance`), `StatementVersionReader.read_first_versions` (TC-SVR-005); real run as of 20261111: 48,134 preview versions, 4,626 companies, 2,727 with ≥ 3 scored periods; 2026 H1 last versions 1,878 scored, 84.1% in / 8.1% below / 7.7% above (= probe); all years 79.3% in, median abs surprise 3.6%; revised periods: v1 inside 19.9%. Output in `meta/runs/guidance/forecast_{outcomes,track}.parquet` (run script `meta/runs/guidance_forecasts.py`) until `GuidanceStep` writes `derived/guidance` in ph6. `make check`: 533 passed |
| 2026-11-11 | 1 | extended (user "ok"): `days_after_end` and `ex_ante` per version; track record adds the last pre-period-end version per period (n_ex_ante, ex_ante_hit_rate, ex_ante_mean_surprise, ex_ante_sufficient; TC-FT-009..010). Ex-ante first versions: 5,363, 57.7% in range, median miss 7.5% (vs 80.5% / 3.4% after the period end). In the 3-year window only 389 companies have an ex-ante preview and 12 have ≥ 3, so ex-ante credibility needs a longer window or more sources. `make check`: 535 passed |
