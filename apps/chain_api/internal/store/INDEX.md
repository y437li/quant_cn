# apps/chain_api/internal/store/

Data access. `JSONStore` reads the chain_view builder output for the demo and `watchlist.json` / `etf_proxy.json` / `factor_monitor.json` / `holdings_risk.json` (plan 15 phases 7, 7b, 7c, 7d; read per request); plan 15 phase 2 adds a parquet store behind the same interface.

## Folders
| Folder | Purpose |
|---|---|
| [`testdata/`](testdata/INDEX.md) | fixture builder output for the tests |

## Files
| File | Purpose | Contains |
|---|---|---|
| `factor_monitor.go` | `GetFactorMonitor`: serve factor_monitor.json as written by Python (plan 15 ph7c) | `FactorMonitor`, `MonitoredFactor`, `FactorReturns` |
| `factor_monitor_test.go` | TC-ST-013..015 |  |
| `holdings_risk.go` | `GetHoldingsRisk`: serve holdings_risk.json as written by Python (plan 15 ph7d) | `HoldingsRisk`, `HoldingPosition`, `HoldingFactor`, `Correlation` |
| `holdings_risk_test.go` | TC-ST-016..019 |  |
| `store.go` | types and the `Store` interface (incl. `GetWatchlist`, `GetEtfProxy`, `GetFactorMonitor`, `GetHoldingsRisk`, `GetMacroMonitor`, `GetFuturesMonitor`) | `Store`, `Company`, `CompanyBrief`, `SearchHit`, `Maker`, `Network`, `ErrNotFound` |
| `json_store.go` | JSONStore: load, bootstrap, company with related briefs, views, sector companies | `JSONStore`, `NewJSONStore` |
| `queries.go` | search, makers, sector network (filters and joins only) | `FindHits`, `ListMakers`, `GetSectorNetwork` |
| `watchlist.go` | watchlist types and `GetWatchlist` (missing file = empty document) | `Watchlist`, `WatchlistEntry`, `WeeklyClose`, `GetWatchlist` |
| `margin_panel.go` | `GetMargin`: one stock's 融资融券 document from margin/<code>.json (plan 15 ph7m) | `GetMargin` |
| `margin_panel_test.go` | TC-ST-025 |  |
| `futures_monitor.go` | futures monitor types and `GetFuturesMonitor` (missing file = empty document; plan 15 ph7i) | `FuturesMonitor`, `FuturesFamily`, `FuturesSpread`, `FuturesFlag`, `GetFuturesMonitor` |
| `futures_monitor_test.go` | TC-ST-023..024 |  |
| `rates_fx_monitor.go` | `GetRatesFxMonitor`: rates_fx_monitor.json as is (missing file = ErrNotFound; plan 34) | `GetRatesFxMonitor` |
| `rates_fx_monitor_test.go` | TC-ST-029 | — |
| `sector_earnings_signal.go` | `GetSectorEarningsSignal`: sector_earnings_signal.json as is (missing file = ErrNotFound; plan 35) | `GetSectorEarningsSignal` |
| `sector_earnings_signal_test.go` | TC-ST-031 | — |
| `opportunities.go` | `GetOpportunities`: opportunities.json as is (missing file = ErrNotFound; plan 21 ph5) | `GetOpportunities` |
| `opportunities_test.go` | TC-ST-033 | — |
| `buyback_monitor.go` | `GetBuybackMonitor`: buyback_monitor.json as is (missing file = ErrNotFound; plan 32) | `GetBuybackMonitor` |
| `buyback_monitor_test.go` | TC-ST-030 | — |
| `task_status.go` | `GetTaskStatus`: task_status.json as is (missing file = ErrNotFound; plan 38) | `GetTaskStatus` |
| `task_status_test.go` | TC-ST-032 | — |
| `sector_monitor.go` | `GetSectorMonitor`: sector_monitor.json as is (missing file = ErrNotFound; plan 31 ph5) | `GetSectorMonitor` |
| `sector_monitor_test.go` | TC-ST-028 |  |
| `volatility_monitor.go` | volatility monitor types and `GetVolatilityMonitor` (missing file = empty document; plan 03 ph6), with smallcap_watch.json attached as `SmallCap` (plan 30 ph2; weekly share and balance, past 去杠杆 episodes ph6 / ph7) | `VolatilityMonitor`, `VolLine`, `VolPoint`, `VolAlerts`, `VolFlag`, `GetVolatilityMonitor` |
| `volatility_monitor_test.go` | TC-ST-025..027 |  |
| `macro_monitor.go` | macro monitor types and `GetMacroMonitor` (missing file = empty document; plan 15 ph7h) | `MacroMonitor`, `MacroSeries`, `MacroPoint`, `GetMacroMonitor` |
| `macro_monitor_test.go` | TC-ST-021..022 |  |
| `etf_proxy.go` | national-team ETF proxy types and `GetEtfProxy` (missing file = empty document) | `EtfProxy`, `ProxyTotals`, `ProxyIndex`, `ProxyWindow`, `ProxyWeek`, `GetEtfProxy` |
| `json_store_test.go` | TC-ST-001..006 |  |
| `watchlist_test.go` | TC-ST-007..009 (present, absent, malformed), TC-ST-020 (conditions) |  |
| `etf_proxy_test.go` | TC-ST-010..012 (present, absent / null slices, malformed) |  |
| `conditions.go` | condition result, position note, flag and review types of the 7f fields in watchlist.json / holdings_risk.json | `ConditionResult`, `PositionNote`, `ReviewFlag`, `PositionReview` |
