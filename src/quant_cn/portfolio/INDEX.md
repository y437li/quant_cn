# src/quant_cn/portfolio/

L5: position sizing, constraints, rebalancing schedules. May import from: L1–L4.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `holdings_history_writer.py` | Daily history of the user's book in the lake (derived/holdings_positions, holdings_risk; plan 15 ph7d) | `HoldingsHistoryWriter` |
| `holdings_risk_builder.py` | The user's book valued at the last risk session and its risk decomposition for the 持仓 page (plan 15 ph7d, D-132) | `HoldingsRiskBuilder` |
| `watchlist_builder.py` | the chain app's watchlist document: gap to buy price, status, valuation at the buy price (plan 15 ph7, D-120) | `WatchlistBuilder` |
| `etf_flow_calculator.py` | ETF membership per index, split-proof daily net flows, position at today's price (plan 15 ph7b, D-126) | `EtfFlowCalculator` |
| `etf_proxy_builder.py` | the chain app's 国家队 ETF document: core vs other, per index, weekly, yearly, recent days (plan 15 ph7b, D-126) | `EtfProxyBuilder` |
