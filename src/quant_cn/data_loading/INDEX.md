# src/quant_cn/data_loading/

L3: Tushare client and one fetcher per sweep pattern; writes into the lake. May import from: L1, L2.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `fetcher_factory.py` | Map a dataset's sweep kind to its fetcher class; new datasets of a known kind need no code | `FetcherFactory` |
| `fetchers.py` | One fetcher per sweep pattern (DATA_LOADING_DESIGN §2.2); the endpoint comes from DatasetSpec | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher` |
| `http_transport.py` | JSON-over-HTTP POST used by the Tushare client; the seam tests replace | `HttpTransport` |
| `tushare_client.py` | Tushare Pro over raw HTTP: paging, retries, rate-limit waits, permission errors (D-003) | `TushareClient` |
