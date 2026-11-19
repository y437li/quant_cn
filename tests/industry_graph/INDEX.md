# tests/industry_graph/

Tests for `quant_cn.industry_graph`. No network; PDFs are generated in `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `test_application_extractor.py` | tests for `application_extractor`, one function per TC ID | `FakeLlm` |
| `test_report_parsing.py` | tests for `pdf_text_extractor`, `section_detector`, `counterparty_table_parser`, `annual_report_parser`, one function per TC ID |  |
| `test_valuation_extractor.py` | tests for `valuation_extractor` and `quote_checker`, one function per TC ID | `FakeLlm` |
| `test_guidance_extractor.py` | tests for `guidance_extractor` (TC-GE-001..003), one function per TC ID | `FakeLlm` |
| `test_base_quoted_extractor.py` | tests for `base_quoted_extractor` (TC-BQE-001..005) | `FakeLlm`, `NameItem`, `NameExtractor`, `AnswerExtractor`, `AnchoredExtractor` |
| `test_inquiry_customer_extractor.py` | tests for `inquiry_customer_extractor` (TC-ICE-001..003) | `FakeLlm` |
| `test_ir_customer_extractor.py` | tests for `ir_customer_extractor` (TC-IRC-001..003) | `FakeLlm` |
| `test_prospectus_extractor.py` | tests for `prospectus_extractor` (TC-PRE-001..002) | `FakeLlm` |
| `test_entity_alias_extractor.py` | tests for `entity_alias_extractor` (TC-EAX-001..002) | `FakeLlm` |
| `test_entity_resolver.py` | tests for `entity_resolver` (TC-ER-001..007) | — |
| `test_counterparty_name.py` | tests for `counterparty_name` (TC-CPN-001..003) | — |
| `test_deal_extractor.py` | tests for `deal_extractor` (TC-DEX-001..002) | `FakeLlm` |
| `test_buyback_terms_extractor.py` | tests for `buyback_terms_extractor` (TC-BTX-001..003) | `FakeLlm` |
| `test_operating_data_extractor.py` | tests for `operating_data_extractor` (TC-ODX-001..002) | `FakeLlm` |
| `test_broker_customer_extractor.py` | tests for `broker_customer_extractor` (TC-BCE-001..002) | `FakeLlm` |
| `test_contract_extractor.py` | tests for `contract_extractor` (TC-CEX-001..002) | `FakeLlm` |
| `test_lenient_item.py` | tests for `lenient_item` (TC-LI-001) | `NumberItem` |
| `test_quarterly_note_extractor.py` | tests for `quarterly_note_extractor`, one function per TC ID | `FakeLlm` |
| `test_legacy_label_importer.py` | tests for `legacy_label_importer`, one function per TC ID |  |
| `test_business_mode_extractor.py` | tests for `business_mode_extractor`, one function per TC ID | `FakeLlm` |
| `test_broker_view_synthesizer.py` | tests for `broker_view_synthesizer`, one function per TC ID | `FakeLlm` |
| `test_moat_extractor.py` | tests for `moat_extractor`, one function per TC ID | `FakeLlm` |
| `test_pricing_adjudicator.py` | tests for `pricing_adjudicator`, one function per TC ID | `FakeLlm` |
| `test_product_matcher.py` | tests for `product_taxonomy` and `product_matcher`, one function per TC ID | |
| `test_edge_readers.py` | tests for `base_edge_reader`, `counterparty_edge_reader`, `top_five_edge_reader`, `deal_edge_reader` (TC-BER-001, TC-CER-001..002, TC-TFR-001, TC-DER-001) | — |
| `test_company_edge_builder.py` | tests for `company_edge_builder` (TC-CEB-001..003) | — |
| `test_edge_span_builder.py` | tests for `edge_span_builder` (TC-ESB-001..003) | — |
| `test_game_company_builder.py` | tests for `game_company_builder`, one function per TC ID | — |
| `test_graph_builder.py` | tests for `graph_builder` (TC-GB-001..004) | — |
| `test_company_period_builder.py` | tests for `company_period_builder` (TC-CPB-001..002) | — |
| `test_graph_query.py` | tests for `graph_query` (TC-GQ-001..003) | — |
| `test_node_member_builder.py` | tests for `node_member_builder` (TC-NMB-001..005) | — |
| `test_node_stats_builder.py` | tests for `node_stats_builder` (TC-NSB-001..003) | — |
| `test_taxonomy_change_set.py` | tests for `taxonomy_change_set` (TC-TCS-001..002) | — |
| `test_node_edge_builder.py` | tests for `node_edge_builder` (TC-NEB-001..004) | — |
| `test_node_lineage_builder.py` | tests for `node_lineage_builder` (TC-NLB-001..002) | — |
