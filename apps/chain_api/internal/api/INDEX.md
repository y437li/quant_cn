# apps/chain_api/internal/api/

HTTP layer: routes /api/* to the Store, everything else to the static front end.

## Files
| File | Purpose | Contains |
|---|---|---|
| `handlers.go` | `Server` and its handlers (400 / 404 / 405 / 500 rules), incl. `/api/watchlist` | `Server`, `NewServer` |
| `handlers_test.go` | TC-API-001..007 |  |
