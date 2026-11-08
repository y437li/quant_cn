# apps/chain_api/cmd/chainapi/

The server binary: loads the store and serves /api plus the static front end on 127.0.0.1:8787.

## Files
| File | Purpose | Contains |
|---|---|---|
| `main.go` | flags -data, -web, -addr; wires JSONStore and api.Server | `main` |
