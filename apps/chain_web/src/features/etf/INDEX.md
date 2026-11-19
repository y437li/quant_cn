# apps/chain_web/src/features/etf/

ETF 监测 page at `#etf` (plan 15 ph7b panel, own page since ph7j). The panel itself lives in `../watchlist/etf-proxy-panel.tsx`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `etf-page.tsx` | page shell: heading, intro line, style panel, the 国家队 ETF panel | `EtfPage` |
| `etf-style-panel.tsx` | 风格 ETF 资金强度 cards (银行, 红利): status, z, 20-day flow vs AUM, weekly z chart (plan 15 ph7g) | `EtfStylePanel` |
| `etf-style-format.ts` | pure helpers: status labels, headline, z chart points | `STATUS_ZH`, `styleHeadline`, `stylePoints` |
| `etf-style-format.test.ts` | vitest TC-ESF-001..002 |  |
