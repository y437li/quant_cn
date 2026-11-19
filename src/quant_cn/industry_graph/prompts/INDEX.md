# src/quant_cn/industry_graph/prompts/

LLM prompts as text files, so wording changes need no code change. Changing a prompt changes the response-cache key (D-098).

## Files
| File | Purpose | Contains |
|---|---|---|
| `application_extraction.txt` | business-section reading: downstream applications per revenue line, named counterparties and their roles, verbatim quotes | system prompt for `ApplicationExtractor` |
| `business_mode_extraction.txt` | 经营模式 reading: variant, pricing mode, pass-through, price actions with quotes | system prompt for `BusinessModeExtractor` |
| `broker_view_synthesis.txt` | many broker digests → method consensus, multiple range and reasons, drivers, bull, risks, divergence, recent change, each citing refs | system prompt for `BrokerViewSynthesizer` |
| `moat_extraction.txt` | 核心竞争力 reading: claims by moat type (cost, switching, intangible, network, efficient scale) with figures and quotes | system prompt for `MoatExtractor` |
| `pricing_adjudication.txt` | pricing-power and archetype verdict from keyed signals, annual claims and broker summary | system prompt for `PricingAdjudicator` |
| `quarterly_note_extraction.txt` | Q1/Q3 note reading: orders, customers, capacity, profit drivers, products, verbatim quotes | system prompt for `QuarterlyNoteExtractor` |
| `valuation_extraction.txt` | broker-report valuation: methods with implied/target multiples and base year, target price, forecasts, comparables, assumptions | system prompt for `ValuationExtractor` |
| `guidance_annual_plan.txt` | annual-report outlook / 经营计划: numeric targets for future periods, no past actuals or industry forecasts | `GuidanceExtractor` prompt (annual_plan) |
| `guidance_ir_record.txt` | IR activity record: management's numeric guidance, no investor questions or past facts | `GuidanceExtractor` prompt (ir_record) |
| `guidance_incentive_plan.txt` | incentive draft 公司层面业绩考核: target value (Am) per year and metric, base year, trigger in condition | `GuidanceExtractor` prompt (incentive_plan) |
| `inquiry_customer_extraction.txt` | inquiry replies: customers and suppliers, alias behind 客户一, amount (sales / purchases only), share, product, region | system prompt for `InquiryCustomerExtractor` |
| `ir_customer_extraction.txt` | IR Q&A / records: named customers, suppliers, partners, stage; answers only | system prompt for `IrCustomerExtractor` |
| `prospectus_extraction.txt` | prospectuses: top customers and suppliers per year, competitors | system prompt for `ProspectusExtractor` |
| `deal_extraction.txt` | investments, acquisitions, disposals, restructurings: kind, target, business, counterparty, stake, amount, status | system prompt for `DealExtractor` |
| `buyback_terms_extraction.txt` | 回购方案 / 增持计划: kind, purpose or holder type, funding (专项贷款 bank and amount), amount range with unit, shares / ratio, price cap, period, method | system prompt for `BuybackTermsExtractor` |
| `operating_data_extraction.txt` | 主要经营数据: per-product revenue, output, volume, price, orders, backlog, capacity of the own period, yoy | system prompt for `OperatingDataExtractor` |
| `broker_customer_extraction.txt` | broker stock reports: named customers / suppliers / partners and stage; no investees, peers or forecasts | system prompt for `BrokerCustomerExtractor` |
| `contract_extraction.txt` | contract / bid / operating-data announcements: counterparty, amount and unit, status, period order totals | system prompt for `ContractExtractor` |
| `entity_alias.txt` | system prompt of `EntityAliasExtractor`: canonical short name, kind, is_member, listed code per name (plan 28 ph3) | — |
