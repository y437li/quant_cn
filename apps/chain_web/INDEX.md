# apps/chain_web/

React + TypeScript front end (Vite, Cytoscape.js). Sources only: dependencies install and build in `~/.builds/chain_web` because the exFAT volume has no symlinks (APP_STANDARD §6).

## Folders
| Folder | Purpose |
|---|---|
| [`src/`](src/INDEX.md) | application code |
| [`tests/`](tests/INDEX.md) | Playwright smoke run |

## Files
| File | Purpose | Contains |
|---|---|---|
| `package.json` | pinned dependencies and scripts |  |
| `tsconfig.json` | strict TypeScript (JSON imports on for test fixtures) |  |
| `vite.config.ts` | dev proxy to the Go API; vitest config |  |
| `index.html` | page shell |  |
