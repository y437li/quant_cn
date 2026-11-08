# apps/chain_web/src/graph/

Graph building (layout only, no business numbers).

## Files
| File | Purpose | Contains |
|---|---|---|
| `taxonomy.ts` | taxonomy index and walk | `buildIndex`, `walk` |
| `elements.ts` | elements per view | `buildCompanyElements`, `buildNodeElements`, `buildSectorElements`, `buildNetworkElements` |
| `elements.test.ts` | TC-EL-001..004 |  |
| `styles.ts` | Cytoscape stylesheet from CSS variables | `buildStyles` |
