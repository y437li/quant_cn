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
