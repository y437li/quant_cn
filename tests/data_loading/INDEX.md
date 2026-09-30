# tests/data_loading/

Tests for `quant_cn.data_loading`. No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_akshare_client.py` | tests for `akshare_client`, one function per TC ID |  |
| `test_baostock_client.py` | tests for `baostock_client`, one function per TC ID | `FakeResult` |
| `test_fetcher_factory.py` | tests for `fetcher_factory`, one function per TC ID |  |
| `test_fetchers.py` | tests for `fetchers`, one function per TC ID |  |
| `test_tushare_client.py` | tests for `tushare_client`, one function per TC ID | `ScriptedTransport` |
