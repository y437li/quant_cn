# apps/chain_api/internal/store/

Data access. `JSONStore` reads the chain_view builder output for the demo; plan 15 phase 2 adds a parquet store behind the same interface.

## Folders
| Folder | Purpose |
|---|---|
| [`testdata/`](testdata/INDEX.md) | fixture builder output for the tests |

## Files
| File | Purpose | Contains |
|---|---|---|
| `store.go` | types and the `Store` interface | `Store`, `Company`, `CompanyBrief`, `SearchHit`, `Maker`, `Network`, `ErrNotFound` |
| `json_store.go` | JSONStore: load, bootstrap, company with related briefs, views, sector companies | `JSONStore`, `NewJSONStore` |
| `queries.go` | search, makers, sector network (filters and joins only) | `FindHits`, `ListMakers`, `GetSectorNetwork` |
| `json_store_test.go` | TC-ST-001..006 |  |
