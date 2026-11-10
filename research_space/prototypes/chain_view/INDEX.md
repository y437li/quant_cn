# research_space/prototypes/chain_view/

Industry-chain view (plan 12 phase 6), market-wide since 2026-11-07: a chain network (dagre, upstream → downstream) and a tabbed company dossier (overview, products and services, customers, suppliers, peers, chain, evidence). Published as a private artifact: https://claude.ai/artifact/5LYDCKATYJnPnsbY2Rvu3z

Generated, git-ignored (rebuild with `build_market_view.py`): `view_data.json`, `views.json`, `co/*.json`; the 10-company prototype data `view_data_proto10.json`. `watchlist.json` (git-ignored, personal targets) is written by `make watchlist` (D-120).

## Folders
| Folder | Purpose |
|---|---|
| [`co/`](co/INDEX.md) | generated per-Shenwan-L1 company detail, loaded by the page on demand |

## Files
| File | Purpose | Contains |
|---|---|---|
| `applications.json` | DeepSeek business-section results for the 10 companies (quote-checked) | |
| `build_market_view.py` | builds the market-wide `view_data.json` and `co/` from lake staging outputs (annual parse, DeepSeek applications and valuations, Tushare main business, Shenwan members) | `QUICK` |
| `build_view_data.py` | builds `view_data.json` from config/industry_chain, 10 FY2025 reports (AnnualReportParser) and Tushare `fina_mainbz_vip`; manual bz_item mapping stands in for phase 4 | `MANUAL`, `COMPANIES` |
| `index.html` | the page: cytoscape network, sector company network, search, tabs, lazy company detail | |
| `index_proto10.html` | the 10-company prototype page, kept for reference | |
| `run_application_pilot.py` | plan 12 ph4a pilot: ApplicationExtractor over the 10 reports, cost to the ledger | |
| `run_valuation_pilot.py` | plan 13 pilot: ValuationExtractor over 28 broker reports of the 10 companies, cost to the ledger | |
| `valuations.json` | ValuationExtractor results for 28 broker reports (quote-checked, implied vs target multiples) | |
