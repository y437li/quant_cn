# apps/chain_web/tests/

End-to-end checks.

## Files
| File | Purpose | Contains |
|---|---|---|
| `smoke.mjs` | Playwright smoke run: 5 companies, 3 sectors, 3 nodes, every tab, search, the watchlist page (cards, chart hover, link to a company, 国家队 ETF panel, 390px width); fails on errors |  |
| `shot_cards.mjs` | screenshots of app cards for phone alerts in a phone style (bigger figures, small print hidden, watchlist card trimmed to price and chart); used by `CardScreenshotter` (plan 22) |  |
