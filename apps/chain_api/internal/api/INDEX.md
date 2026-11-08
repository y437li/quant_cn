# apps/chain_api/internal/api/

HTTP layer: routes /api/* to the Store, everything else to the static front end.

## Files
| File | Purpose | Contains |
|---|---|---|
| `handlers.go` | `Server` and its handlers (400 / 404 / 405 rules) | `Server`, `NewServer` |
| `handlers_test.go` | TC-API-001..006 |  |
