# tests/data_loading/

Tests for `quant_cn.data_loading`. No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `test_akshare_client.py` | tests for `akshare_client`, one function per TC ID |  |
| `test_baostock_client.py` | tests for `baostock_client`, one function per TC ID | `FakeResult` |
| `test_deep_seek_client.py` | tests for `deep_seek_client`, one function per TC ID | `FakeLlmTransport`, `BeijingClock` |
| `test_document_downloader.py` | tests for `request_pacer`, `document_classifier`, `document_downloader`, one function per TC ID | `FakeFileTransport` |
| `test_document_retyper.py` | Tests of DocumentManifestWriter and DocumentRetyper (TC-DMW-001, TC-DRT-001) | |
| `test_fetcher_factory.py` | tests for `fetcher_factory`, one function per TC ID |  |
| `test_fetchers.py` | tests for `fetchers`, one function per TC ID |  |
| `test_http_transport.py` | tests for `http_transport`, one function per TC ID | `CutResponse` |
| `test_tushare_client.py` | tests for `tushare_client`, one function per TC ID | `ScriptedTransport` |
| `test_snapshot_fetcher.py` | tests for `snapshot_fetcher`, one function per TC ID |  |
| `test_manual_series_client.py` | tests for `manual_series_client`, one function per TC ID (TC-MSC-001..003) | — |
| `test_nbs_house_price_client.py` | tests for `nbs_house_price_client` and `base_html_list_client`, one function per TC ID | `FakeTransport` |
| `test_nppa_game_client.py` | tests for `nppa_game_client`, one function per TC ID | — |
| `test_web_clients.py` | tests for `base_web_client`, `cninfo_client`, `eastmoney_report_client`, `app_store_client`, one function per TC ID | `FakeWebTransport`, `SplittingTransport` |
| `test_cboe_client.py` | tests for `cboe_client`, one function per TC ID | `FakeCsvTransport` |
