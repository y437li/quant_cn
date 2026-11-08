# tests/data_loading/

Tests for `quant_cn.data_loading`. No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_akshare_client.py` | tests for `akshare_client`, one function per TC ID |  |
| `test_baostock_client.py` | tests for `baostock_client`, one function per TC ID | `FakeResult` |
| `test_deep_seek_client.py` | tests for `deep_seek_client`, one function per TC ID | `FakeLlmTransport`, `BeijingClock` |
| `test_document_downloader.py` | tests for `request_pacer`, `document_classifier`, `document_downloader`, one function per TC ID | `FakeFileTransport` |
| `test_fetcher_factory.py` | tests for `fetcher_factory`, one function per TC ID |  |
| `test_fetchers.py` | tests for `fetchers`, one function per TC ID |  |
| `test_http_transport.py` | tests for `http_transport`, one function per TC ID | `CutResponse` |
| `test_tushare_client.py` | tests for `tushare_client`, one function per TC ID | `ScriptedTransport` |
| `test_web_clients.py` | tests for `base_web_client`, `cninfo_client`, `eastmoney_report_client`, one function per TC ID | `FakeWebTransport`, `SplittingTransport` |
