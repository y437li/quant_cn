# src/quant_cn/industry_graph/

L4: the A-share industry-chain graph (plan 12, D-099): report parsing now; taxonomy, extraction and query to come. May import from: L1. Independent of statistic and calculation.

## Folders
| Folder | Purpose |
|---|---|
| [`prompts/`](prompts/INDEX.md) | LLM prompts as text files, loaded by the extractors |

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `annual_report_parser.py` | one annual report PDF → chain sections and top-5 counterparty tables (plan 12 phase 3) | `ParsedReport`, `AnnualReportParser` |
| `application_extractor.py` | DeepSeek reads a report's business sections: applications and named counterparties (D-102) | `ApplicationItem`, `LineItem`, `CounterpartyItem`, `ApplicationReply`, `ApplicationResult`, `ApplicationExtractor` |
| `counterparty_table_parser.py` | top-5 customer and supplier tables of an annual report, parsed without the LLM (D-102) | `CounterpartyRow`, `CounterpartyTable`, `CounterpartyTableParser` |
| `pdf_text_extractor.py` | page text of a report PDF without running headers, footers and page numbers | `ReportPages`, `PdfTextExtractor` |
| `quote_checker.py` | the pages an LLM is given and the check that its quotes come from them | `Evidence`, `QuoteChecker` |
| `section_detector.py` | the chain sections of an annual report, located by heading text (D-102) | `Section`, `SectionDetector` |
| `valuation_extractor.py` | DeepSeek reads broker valuation pages: method, multiples (implied vs target), target price, assumptions (plan 13) | `ValuationItem`, `ValuationReply`, `ValuationResult`, `ValuationExtractor` |
| `guidance_extractor.py` | DeepSeek reads company guidance (annual plan outlook, IR record, incentive draft targets) into quote-checked rows (plan 18 ph3) | `GuidanceItem`, `GuidanceReply`, `GuidanceResult`, `GuidanceExtractor` |
| `base_quoted_extractor.py` | shared base of the plan 28 document extractors: prompt file, per-item validation, quote check, keyword page picking (D-161 update 6) | `QuotedItem`, `QuotedResult`, `BaseQuotedExtractor` |
| `inquiry_customer_extractor.py` | DeepSeek reads exchange inquiry replies for named customers and suppliers, real names behind 客户一… (plan 28 ph2) | `InquiryCounterpartyItem`, `InquiryCustomerExtractor` |
| `counterparty_name.py` | rules for an LLM-returned counterparty name: real name or not (客户一, 某, 头部车企), name or short form in the quote (D-161 update 8) | `CounterpartyName` |
| `entity_alias_extractor.py` | DeepSeek proposes the entity of a batch of counterparty names: canonical short name, kind, group member, code hint (plan 28 ph3) | `AliasItem`, `EntityAlias`, `EntityAliasExtractor` |
| `entity_resolver.py` | one entity id per counterparty name: alias map, A-share full / short / former names, short-name prefix (plan 28 ph3) | `EntityMatch`, `EntityResolver` |
| `ir_customer_extractor.py` | DeepSeek reads IR Q&A and IR meeting records for named customers / suppliers / partners and the stage reached (plan 28 ph2) | `IrCounterpartyItem`, `IrCustomerExtractor` |
| `prospectus_extractor.py` | DeepSeek reads IPO prospectuses for top customers, suppliers and competitors (plan 28 ph2) | `ProspectusExtractor` |
| `deal_extractor.py` | DeepSeek reads investment and restructuring announcements into deal rows: kind, target, stake, amount, status (plan 28 ph2) | `DealItem`, `DealExtractor` |
| `buyback_terms_extractor.py` | DeepSeek reads buyback plans and holder 增持 plans into their terms: purpose / holder type, funding incl. 专项贷款, amount, price cap, period (plan 32 ph2) | `BuybackTermsItem`, `BuybackTermsExtractor` |
| `operating_data_extractor.py` | DeepSeek reads 主要经营数据 announcements into per-product revenue, volume, price and order figures (plan 28 ph2) | `OperatingDataItem`, `OperatingDataExtractor` |
| `broker_customer_extractor.py` | DeepSeek reads broker stock reports for the customers they name, with stage (plan 28 ph2) | `BrokerCustomerExtractor` |
| `contract_extractor.py` | DeepSeek reads 重大合同 / 中标 / 经营数据 announcements into contract and period order rows, amounts scaled (plan 18 ph3) | `ContractItem`, `ContractReply`, `ContractResult`, `ContractExtractor` |
| `lenient_item.py` | pydantic base for LLM reply items: numeric text ("30%") parsed into float fields | `LenientItem` |
| `quarterly_note_extractor.py` | DeepSeek reads the Q1/Q3 narrative notes (change reasons, 其他提醒事项): orders, customers, capacity, drivers, products | `QuarterlyNoteItem`, `QuarterlyNoteReply`, `QuarterlyNoteResult`, `QuarterlyNoteExtractor` |
| `legacy_label_importer.py` | imports earlier runs' jsonl / parse-parquet label files into LabelStore with document keys and public dates (plan 28 ph0) | `LegacyLabelImporter` |
| `business_mode_extractor.py` | DeepSeek reads 经营模式 text: variant among the archetype's candidates, pricing mode, cost pass-through, price actions, quote-checked (D-118) | `ModeClaim`, `PriceAction`, `BusinessModeReply`, `BusinessModeResult`, `BusinessModeExtractor` |
| `broker_view_synthesizer.py` | DeepSeek synthesizes many broker reports into one view per product, Shenwan L3 or company; every point cites report refs (citation check) | `ReportDigest`, `ViewPoint`, `BrokerViewReply`, `BrokerView`, `BrokerViewSynthesizer` |
| `moat_extractor.py` | DeepSeek reads 核心竞争力分析: claimed advantages by moat type with figures and quotes (§4.4) | `MoatClaim`, `MoatReply`, `MoatResult`, `MoatExtractor` |
| `pricing_adjudicator.py` | DeepSeek verdict on pricing power and the archetype for rule-open companies; reasons must cite supplied evidence keys (D-118) | `Reason`, `AdjudicationReply`, `Adjudication`, `PricingAdjudicator` |
| `product_taxonomy.py` | config/industry_chain loaded for lookups: nodes, merged ids, Shenwan L3 → segment context | `TaxonomyNode`, `ProductTaxonomy` |
| `product_matcher.py` | revenue lines (主营构成) mapped to taxonomy nodes by rules: generic filter, normalization, exact/contains/overlap scoring with Shenwan context, compound split, sector fallback (D-115) | `ProductMatch`, `ProductMatcher` |
| `base_edge_reader.py` | base of the plan 28 ph4 readers listing raw edges of a label row; item period parsing | `EdgeItem`, `BaseEdgeReader` |
| `company_edge_builder.py` | company_edge rows: one per stated edge, resolved, oriented, with period / known_on / evidence (plan 28 ph4) | `CompanyEdgeBuilder` |
| `counterparty_edge_reader.py` | raw edges of counterparty-list label rows (plan 28 sets, applications) | `CounterpartyEdgeReader` |
| `deal_edge_reader.py` | raw invests_in edges of outward deals | `DealEdgeReader` |
| `edge_span_builder.py` | edge_span rows: life cycle of each company edge, point in time (plan 28 ph4) | `EdgeSpanBuilder` |
| `top_five_edge_reader.py` | raw edges of annual top-5 customer / supplier tables | `TopFiveEdgeReader` |
| `game_company_builder.py` | game_company: approved games (版号) linked to the listed companies behind their holders (plan 31) | `GameCompanyBuilder` |
| `graph_builder.py` | rebuild company_edge and edge_span from the label store and entity_map (plan 28 ph4) | `GraphBuilder` |
| `company_period_builder.py` | company_period, the company leaf: one row per company, period, label set and document (plan 28 ph4) | `CompanyPeriodBuilder` |
| `graph_query.py` | point-in-time questions: company as known on a date, spans as of a date, timeline (plan 28 ph4) | `GraphQuery` |
| `node_member_builder.py` | node_member: company → taxonomy node per period by revenue weight (plan 28 ph3b-1) | `NodeMemberBuilder` |
| `node_stats_builder.py` | curation material from node_member: segment stats, period diff, unmatched lines (plan 28 ph3b-2) | `NodeStatsBuilder` |
| `taxonomy_change_set.py` | accepted taxonomy versions (config/industry_chain/_changes) applied on top of v0 (plan 28 ph3b-4) | `TaxonomyChange`, `TaxonomyChangeSet` |
| `node_edge_builder.py` | node_edge: supplier segment -> buyer segment per year, evidenced vs prior (plan 28 ph4d) | `NodeEdgeBuilder` |
| `node_lineage_builder.py` | node_lineage: what each taxonomy version changed, node by node (plan 28 ph3b-4) | `NodeLineageBuilder` |
