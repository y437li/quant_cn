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
| `quarterly_note_extractor.py` | DeepSeek reads the Q1/Q3 narrative notes (change reasons, 其他提醒事项): orders, customers, capacity, drivers, products | `QuarterlyNoteItem`, `QuarterlyNoteReply`, `QuarterlyNoteResult`, `QuarterlyNoteExtractor` |
| `business_mode_extractor.py` | DeepSeek reads 经营模式 text: variant among the archetype's candidates, pricing mode, cost pass-through, price actions, quote-checked (D-118) | `ModeClaim`, `PriceAction`, `BusinessModeReply`, `BusinessModeResult`, `BusinessModeExtractor` |
| `broker_view_synthesizer.py` | DeepSeek synthesizes many broker reports into one view per product, Shenwan L3 or company; every point cites report refs (citation check) | `ReportDigest`, `ViewPoint`, `BrokerViewReply`, `BrokerView`, `BrokerViewSynthesizer` |
| `pricing_adjudicator.py` | DeepSeek verdict on pricing power and the archetype for rule-open companies; reasons must cite supplied evidence keys (D-118) | `Reason`, `AdjudicationReply`, `Adjudication`, `PricingAdjudicator` |
| `product_taxonomy.py` | config/industry_chain loaded for lookups: nodes, merged ids, Shenwan L3 → segment context | `TaxonomyNode`, `ProductTaxonomy` |
| `product_matcher.py` | revenue lines (主营构成) mapped to taxonomy nodes by rules: generic filter, normalization, exact/contains/overlap scoring with Shenwan context, compound split, sector fallback (D-115) | `ProductMatch`, `ProductMatcher` | DeepSeek reads the Q1/Q3 narrative notes (change reasons, 其他提醒事项): orders, customers, capacity, drivers, products | `QuarterlyNoteItem`, `QuarterlyNoteReply`, `QuarterlyNoteResult`, `QuarterlyNoteExtractor` |
