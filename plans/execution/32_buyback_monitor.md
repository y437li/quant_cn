# 32 — Market-wide buyback and 增持 monitor with LLM labels (全市场回购与增持监测)

| | |
|---|---|
| Status | approved 2026-11-17 (user: "分清楚吧，都标记好"); ph1–4 done |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-17 |
| Notion | pending |
| Decisions | D-154, D-122, D-149, D-151, D-169 |
| Depends on plans | 23 (repurchase, BuybackLedger, buyback events), 12 (CNINFO documents), 18 / 28 (Ark extraction, LabelStore) |

## Goal
Every A-share buyback programme and every major-holder 增持 plan since 2024 sits in one app tab and the morning e-mail, kept apart by a `kind` label (回购 / 增持), with its progress and with LLM labels (Ark Coding Plan, D-122) read from its plan announcement: purpose or holder type, funding source (incl. 回购 / 增持专项贷款), amount range, price cap and period. Today only the book's buyback events and new buyback plans ≥ 2% of market cap are shown.

## Scope
- In:
  - All programmes in `curated.repurchase` from 2024-01 (≈ 5,800 预案 rows; 2,634 in 2024, 1,455 in 2025, 1,569 in 2026 so far). They are joined to their CNINFO plan announcement (回购方案 / 预案 / 回购报告书).
  - Labels per programme: purpose (注销减资 / 员工持股·股权激励 / 维护公司价值及股东权益 / 转债转股 / other), funding (自有 / 自筹 / 回购专项贷款 with bank and loan amount), amount low–high, price cap, period. Each label carries a checked quote (BaseQuotedExtractor).
  - 增持 plans by controlling holders, 实控人, 董监高 and state platforms: CNINFO 增持计划 announcements labelled with holder type, funding (自有 / 增持专项贷款), amount range, price cap and period; executed amounts from `stk_holdertrade` (in_de = IN) of the named holders since the plan date.
  - Daily refresh in `make track-daily`; tab `#buyback` under 监测 with a 回购 / 增持 switch; the 回购 e-mail section gains market totals and labels for both kinds, shown apart.
- Out:
  - Small 董监高 trades without a plan announcement (they stay in `stk_holdertrade` only).
  - Pre-2024 history (can be extended later).
  - Research on whether purpose predicts returns (a follow-up under plan 23 ph4's method).
  - Changing the risk model or condition metrics.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Plan announcements | Add searchkeys 回购 and 增持 to `cninfo_keyword_announcements`. Add doc_types `buyback_plan` (`回购.{0,20}(方案\|预案\|报告书)`) and `holder_increase_plan` (`增持.{0,20}计划`), excluding 摘要 / 法律意见 / 核查 / 进展 / 完成 / 结果 / 实施期限届满, to the CNINFO rules. Backfill 2024-01 to now, then download only those two doc_types | ≥ 90% of 2024+ 预案 programmes match a `buyback_plan` PDF on (ts_code, ann_date ± 3 days). Unmatched ones are listed. The `holder_increase_plan` count and a 20-title spot check are logged. `make check` passes | — | done 2026-11-17 — 67,228 回购/增持 titles listed (74 month keys); 6,632/6,634 PDFs downloaded (buyback_plan 5,317, holder_increase_plan 1,315; 2 not_pdf). Match: 2,824/3,103 = 91.0% of 2024+ open-market 预案 have a buyback_plan PDF (2024 92.1%, 2025 85.9%, 2026 92.8%); Tushare 预案 that are 限制性股票/员工持股 回购注销 (2,627 with such a title ±3d and no plan) are not market programmes and left out. 279 unmatched, mostly BJ 920xxx and 400xxx codes absent from the keyword sweep plus titles without 方案 (e.g. 关于回购公司股份并用于注销的公告); list in lake meta/runs/plan32_ph1_unmatched.csv (script plan32_ph1_match.py). Exclude rule gained 完毕/首次回购/存续期 after a 20-title check (1 + 2 noise); recheck of 20 增持 titles: 20/20 plans. make check: lint 0, mypy clean, pytest 1021 passed, go ok, vitest 50 passed |
| 2 | Ark labels | `BuybackTermsExtractor` (BaseQuotedExtractor, prompt in `prompts/`) reads both doc_types and writes LabelStore set `buyback_terms` (known_on = ann_date). Fields: kind 回购 / 增持, purpose or holder type, funding, loan bank and amount, amount range, price cap, period. Pilot on 100 announcements (both kinds) first, then run on all of them | Hand check of 50 random pilot labels: kind, purpose / holder and funding ≥ 95% right, amounts and price cap ≥ 95% within rounding, every quote verified. Token cost logged. Full run: ≥ 95% labelled, failures listed | 1 | done 2026-11-17 — pilot passed: 100 docs (50 + 50, seed 32), 98 labelled (2 dropped: quote paraphrased across a line break; terms were right), 101 items, 233k tokens (prompt v2). Rule audit of all 101 items against the PDF text (amounts, loan amount, price cap, 专项贷款, purpose words): 1 item wrong (price cap 53 and amount low missed). Hand check of 50 random items: kind 50/50, purpose / holder 50/50, funding 48/50 in v1 (其他 where the text gives none) → prompt v2 rule "没有写资金来源时写 []" and "按回购价格上限X元/股测算" → v2: 1 funding miss in 101. Conditional 专项贷款 sentences ("如采用…") are not labelled as loans by design. Full run: 6,632 docs, 6,503 labelled (98.1%; 回购 5,241 / 5,317, 增持 1,262 / 1,315), 6,572 items, 16.4M tokens (14.9M in / 1.3M out, 6,531 calls). 129 unlabelled in meta/runs/plan32/unlabelled.csv: 90 quote-check drops of real plans, 39 not a new plan. Imported as label set buyback_terms (config/label_sources.yaml, 6,632 rows). make check: lint 0, mypy clean, pytest 1031 passed, go ok, vitest 50 passed |
| 3 | Monitor document | `BuybackMonitorBuilder` joins BuybackLedger programmes (回购) and labelled 增持 plans with `stk_holdertrade` execution to `buyback_terms`, keeping the two kinds apart, writes `$(APP_DATA)/buyback_monitor.json` and is added to `make track-daily`. Contents: live programmes (planned, executed, % done, price cap vs close, expiry, labels), the day's new / completed / stopped ones, and totals per kind by purpose / holder type and funding (incl. 专项贷款 totals) | TCs on hand rows: PIT (a label is unseen before its ann_date), no double count of 实施 cumulative amounts, totals equal the sum of rows. The real 20261117 file has counts that match a direct SQL check | 2 | done 2026-11-18 — BuybackPlanFrame (TC-BPF-001..003) + BuybackMonitorBuilder (TC-BMB-001..002) write buyback_monitor.json (≈ 420 KB) from `make buyback-events` (already in track-daily; no new target). 20261117: 回购 775 live (low 1,308 亿 / high 2,399 亿, executed 1,072 亿; 190 with 专项贷款, loans 387 亿), 49 events (38 new, 6 reached the low, 5 expired); 增持 299 live (high 325 亿, executed 160 亿; 35 with loans, 72 亿), 18 events. Direct SQL check: 3,009 kept 回购 programmes since 2024 = the file's month counts; 38 new in the window = SQL. Unlabelled programmes are kept only with a price cap and no 限制性股票 title within ±3 days. Found and fixed a BuybackLedger bug: same-day rows had no fixed order, so a 完成 filed with a new 预案 could go to either programme and runs differed (京东方 42 亿 vs 10 亿); now ordered (progress / 停止, then 预案 larger first, then 股东大会通过), TC-BBL-005, three runs byte-identical. make check: lint 0, mypy clean, pytest 1050 passed, go ok, vitest 53 passed |
| 4 | App tab and e-mail | Go `/api/buyback`. Web `#buyback` (监测 group): a 回购 / 增持 switch and a table with purpose / funding / size filters, the day's new list, totals by month. `BuybackReportSection` adds a market line (new plans today by purpose, 回购贷款 amount) and labels on its rows | go test, vitest (format helpers), smoke opens the tab. An e-mail fixture shows labels and the market line. `make check` passes | 3 | done 2026-11-18 — Go /api/buyback (GetBuybackMonitor, TC-ST-030, TC-API-017); web #buyback 回购增持 under 监测: 回购 / 增持 switch, headline, totals by purpose / holder type and funding, month bars (专项贷款 part), the window's events (first 10, expandable), live table with purpose / 专项贷款 / size filters (vitest TC-BBF-001..002; smoke: 210 rows, 增持 + loan filter ok). E-mail: the market line and labels went into a new section BuybackMarketReportSection (DOC buyback_monitor, TC-BMR-001..002) after the 回购 block instead of extending BuybackReportSection, since a section reads one document; real dry-run shows "新回购 33 个（员工持股 17、股权激励 17、维护价值 12），其中专项贷款 7 个 …" and the 14-row table. make check: lint 0, mypy clean, pytest 1052 passed, go ok, vitest 55 passed |

Status cell: `<state> <YYYY-MM-DD> (<commit>) — <note>`, state one of todo / doing / blocked / done.

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `CninfoClient`, `DocumentDownloader`, `DocumentRetyper` | reuse (config: searchkey, doc_type rule) | `quant_cn.data_loading` | 1 |
| `BuybackTermsExtractor` (name via `naming`) | new, subclass of `BaseQuotedExtractor` | `quant_cn.industry_graph` | 2 |
| `DeepSeekClient`, `LabelStore` | reuse | `quant_cn.data_loading`, `quant_cn.lake` | 2 |
| `BuybackMonitorBuilder`, `BuybackPlanFrame` | new | `quant_cn.portfolio` | 3 |
| `BuybackLedger` | reuse; fixed same-day row order (TC-BBL-005) | `quant_cn.lake` | 3 |
| `BuybackMarketReportSection` | new, subclass of `ReportSection` (market line, labels; BuybackReportSection unchanged) | `quant_cn.visualization` | 4 |
| Go `GetBuybackMonitor`, React `BuybackPage` | new | `apps/chain_api`, `apps/chain_web` | 4 |

## Risks
- Searchkey 回购 is broad (progress notices dominate, ≈ 17k 完成 rows since 2024). The listing is cheap, but the doc_type rule must keep downloads to plan announcements only.
- Plans often say 不低于 X 亿 且不超过 Y 亿 or give a share range; amounts must be normalised to yuan.
- 回购专项贷款 is sometimes disclosed only in a later separate 贷款承诺函 notice; the label may miss it, so phase 2 measures the miss rate.
- `config/datasets.yaml` and `documents.yaml` are shared with concurrent sessions, so new keys are announced to peers before the edit.
- Ark quota: about 5.8k calls for the backfill. The pilot cost decides batch pacing.

## Open questions
- Settled 2026-11-17 by approval ("分清楚吧，都标记好"): 增持 plans are included and kept apart from buybacks by the `kind` label; defaults for the rest (history from 2024-01, no phone alert).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-18 | 4 | Done: #buyback tab, /api/buyback, e-mail block 回购增持（全市场） as a new section |
| 2026-11-18 | 3 | Done: buyback_monitor.json from `make buyback-events`; BuybackLedger same-day order fixed (TC-BBL-005) |
| 2026-11-17 | 2 | Done: full run 98.1% labelled, label set buyback_terms imported |
| 2026-11-17 | 2 | BuybackTermsExtractor + prompt; pilot passed (rule audit 100/101 amounts, hand check 50: funding 48/50 → prompt v2); full run started |
| 2026-11-17 | 1 | Done: 91.0% match on market 预案; restricted-stock 回购注销 rows found in Tushare 预案 and excluded from the denominator (ph3 must filter them too) |
| 2026-11-17 | all | Approved ("分清楚吧，都标记好"): 增持 plans added, kept apart by `kind`; ph1 started |
| 2026-11-17 | all | Drafted at the user's request ("监控所有回购，可以用方舟计划lable"), awaiting approval |
