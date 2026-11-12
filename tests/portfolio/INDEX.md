# tests/portfolio/

Tests for `quant_cn.portfolio`. No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_holdings_history_writer.py` | tests for `holdings_history_writer`, one function per TC ID |  |
| `test_holdings_risk_builder.py` | tests for `holdings_risk_builder` and `core.positions_book`, one function per TC ID | `FixedModel` |
| `test_watchlist_builder.py` | contract tests for `WatchlistBuilder` on a mini lake | TC-WB-001..009 |
| `test_etf_flow_calculator.py` | contract tests for `EtfFlowCalculator` on hand-built frames | TC-EFC-001..005 |
| `test_etf_proxy_builder.py` | contract tests for `EtfProxyBuilder` on a mini lake | TC-EP-001..004 |
