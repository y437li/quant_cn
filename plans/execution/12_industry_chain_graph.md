# 12 — A-share industry-chain knowledge graph

| | |
|---|---|
| Status | doing (phase 2) — approved 2026-11-07 (user: "修一下，然后可以先下载文件") |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-07 |
| Notion | pending |
| Decisions | D-096, D-097, D-098, D-099 (proposed), D-100, D-101, D-102, D-103, D-104, D-106, D-107 |
| Depends on plans | 01, 11 (done: `stock_basic`, Shenwan `index_classify` / `index_member_all`, loader framework) |

## Goal
The lake holds an evidence-backed graph that maps every A-share company to products, materials,
technologies, segments and end markets. Every company edge cites a document, page, quote and
confidence, so `GraphQuery.explain_exposure("300750.SZ", "AI数据中心")` returns the chain and its evidence.

## Scope
- In: an Opus-authored whole-market product taxonomy and chain skeleton (a prior). CNINFO metadata and PDFs from
  2023-11-01 to today: annual, semiannual and Q1/Q3 reports, prospectuses, and announcements filtered by title
  (major contracts, M&A/restructuring, investment projects, IR activity records). Eastmoney broker industry and
  stock reports with PDFs (D-100). Tushare `irm_qa_sh` / `irm_qa_sz` Q&A. Existing lake tables `report_rc`
  (titles, ratings) and `stk_surv` (visit notes) as secondary evidence. Page-level PDF text. DeepSeek extraction and validation. Entity resolution. DuckDB schema `graph`.
  Query class and a notebook.
- Out: the US-side chain (US companies' own suppliers and customers from SEC 10-K filings): a later plan; here foreign companies are end-point nodes only (D-097 amendment), and US dependence is measured from the A-share side (overseas and North America revenue share, named US counterparties).
- Out: Tushare `research_report` / `anns_d` (permission denied on this token, probed 2026-11-07),
  company websites, OCR (text-layer PDFs only; failures listed), Neo4j export, UI, factors built on the graph.

## Volume (CNINFO counts, 2025-11 → 2026-11, × 3 years)
Annual ≈ 11.4k/yr, semiannual ≈ 11.3k/yr, Q1 ≈ 5.6k/yr and Q3 ≈ 5.7k/yr. These counts include summaries, English
versions and corrections. Keeping full Chinese reports only leaves ≈ 60k PDFs. Estimated disk use is about 60 GB
(1.6 TB free).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Opus taxonomy seed (whole market) | `config/industry_chain/<sw_l1>.yaml` for all 31 Shenwan L1 sectors. Each holds segment → product → sub-product trees, materials, technologies and end markets with Chinese/English names and aliases. It also holds product-to-product chain edges (`upstream_of`, `component_of`, `used_in`, `uses_material`) tagged `source: prior` and the mapping from every SW L3 code to its segments. `_global_companies.yaml` adds key foreign players with prior role edges (D-097 amendment). `ProductTaxonomy` loads and validates the files | Validator passes: ids unique, aliases unambiguous, `upstream_of` acyclic, every SW L3 code in `index_classify` mapped. Node and edge counts are reported per sector. The user spot-checks 3 sectors | — | todo |
| 2 | Document acquisition | `CninfoClient`, `EastmoneyReportClient` (via `BaseWebClient` + `RequestPacer`). Datasets `cninfo_announcements` (one key per calendar day, every category), `em_industry_reports` / `em_stock_reports` (one key per month), `irm_qa_sh` / `irm_qa_sz`. `DocumentDownloader` + `DocumentClassifier` (config/documents.yaml) write PDFs to `documents/<source>/<doc_type>/<YYYY>/<MM>/` with a sha256 manifest (`meta.documents`, D-101). CLI `download-docs` | Metadata row counts equal CNINFO `totalAnnouncement` per category-month. Every selected PDF is downloaded or listed as failed. Re-running does no work. `make check` passes | — | doing |
| 3 | Parsing + sections | `PdfTextExtractor` (PyMuPDF, one row per page) writes `derived/doc_pages`. `SectionDetector` keeps only the chain sections of D-102 (主营业务/产品, 行业情况, 主营业务构成, 前五名客户, 前五名供应商, 原材料, 产能, 核心技术, 主要竞争对手/同行业可比公司, 可能面对的风险) as `derived/doc_sections` with page ranges and the top-5 customer/supplier tables parsed | ≥ 98% of PDFs have a text layer, with the rest listed. The customer and supplier sections are found in ≥ 95% of a 100-annual-report sample, and their tables parse to rows with shares summing as reported. Page numbers match the PDF viewer | 2 | todo |
| 4 | DeepSeek extraction | `BaseLlmClient`, `DeepSeekClient` (key from env, retries, response cache keyed by prompt hash; default `deepseek-flash`, D-098) and `RelationExtractor`. Input is the D-102 sections only. Output is JSON validated by Pydantic: weighted edges `produces` / `sells_to` / `buys_from` / `buys_material` with period, share_pct, amount, basis, evidence quote, page and confidence. `fina_mainbz_p/i` items are mapped to taxonomy products. Unknown objects become `node_proposals` | A 50-company pilot (5 sectors, flash vs pro) is reviewed by Opus with ≥ 85% precision before the full run. Shares are checked against the source table. Cost and tokens are logged per document | 1, 3 | todo |
| 5 | Validation + resolution | `EvidenceChecker` (deterministic: the quote must appear on the cited page), `RelationValidator` (second DeepSeek pass returning SUPPORTED, PARTIAL or NOT; ≥ 0.90 approve, 0.70–0.90 review, < 0.70 reject), `EntityResolver` (companies via `stock_basic`, full names and aliases; products to taxonomy ids; anonymous "客户一" placeholders named only from another document; matching sells_to / buys_from pairs merged, D-102). Opus merges `node_proposals` into the taxonomy | 0 accepted edges have a failed quote check. Precision is ≥ 90% on a 300-edge stratified sample reviewed by Opus with the user, and the review queue size is reported | 4 | todo |
| 6 | Graph + query | DuckDB schema `graph` (`entities`, `relations`, `evidence`, `documents`) and the CompanyCard tables plus `company_card/<ts_code>.json` per company (D-104). `GraphQuery` provides `companies_for`, `upstream`, `downstream`, `customers`, `suppliers` (with shares), `explain_exposure` and `peers` (product-vector similarity + competitor_of evidence + shared counterparties, D-102) over one network of company–company, company–product and product–product edges. Notebook `research_space/industry_chain.ipynb` answers the plan's §25 questions | `explain_exposure` returns a path with evidence for 10 named companies × AI data center. `peers` for 10 named companies returns stage-level peers whose reasons cite evidence. `make lake-rebuild` reproduces the `graph` tables byte-identically from the cached LLM responses | 5 | todo |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `ProductTaxonomy`, `TaxonomyValidator` | new | `industry_graph` (L4, D-099) | 1 |
| `CninfoClient` | new (subclass `BaseApiClient`) | `data_loading` | 2 |
| `DocumentDownloader` | new | `data_loading` | 2 |
| `DateSweepFetcher`, `TushareClient`, `ParquetWriter`, `FetchLog` | reuse | `data_loading`, `lake` | 2 |
| `PdfTextExtractor`, `SectionDetector` | new | `industry_graph` | 3 |
| `BaseLlmClient` | new | `core` | 4 |
| `DeepSeekClient` | new | `data_loading` | 4 |
| `RelationExtractor`, `ExtractionStep` | new | `industry_graph`, `pipeline` | 4 |
| `EvidenceChecker`, `RelationValidator`, `EntityResolver` | new | `industry_graph` | 5 |
| `GraphStore`, `GraphQuery` | new | `industry_graph` | 6 |

## Risks
- DeepSeek cost and throughput: about 60k documents × 20–40k tokens of section text. Mitigation: sections only,
  the latest annual report first, cache every response, report cost after the pilot before the full run.
- An Opus prior would leak into the graph as fact. Mitigation: prior edges sit only between products; company
  edges need document evidence (D-097); queries mark prior edges as such.
- CNINFO rate-limits or changes its API. Mitigation: ≤ 2 req/s, retries, resumable fetch log, raw JSON kept.
- Product aliasing (碳化硅 vs SiC substrate vs SiC device). Mitigation: the taxonomy holds aliases per granular node,
  and the extractor must pick the most specific node or propose a new one.
- The DeepSeek key in `chinese_market/src/common/config.py` is committed in plain text. Mitigation: rotate it and
  read `DEEPSEEK_API_KEY` from `.env` only.

## Open questions
- Notion parent page for plan mirrors (still `pending` for all plans).
- DeepSeek budget ceiling for the full run; models available: `deepseek-v4-pro`, `deepseek-flash` (key in `.env`, verified 2026-11-07).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-07 | — | drafted: Tushare `research_report` and `anns_d` denied, `irm_qa_sz` OK, CNINFO query and PDF download verified |
| 2026-11-07 | 2 | approved; Eastmoney reports added (D-100); storage layout D-101; clients, downloader, CLI, tests built (lint 0, tests pass, 95% cov); metadata sweep running; `irm_qa_*` deferred to after the document lists (Tushare paces it at ~10 s/day) |
| 2026-11-07 | 2 | user: download all Eastmoney stock reports; downloader releases the catalog after listing so PDF downloads run beside the CNINFO metadata sweep |
| 2026-11-07 | 3–6 | user: read only the chain sections; customers, suppliers and shares; one network (D-102). Added `fina_mainbz_p` / `fina_mainbz_i` (Tushare product and industry revenue breakdown, permission OK) |
| 2026-11-07 | 3, 6 | user: identify peers — four-signal peer score, competitor sections added (D-102) |
| 2026-11-07 | 3 | user: A-share reports share one format — sections found by heading rules, revenue and top-5 tables parsed without the LLM (D-102) |
| 2026-11-07 | 3 | prototype on 6 FY2025 annual reports (沃尔核材, 中际旭创, 宁德时代, 恒瑞医药, 沪硅产业, 天岳先进; `meta/runs/proto/section_proto.py`): all have a text layer; 4/6 have PDF outlines; the 管理层讨论与分析 chapter was found in 6/6 and is 12–19% of the text (恒瑞 39%); top-5 tables parsed in 5/6, with row shares summing exactly to the stated totals; 恒瑞 (SSE main board) discloses totals only, parsed from the sentence. Three layouts: SZSE (元/千元, %), STAR (万元, no %, related-party column), SSE main (sentence totals). Counterparty names: 1/6 names suppliers (沃尔核材: 金氏铜业, 江西铜业…); the rest are anonymous |
| 2026-11-07 | 4–5 | user: foreign customers — prototype shows named overseas customers in prose (沪硅: TSMC/UMC/ST; 宁德: VW/BMW/Stellantis; 天岳: Bosch); entity master gains non-A-share companies; named links without share; mentions excluded; inferred matches separate (D-102) |
| 2026-11-07 | 1 | user: foreign companies belong in the chain — `_global_companies.yaml` (prior roles) plus region nodes with revenue share; A-share↔foreign edges still need evidence (D-097 amendment) |
| 2026-11-07 | — | user: focus on A-shares; US-side chain (10-K) deferred to a later plan; foreign companies stay end-point nodes |
| 2026-11-07 | 1, 3 | user: dependence can be reverse — supply-side edges from foreign suppliers, risk section added, prior `import_dependence` on products (D-102) |
| 2026-11-07 | 3 | rule pass built as classes in new package `industry_graph` (L4, D-099 accepted): `PdfTextExtractor` (running headers removed; page numbers by sequence), `SectionDetector` (own-line chapter heading, TOC pages skipped), `CounterpartyTableParser` (SZSE / STAR / SSE-main layouts), `AnnualReportParser`; 13 tests. On 10 FY2025 reports: MD&A found 10/10 (13–19% of text, 恒瑞 39%); top-5 customers and suppliers consistent in 9/9 tabled reports, 恒瑞 totals only. `pymupdf` added. Still to do: `doc_pages` / `doc_sections` writers and the 100-report sample |
| 2026-11-07 | 2 | free labels (D-103): `stock_company`, `ths_index`, `ths_member`, `dc_index`, `dc_member` added and downloading before the CNINFO sweep resumes |
| 2026-11-07 | 6 | view design prototype (`research_space/prototypes/chain_view`, private artifact): chain network (company → products by revenue share → prior upstream/downstream; customers/suppliers with shares; named foreign customers; peers by product-vector cosine) + dossier tabs (概览/产品与服务/客户/供应商/同行/上下游/证据). Learned: `fina_mainbz` items are coarse (10/42 matched by substring) → phase 4 maps bz_items with rules + DeepSeek flash batches (D-103) |
| 2026-11-07 | 6 | user: per-company schema → CompanyCard (D-104); research-report valuation → plan 13 (D-105, to draft) |
| 2026-11-07 | 1, 6 | user: sector-specific KPIs by Shenwan industry → `config/sector_kpis.yaml` (Opus prior) + CompanyCard.sector_kpis (D-106) |
| 2026-11-07 | 4 | user: sector KPIs must be read from research reports — Opus list is a seed; report pass (term counts + DeepSeek flash on ~15 industry deep-dives per sector) decides the final set (D-106 amendment) |
| 2026-11-07 | 4 | user: broker reports and company filings decide the KPI set together — tiers core / broker / disclosed with citation counts and disclosure share (D-106) |
| 2026-11-07 | 1 | merge done (D-107): 445 → 0 clashes, 201 merged ids, 245 bridges, copper sub-chain; checker OK. Remaining in ph1: `_global_companies.yaml`, `ProductTaxonomy` class + tests, user spot-check of 3 sectors |
| 2026-11-07 | 6 | view: company graph as six swim lanes (suppliers / upstream / own products / downstream / end markets / customers); peers only in their tab; internal supply edges |
| 2026-11-07 | 4 | **4a pilot started** (user: "用DeepSeek读一下主要应用领域试试，做好计划，然后follow"). Scope: the 10 prototype companies only. Steps: (1) `LlmConfig` + `BaseLlmClient` (core) + `DeepSeekClient` (data_loading; key from env, RequestPacer, response cache in `meta/llm_cache/`, token usage logged); (2) `ApplicationExtractor` (industry_graph): business + industry sections → per revenue line the downstream applications (mapped to candidate taxonomy nodes or proposed), customer types, named counterparties vs mere mentions, each with a verbatim quote and page; quotes checked against the page text; (3) tests with fake LLM and transport; (4) run on the 10 reports with `deepseek-flash`, feed results into the view's anonymous-customer profiles (source tag "DeepSeek 读年报"), publish; (5) report precision by hand on the 10 companies, tokens and cost. Done when: `make lint` and tests pass, 10 companies processed, every kept quote found on its page, view updated |
| 2026-11-07 | 4 | **4a pilot done**: `LlmConfig`, `BaseLlmClient`/`LlmReply`, `DeepSeekClient` (cache, cost, ledger), `ApplicationExtractor` (prompt file, quote check, roles customer/supplier/partner/competitor/subsidiary/mention) + tests. 10 reports: 103/105 then 92/100 applications kept after quote check; customers vs mentions separated correctly in hand review (e.g. 中际旭创: Google/Microsoft = mention; 宁德时代: VW/BMW = customer; 沪硅: TSMC/SMIC = customer); competitors give peer evidence (牧原 → 正大, 温氏, 新希望). Cost ¥0.157 (D-108). Fixed taxonomy: hog by-products now come from slaughter, not live hogs; 226 possible stage-skipping edges listed for review (`meta/runs/shortcut_edges.tsv`). Also: datasets starting after the run end are skipped; key-source datasets not yet curated give no keys |
| 2026-11-07 | 2, 6 | user: use the 2026 periodic reports too — sweep order Mar–Apr 2026 (FY2025 annual + Q1) → Aug 2026 (H1) → Oct 2026 (Q3) → rest; CompanyCard fields take their latest source and keep the period (D-104) |
| 2026-11-07 | 6 | user: define the business-model part — design v0.1 in plans/architecture/BUSINESS_MODEL_DESIGN.md (12 archetypes, driver trees, CompanyCard.business_model), D-112 proposed |
| 2026-11-07 | 6 | business-model step 1 done: `config/business_models.yaml` (12 archetypes, 68 variants, 346 L3 defaults, 1,349 driver links); user spot-check pending |
| 2026-11-07 | 3 | full-market FY2025 annual parse (5,598 reports, rules only, ¥0): v1 business 91.0% / counterparty 90.2%; fixed BSE layout (业务概要, (3) 主要客户情况, 合计-row totals, 第五节 重大事件), A+H 第二章 董事会报告, 百万元/前五大供货商/前5名/wrapped-word sentences, joint-heading split, whole-report fallback → business 96.4%, counterparty 95.7% (≥95% met), customers consistent 65.3%, totals-only 28.0%, none 5.1% (105 of 285 are banks/brokers with no top-5 disclosure); 5,251 named customer and 6,245 named supplier rows. Staging: lake meta/runs/parse/annual_fy2025.parquet |
| 2026-11-07 | plan 13 ph3 | valuation full run done: 11,147 stock reports, 0 failed, DeepSeek flash ¥73.47 (53.7M in / 5.8M out) |
| 2026-11-07 | 4 | full run: ApplicationExtractor over 11,059 reports (FY2025 annual + 2026H1), 15 failed, 599 no business section, DeepSeek flash ¥101.04 (57.2M in / 11.8M out); output lake meta/runs/applications/applications.jsonl |
| 2026-11-07 | 4 | new `QuarterlyNoteExtractor` (TC-QNE-001..004): 2026Q3 + 2026Q1 notes; 3,397 of 11,157 read (≥300 chars of 其他提醒事项/其他重要事项), 13,089 items (1,177 orders, 269 customers, 1,442 capacity, 4,553 drivers), ¥8.54; skipped reports keep operating change reasons by rule. Output meta/runs/quarterly/quarterly_notes.jsonl |
| 2026-11-07 | 6 | chain view market-wide (build_market_view.py, lazy per-L1 shards, sector company network, 季报要点 tab), artifact v11 |
| 2026-11-08 | 1, 4 | `ProductTaxonomy` + `ProductMatcher` (TC-PT-001..003, TC-PM-001..005, D-115): mapped non-generic revenue lines 27% → 78.5%, companies ≥50% mapped 1,805 → 4,477; taxonomy YAML comma bugs fixed (1,4-丁二醇, 2,4-D, 5 name_en) |
| 2026-11-08 | 6 | view v13: search fixed (non-string node name), valuation and KPI tab by product / L3 / sector KPIs, zoom / fullscreen / collapse, draggable dossier width |
| 2026-11-08 | 6 | D-118: pricing power P1–P6 + T1 (rules on income single quarters, fut_daily via new `config/material_prices.yaml`, leaders, cycle clocks, quarterly notes, annual 经营模式 reading); graded label maker / lean_maker / middle / lean_taker / taker / insufficient with confidence; archetype signatures in `business_models.yaml` and a posterior check (consistent / partial / inconsistent / insufficient). New `BusinessModeExtractor` (TC-BME-001..003), full FY2025 run in progress (~¥30). Fixes after review: share signal maker-only, own output removed from the cost basket, selling-price text only, L1 peers when L3 < 5 |
| 2026-11-08 | 6 | graded pricing power (maker / lean_maker / middle / lean_taker / taker / insufficient + confidence); share signal maker-only. New `PricingAdjudicator` (TC-PAD-001..003): DeepSeek verdict for insufficient or archetype-inconsistent companies, reasons must cite supplied evidence keys; queued after the business-mode run (est. ¥4–6, user "ok") |
