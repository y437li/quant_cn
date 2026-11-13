# src/quant_cn/data_loading/

L3: vendor clients (Tushare, AkShare, BaoStock, CNINFO, Eastmoney), one fetcher per sweep pattern, the document downloader; writes into the lake. May import from: L1, L2.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `akshare_client.py` | AkShare as a third data source (D-065): official lists and series Tushare lacks or denies | `AkshareClient` |
| `baostock_client.py` | BaoStock as a verification-only source (D-065, D-085): closes and adjustment factors | `BaostockClient` |
| `base_web_client.py` | shared transport and pacing for clients that page public websites (D-096) | `BaseWebClient` |
| `manual_series_client.py` | hand-entered cycle series from config/manual_series.yaml (+ local licensed file) as source "manual" (plan 20, D-139) | `ManualSeriesClient`, `ManualSeriesDef`, `ManualObservation`, `ManualSeriesFile` |
| `app_store_client.py` | Apple App Store top charts from the public iTunes RSS feeds (D-137) | `AppStoreClient` |
| `cninfo_client.py` | CNINFO announcement metadata, the industry-chain graph document source (D-096) | `CninfoClient` |
| `deep_seek_client.py` | DeepSeek chat completions as a JSON-returning LLM client with response cache, cost and ledger (D-098) | `DeepSeekClient` |
| `document_classifier.py` | title rules → document type (config/documents.yaml, D-101) | `DocumentClassifier` |
| `document_downloader.py` | fetch listed PDFs into documents/ with a manifest of hashes (plan 12 phase 2, D-101) | `DocumentDownloader` |
| `document_manifest_writer.py` | Append-only manifest parts of downloaded documents (D-101, D-149) | `DocumentManifestWriter` |
| `document_retyper.py` | Re-apply changed title rules to downloaded documents (plan 18 ph2, D-149) | `DocumentRetyper` |
| `eastmoney_report_client.py` | Eastmoney research-report lists: broker stock and industry reports with PDF links (D-100) | `EastmoneyReportClient` |
| `fetcher_factory.py` | Map a dataset's sweep kind to its fetcher class; new datasets of a known kind need no code | `FetcherFactory` |
| `fetchers.py` | One fetcher per sweep pattern (DATA_LOADING_DESIGN §2.2); the endpoint comes from DatasetSpec | `SingleCallFetcher`, `EnumFetcher`, `DateSweepFetcher`, `PeriodSweepFetcher`, `DateWindowFetcher` |
| `http_transport.py` | HTTP calls used by the vendor clients (JSON POST, form POST, GET); the seam tests replace | `HttpTransport` |
| `snapshot_fetcher.py` | Sweep for sources that only serve the current state (App Store charts, D-137): today only | `SnapshotFetcher` |
| `request_pacer.py` | polite, retried requests to public websites, shared by threads (D-096) | `RequestPacer` |
| `tushare_client.py` | Tushare Pro over raw HTTP: paging, retries, rate-limit waits, permission errors (D-003) | `TushareClient` |
