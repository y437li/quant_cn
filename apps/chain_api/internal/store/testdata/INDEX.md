# apps/chain_api/internal/store/testdata/

Fixture: a four-company builder output.

## Folders
| Folder | Purpose |
|---|---|
| [`co/`](co/INDEX.md) | per-sector detail fixture |

## Files
| File | Purpose | Contains |
|---|---|---|
| `factor_monitor.json` | FactorMonitorBuilder sample (3 factors, 2 sessions) for TC-ST-013, TC-API-009 |  |
| `holdings_risk.json` | HoldingsRiskBuilder sample (3 positions, one without a close) for TC-ST-016, TC-API-010 |  |
| `view_data.json` | taxonomy, sectors, quick list, four companies |  |
| `views.json` | one product view |  |
| `watchlist.json` | WatchlistBuilder sample of 2026-11-06 (涪陵榨菜, 盐津铺子) |  |
| `futures_monitor.json` | synthetic FuturesMonitorBuilder output (铜 with a new curve signal, 生猪 with null slices, 猪粮比) for TC-ST-023, TC-API-013 |  |
| `smallcap_watch.json` | synthetic SmallCapWatchBuilder output (a triggered gap row with pct, a near level row, a null-value flow row; null gap_pct in history) for TC-ST-027 |
| `volatility_monitor.json` | synthetic VolatilityMonitorBuilder output (美国 VIX with a level flag, 300ETF VIX with null change and percentile) for TC-ST-025, TC-API-014; copied to the web fixture |  |
| `macro_monitor.json` | synthetic MacroMonitorBuilder output (2 lines, one null prev) for TC-ST-021, TC-API-012 |  |
| `etf_proxy.json` | trimmed EtfProxyBuilder output of 2026-11-06 (core / other totals, 2 indices) |  |
