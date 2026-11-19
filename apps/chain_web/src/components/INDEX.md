# apps/chain_web/src/components/

Shared components.

## Files
| File | Purpose | Contains |
|---|---|---|
| `chain-graph.tsx` | Cytoscape wrapper with lane / cose / dagre layouts and zoom controls | `ChainGraph` |
| `app-route.ts` | pages, sidebar groups (市场 / 监测 / 我的) and the hash ↔ page mapping (plan 15 ph7j) | `Page`, `NAV`, `readRoute`, `routeHash` |
| `app-route.test.ts` | vitest TC-AR-001..003 |  |
| `side-nav.tsx` | left sidebar with groups, current page, badges; folds into a menu button below 760 px | `SideNav` |
| `splitter.tsx` | draggable dossier width | `Splitter` |
| `context.tsx` | app context and selection | `Ctx`, `useApp` |
| `ui.tsx` | tags, links, KPI tiles, tabs, bars | `Tag`, `NodeLink`, `CompanyLink`, `Tabs` |
| `dupont-plane.tsx` | fixed DuPont plane (turnover 0–2, ROE −20–40%) with the market cloud, a highlighted group and paths | `DupontPlane` |
