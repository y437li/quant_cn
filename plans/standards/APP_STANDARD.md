# APP_STANDARD — Go API and React front end (plan 15, D-116)

Addendum to CODING_STANDARD.md for `apps/`. Python rules still govern everything under `src/`.

## 1. What may live in apps/
- **No business logic.** Matching, similarity, statistics, cycle clocks, synthesis and any number shown come from Python tables (or, for the demo, the prototype builder's JSON). Go filters, joins and paginates. React lays out and draws.
- Read-only. The API never writes the lake and never opens `meta/quant_cn.duckdb`.

## 2. Contracts
- `apps/chain_api/openapi.yaml` is the single API contract. Every handler matches it, and the TypeScript client types are written from it.
- Go: every exported type and function carries a doc comment with **Purpose**, **Contract** (input, output, errors) and **Test cases** (TC ids), as Python docstrings do.
- TypeScript: every exported component and function carries a TSDoc block with Purpose and Contract.

## 3. Layout
- `apps/chain_api/`:
  - `cmd/chainapi` (main);
  - `internal/store` (data access behind the `Store` interface);
  - `internal/api` (HTTP handlers);
  - `web/` (the embedded front-end build).
- `apps/chain_web/src/`:
  - `api/` (typed client);
  - `graph/` (Cytoscape element building from API data);
  - `features/<company|node|sector|search>/`;
  - `components/` (shared UI).
- Every folder has an INDEX.md (CODING_STANDARD §5.1). Generated folders (`web/dist`) are exempt.

## 4. Size, naming, style
- Functions ≤ 50 lines and files ≤ 400 lines, as in Python. Go uses gofmt and `go vet`. TS uses strict mode, eslint and prettier defaults.
- Names: Go `MixedCaps` with verb-first functions (`GetCompany`, `ListPeers`). React components `PascalCase`, hooks `useX`, files `kebab-case.ts(x)`.

## 5. Tests and checks
- Go: `go test ./...` with fixture data under `internal/store/testdata`. Each handler has a test per TC id.
- TS: Vitest for element builders and formatters. A Playwright smoke run opens the demo companies and every tab and fails on any console error.
- `make app-check` = `go vet` + `go test` + `tsc --noEmit` + vitest. It is part of `make check` once the front end exists.

## 6. Environment (exFAT volume)
- Go caches stay in `$HOME` (the defaults).
- Front-end dependencies cannot live on the exFAT repo volume, which has no symlinks. `make app-web` mirrors `apps/chain_web` to `$HOME/.builds/chain_web`, installs and builds there, and copies `dist/` to `apps/chain_api/web/dist`.
- Node is Homebrew `node@22` (arm64).
