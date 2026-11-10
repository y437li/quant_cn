# tests/industry_graph/

Tests for `quant_cn.industry_graph`. No network; PDFs are generated in `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `test_application_extractor.py` | tests for `application_extractor`, one function per TC ID | `FakeLlm` |
| `test_report_parsing.py` | tests for `pdf_text_extractor`, `section_detector`, `counterparty_table_parser`, `annual_report_parser`, one function per TC ID |  |
| `test_valuation_extractor.py` | tests for `valuation_extractor` and `quote_checker`, one function per TC ID | `FakeLlm` |
| `test_quarterly_note_extractor.py` | tests for `quarterly_note_extractor`, one function per TC ID | `FakeLlm` |
| `test_business_mode_extractor.py` | tests for `business_mode_extractor`, one function per TC ID | `FakeLlm` |
| `test_broker_view_synthesizer.py` | tests for `broker_view_synthesizer`, one function per TC ID | `FakeLlm` |
| `test_moat_extractor.py` | tests for `moat_extractor`, one function per TC ID | `FakeLlm` |
| `test_pricing_adjudicator.py` | tests for `pricing_adjudicator`, one function per TC ID | `FakeLlm` |
| `test_product_matcher.py` | tests for `product_taxonomy` and `product_matcher`, one function per TC ID | |
