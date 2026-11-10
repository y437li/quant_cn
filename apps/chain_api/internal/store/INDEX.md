# apps/chain_api/internal/store/

Data access. `JSONStore` reads the chain_view builder output for the demo and `watchlist.json` (plan 15 phase 7, read per request); plan 15 phase 2 adds a parquet store behind the same interface.

## Folders
| Folder | Purpose |
|---|---|
| [`testdata/`](testdata/INDEX.md) | fixture builder output for the tests |

## Files
| File | Purpose | Contains |
|---|---|---|
| `store.go` | types and the `Store` interface (incl. `GetWatchlist`) | `Store`, `Company`, `CompanyBrief`, `SearchHit`, `Maker`, `Network`, `ErrNotFound` |
| `json_store.go` | JSONStore: load, bootstrap, company with related briefs, views, sector companies | `JSONStore`, `NewJSONStore` |
| `queries.go` | search, makers, sector network (filters and joins only) | `FindHits`, `ListMakers`, `GetSectorNetwork` |
| `watchlist.go` | watchlist types and `GetWatchlist` (missing file = empty document) | `Watchlist`, `WatchlistEntry`, `WeeklyClose`, `GetWatchlist` |
| `json_store_test.go` | TC-ST-001..006 |  |
| `watchlist_test.go` | TC-ST-007..009 (present, absent, malformed) |  |
