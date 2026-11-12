# apps/chain_api/internal/store/

Data access. `JSONStore` reads the chain_view builder output for the demo and `watchlist.json` / `etf_proxy.json` / `factor_monitor.json` / `holdings_risk.json` (plan 15 phases 7, 7b, 7c, 7d; read per request); plan 15 phase 2 adds a parquet store behind the same interface.

## Folders
| Folder | Purpose |
|---|---|
| [`testdata/`](testdata/INDEX.md) | fixture builder output for the tests |

## Files
| File | Purpose | Contains |
|---|---|---|
| `factor_monitor.go` | `GetFactorMonitor`: serve factor_monitor.json as written by Python (plan 15 ph7c) | `FactorMonitor`, `MonitoredFactor`, `FactorReturns` |
| `factor_monitor_test.go` | TC-ST-013..015 |  |
| `holdings_risk.go` | `GetHoldingsRisk`: serve holdings_risk.json as written by Python (plan 15 ph7d) | `HoldingsRisk`, `HoldingPosition`, `HoldingFactor`, `Correlation` |
| `holdings_risk_test.go` | TC-ST-016..018 |  |
| `store.go` | types and the `Store` interface (incl. `GetWatchlist`, `GetEtfProxy`, `GetFactorMonitor`, `GetHoldingsRisk`) | `Store`, `Company`, `CompanyBrief`, `SearchHit`, `Maker`, `Network`, `ErrNotFound` |
| `json_store.go` | JSONStore: load, bootstrap, company with related briefs, views, sector companies | `JSONStore`, `NewJSONStore` |
| `queries.go` | search, makers, sector network (filters and joins only) | `FindHits`, `ListMakers`, `GetSectorNetwork` |
| `watchlist.go` | watchlist types and `GetWatchlist` (missing file = empty document) | `Watchlist`, `WatchlistEntry`, `WeeklyClose`, `GetWatchlist` |
| `etf_proxy.go` | national-team ETF proxy types and `GetEtfProxy` (missing file = empty document) | `EtfProxy`, `ProxyTotals`, `ProxyIndex`, `ProxyWeek`, `GetEtfProxy` |
| `json_store_test.go` | TC-ST-001..006 |  |
| `watchlist_test.go` | TC-ST-007..009 (present, absent, malformed) |  |
| `etf_proxy_test.go` | TC-ST-010..012 (present, absent / null slices, malformed) |  |
