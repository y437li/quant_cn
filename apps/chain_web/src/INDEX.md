# apps/chain_web/src/

Application code.

## Folders
| Folder | Purpose |
|---|---|
| [`api/`](api/INDEX.md) | typed client of openapi.yaml |
| [`lib/`](lib/INDEX.md) | display formatters |
| [`graph/`](graph/INDEX.md) | taxonomy index, Cytoscape element builders, styles |
| [`components/`](components/INDEX.md) | shared UI, graph, splitter, context |
| [`features/`](features/INDEX.md) | company, node, sector, search, DuPont and watchlist views |

## Files
| File | Purpose | Contains |
|---|---|---|
| `main.tsx` | entry |  |
| `app.tsx` | shell: header (page chips with the watchlist badge), graph stage, resizable dossier, hash navigation (`#co=`, `#dupont=`, `#watchlist`) | `App` |
| `styles.css` | tokens and layout (light / dark), ported from the prototype |  |
| `types.d.ts` | module declaration for cytoscape-dagre |  |
