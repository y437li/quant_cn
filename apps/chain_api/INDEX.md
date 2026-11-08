# apps/chain_api/

Go module `quantcn/chainapi`: the read-only API described in `openapi.yaml`. Build with `make app-api`; run with `make app-run`.

## Folders
| Folder | Purpose |
|---|---|
| [`cmd/`](cmd/INDEX.md) | entry points |
| [`internal/`](internal/INDEX.md) | store and HTTP handlers |
| [`web/`](web/INDEX.md) | the built front end it serves |

## Files
| File | Purpose | Contains |
|---|---|---|
| `go.mod` | module definition (no third-party dependencies in the demo) |  |
| `openapi.yaml` | the API contract: every handler and the TS client follow it |  |
