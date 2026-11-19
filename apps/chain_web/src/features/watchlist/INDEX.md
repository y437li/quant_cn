# apps/chain_web/src/features/watchlist/

观察账本 page at `#watchlist` (plan 15 phase 7, D-120). Read-only display of `GET /api/watchlist` and `GET /api/etf-proxy`; every number comes from the Python `WatchlistBuilder` / `EtfProxyBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `watchlist-page.tsx` | headline (nearest stock, as-of), one card per stock or ETF (ETF tag, no valuation, ph7p), valuation table (stocks only), empty state, data notes | `WatchlistPage` |
| `watchlist-charts.tsx` | SVG range bar (52-week line, buy zone, broker target box, price dot) and weekly close chart with hover tooltip | `RangeBar`, `WeeklyChart` |
| `etf-proxy-panel.tsx` | 国家队 ETF panel (phase 7b; shown on the ETF 监测 page `#etf`): headline, weekly core / other position chart with hover, weekly core flow bars, last days, per-index table, per-index rhythm table (分指数节奏: peak, trough, 近3月分位 / 区间, added since, recent flows, drawdown), 近3月 line, per-index weekly flow matrix (ph7o) | `EtfProxyPanel` |
| `etf-proxy-format.ts` | pure helpers of the panel: 亿元 and signed flows, flow class, headline, position with month, drawdown %, 近3月 percentile / range / line, weekly flow matrix and heat | `yi`, `signedNum`, `signedYi`, `flowClass`, `proxyHeadline`, `markYi`, `pctDown`, `pctRank`, `windowRange`, `windowLine`, `flowMatrix`, `heat` |
| `etf-proxy-format.test.ts` | vitest TC-EPW-001..006 |  |
| `watchlist-format.ts` | pure display helpers: status label, number formats, nearest entry, badge count, label placement, scales, reason bullets (`splitPoints`) | `STATUS_ZH`, `statusLabel`, `gapText`, `nearestEntry`, `badgeCount`, `placeLabels`, `niceTicks`, `splitPoints` |
| `point-list.tsx` | a reason text (理由 / 逻辑 / 要盯) as a bullet list | `PointList`, `Points` |
| `watchlist-format.test.ts` | vitest TC-WL-001..010 against the sample |  |
| `watchlist.fixture.json` | WatchlistBuilder sample of 2026-11-06 (same as the Go fixture) |  |
