# 18 — Company guidance tracking

| | |
|---|---|
| Status | approved 2026-11-11 (user: "两个都批准，先做plan 18第一阶段"); phase 1 done; phase 2 done 2026-11-13; phase 3 done 2026-11-13; phase 4 todo |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-11 |
| Notion | pending |
| Decisions | D-124, D-122, D-102, D-105, D-149, D-150 |
| Depends on plans | 12 (CNINFO documents, SectionDetector, QuoteChecker), 13 (report_rc consensus) |

## Goal
Every quantitative statement a company makes about its own future (earnings previews, annual-report business plans, IR statements, equity-incentive and restructuring targets) and every announced contract or bid win is one point-in-time row with its quote, matched to the actual outcome (revenue for contracts), so each company has a guidance track record, a credibility score and an announced-order backlog.

## Scope
- In:
  - Earnings previews and flash reports (`forecast_vip`, `express_vip`, already in the lake) vs actuals, all versions since 2018.
  - LLM extraction on the Ark API (D-122, `deepseek-v4-1-flash`) of: annual-report 经营计划 / 未来发展展望 (FY2023–FY2025), IR activity records, equity-incentive performance targets, restructuring profit guarantees, major contracts and bid wins (重大合同 / 中标, 3,494 since 2023-11, 710 companies), monthly or quarterly operating-data announcements (新签合同额); every item quote-checked.
  - New CNINFO keywords 股权激励, 经营数据, 新签合同 and doc types `incentive_plan`, `operating_data`; fix the inquiry-reply misclassification (问询函 / 回复 titles filed as semiannual).
  - Matching to actuals (statements, fina_mainbz, annual-report 产销量 and 重大合同及其履行情况) and comparison with broker consensus (`report_rc`); contract backlog = announced, not yet recognised contract value / trailing revenue.
- Out: qualitative tone or sentiment scoring; guidance from news or media interviews; trading signals built on guidance (a later research plan, e.g. under plan 16).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Earnings-preview tracker | `ForecastTracker` → `derived/guidance/forecast_outcomes.parquet`: per (company, period, version) the range, the actual (first statement known after it), in / above / below, distance in range widths, revision path; per company a hit rate and bias since 2018 | 2026 H1 reproduces the probe (1,878 matched, 84.1% in range). PIT test: an outcome is invisible before the actual's `f_ann_date` next session. No LLM | — | done |
| 2 | Acquisition fixes | `cninfo_keyword_announcements` gains 股权激励, 经营数据, 新签合同; `config/documents.yaml` gains `incentive_plan`, `operating_data` and excludes 问询函 / 回复 from periodic rules; existing misfiled manifest rows re-typed; Q&A gap fixed (`irm_qa_sh` stops 2024-07-11, `irm_qa_sz` has no curated files) | Incentive drafts and operating-data announcements since 2023-11 downloaded (counts in the Log); 0 inquiry replies left under `semiannual`; both Q&A datasets current to the last session | — | done |
| 3 | Guidance extraction (pilot) | `SectionDetector` extended to locate 经营计划 / 未来发展展望; `GuidanceExtractor` (prompt per doc type, pydantic `GuidanceItem`: metric, period, value or range, unit, kind target / expectation / commitment, condition, quote, page); `ContractExtractor` (pydantic `ContractItem`: counterparty, amount, currency, share of prior-year revenue, term, status 预中标 / 中标 / 签约 / 终止, segment, quote, page) | 50 companies × (annual plan, IR record, incentive draft) and 100 contract / bid / operating-data announcements: Opus hand check ≥ 85% precision on metric + period + value (amount + counterparty + status for contracts); yield per source in the Log; every kept quote found on its page | 2 | done |
| 4 | Full extraction | Same classes over all FY2023–FY2025 annual reports, IR records, incentive drafts, restructuring reports, contract / bid / operating-data announcements since 2023-11 → `derived/guidance/{items, contracts}.parquet` (`known_on` = ann_date, next session); one contract across 预中标 → 中标 → 签约 is linked, not counted twice | Run complete with failures < 1%; items per source and per metric in the Log; Ark calls and tokens recorded in `meta/llm_usage.jsonl` | 3 | todo |
| 5 | Outcome tracking | `GuidanceTracker`: map each item's metric to an actual (revenue, net profit, deducted profit, volume / capacity from fina_mainbz or 产销量), outcome hit / miss / beat with the gap; per company credibility (hit rate, mean bias, n) next to the `report_rc` consensus gap. `ContractTracker`: per contract the revenue recognised and progress from the annual-report 重大合同及其履行情况 section; per company the announced backlog / trailing revenue and its conversion over the following quarters | 10 named companies hand-checked by the user; items with no measurable actual flagged `unmatched`, share reported; `make check` passes | 1, 4 | todo |
| 6 | Wire in | `GuidanceStep` (pipeline) in `make curate`; company page shows guidance vs actual and credibility; plan 16 reads guidance vs priced-in expectations | Page shows 5 companies (宁德时代, 牧原, 立讯, 茅台, 中国平安) without errors; registry and INDEX current | 5 | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `ForecastTracker` | new | `quant_cn.calculation` (L4) | 1 |
| `SectionDetector` | extend (经营计划 / 未来发展展望 section) | `quant_cn.industry_graph` | 3 |
| `GuidanceExtractor` (+ `GuidanceItem`, `GuidanceReply`) | new (uses `BaseLlmClient`, `QuoteChecker`) | `quant_cn.industry_graph` | 3 |
| `ContractExtractor` (+ `ContractItem`, `ContractReply`) | new (uses `BaseLlmClient`, `QuoteChecker`) | `quant_cn.industry_graph` | 3 |
| `GuidanceTracker` | new | `quant_cn.industry_graph` | 5 |
| `ContractTracker` | new | `quant_cn.industry_graph` | 5 |
| `GuidanceStep` | new (`BaseStep`) | `quant_cn.pipeline` (L6) | 6 |
| `DeepSeekClient`, `PdfTextExtractor`, `QuoteChecker`, `PitAligner`, `DocumentDownloader` | reuse | data_loading / industry_graph / lake | 1–4 |

## Risks
- Metric matching: "营收增长 20%" vs a target in 亿元 vs a segment volume; items whose metric cannot be mapped are kept but `unmatched`, never forced.
- Look-ahead: actuals are restated; the outcome uses the first statement known after the guidance, not the latest restated value.
- Previews are mandatory only for large changes, so the sample is biased toward volatile companies; the credibility score reports n and source mix.
- Ark Coding Plan rate limits and terms for a run of ~50k documents; the pilot measures throughput before the full run.
- Conditional targets (incentive targets are thresholds, not forecasts) are tagged `kind: commitment` and scored apart from forecasts.
- Contracts: only those above the disclosure threshold or voluntarily announced are seen (about 700 companies, order-driven sectors); counterparties are often anonymised (某央企); framework agreements carry no firm amount and are tagged, not added to the backlog.

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
| 2026-11-11 | 2–5 | scope extended to contracts (user: "有没有可能track他们的合同？" → "可以用deepseek抽取"): keywords 经营数据 / 新签合同, `ContractExtractor`, `ContractTracker`, backlog / revenue; extraction on DeepSeek (`deepseek-v4-1-flash` via Ark, D-122). Probe: 40 sampled contract announcements, rule-based amount 19, counterparty 26, term 18, share of revenue 7; 40/40 annual reports carry 重大合同及其履行情况 |
| 2026-11-12 | 2 | started (user "可以" after the 晶科 guidance review). D-149: inquiry replies first in the cninfo rules, 港股公告 / H股 dropped, `incentive_plan` / `operating_data` types, keywords 股权激励 / 经营数据 / 新签合同; `DocumentRetyper` (TC-DRT-001; `DocumentManifestWriter` TC-DMW-001) moved 52 + 1,298 files, excluded 61 H-share / HK filings; 0 inquiry replies left under periodic types. Q&A: `irm_qa_sh` (stopped 2024-07-11) and `irm_qa_sz` (never run) downloading; keyword sweep + PDF download queued after |
| 2026-11-13 | 2 | Q&A gap closed: `irm_qa_sh` 2023-11 → 2026-11-12, 316,416 rows (564 days fetched, 290 empty); `irm_qa_sz` first run, 1,108 days, 752,761 rows; every month present in both. Keyword sweep (股权激励 / 经营数据 / 新签合同) + PDF download started |
| 2026-11-13 | 2 | done: keyword PDFs since 2023-11 in `documents/cninfo/`: `operating_data` 5,005 (经营数据 / 新签合同), `incentive_plan` 2,143 drafts (first pass with 股权激励 only 275, because draft titles read "…限制性股票激励计划（草案）"; keyword 激励计划 added, resweep 99,829 keyword rows, +1,868 drafts, 0 failed, 1.76 GB total for both types). 0 inquiry replies under periodic types; both Q&A datasets current. Next: ph3 pilot |
| 2026-11-13 | 3 | done (user "开始第三阶段吧"; D-150): `SectionDetector` key `outlook` (TC-SD-006; found in 109/113 sampled FY2025 reports, 4 BSE misses then fixed by the 未来展望 rule), `GuidanceExtractor` (TC-GE-001..003), `ContractExtractor` (TC-CEX-001..002), `LenientItem` (TC-LI-001); prompts `guidance_{annual_plan,ir_record,incentive_plan}.txt`, `contract_extraction.txt`. Pilot (`meta/runs/guidance_pilot.py`, seed 18): 50 companies with all three sources, 60 重大合同 / 中标 and 40 order-titled 经营数据 announcements. Yield, round 2: annual plan 10 items from 7/50 docs; IR record 10 from 6/50; incentive draft 326 from 47/50; contracts 96 from 53/60; operating data 274 from 35/40. Opus hand check, round 1: guidance 124/132 (IR 12/19), contracts 131/168 (重大合同 54/88); prompts fixed. Round 2: guidance 70/70; contracts 133/146 = 91% (重大合同 83/96 = 86%, 经营数据 50/50). Every kept quote is found on its page (QuoteChecker). The remaining contract errors (BOT / concession deals, buy-side deals, consortium totals without the tag, annual rates) were fixed in the prompt after round 2; not yet re-checked, so phase 4 opens with a spot check. Verdicts in `meta/runs/guidance/review*_verdicts.jsonl`. Ark: about 1,250k tokens in / 200k out over 3 runs, ¥0 (Coding Plan) |
