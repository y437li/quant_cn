# src/quant_cn/data_loading/

L3: Tushare client and one fetcher per sweep pattern; writes into the lake. May import from: L1, L2.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `akshare_client.py` | AkShare as a third data source (D-065): official lists and series Tushare lacks or denies | `AkshareClient` |
| `baostock_client.py` | BaoStock as a verification-only source (D-065, D-085): closes and adjustment factors | `BaostockClient` |
| `fetcher_factory.py` | Map a dataset's sweep kind to its fetcher class; new datasets of a known kind need no code | `FetcherFactory` |
| `fetchers.py` | One fetcher per sweep pattern (DATA_LOADING_DESIGN §2.2); the endpoint comes from DatasetSpec | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher`, `DateWindowFetcher` |
| `http_transport.py` | JSON-over-HTTP POST used by the Tushare client; the seam tests replace | `HttpTransport` |
| `tushare_client.py` | Tushare Pro over raw HTTP: paging, retries, rate-limit waits, permission errors (D-003) | `TushareClient` |
