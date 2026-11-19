# apps/chain_web/src/features/margin/

融资融券 tab of the company dossier (plan 15 ph7m). Read-only display of `GET /api/margin/{code}`; numbers from the Python `MarginPanelBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `margin-tab.tsx` | headline, warnings, financing and short balance charts, forced-liquidation ladder | `MarginTab` |
| `margin-format.ts` | pure helpers: headline, contrarian warnings, first liquidation price | `marginHeadline`, `marginWarnings`, `firstLiquidation` |
| `margin-format.test.ts` | vitest TC-MGF-001..002 |  |
