# config/

Configuration only, no code. Loaded by `core.Config`; secrets never live here (env only).

## Folders
| Folder | Purpose |
|---|---|
| [`industry_chain/`](industry_chain/INDEX.md) | product taxonomy and chain skeleton, one YAML per Shenwan L1 sector (plan 12, D-097) |

## Files
| File | Purpose | Contains |
|---|---|---|
| `README.md` | meaning and precedence of every configuration key |  |
| `risk_model.yaml` | Barra-style risk model settings (plan 05, D-127): styles with CNE5 descriptor weights, half-lives, lags, adjustments, validation | `RiskModelSettings` |
| `base.yaml` | lake root default, Tushare paging/retry settings, download order and start dates, enum key lists, watchlist thresholds | `lake`, `tushare`, `download`, `enum_values`, `watchlist` |
| `etf_proxies.yaml` | national-team ETF proxy: 7 indices (benchmark regex, reference ETF), the 11 core ETFs, start (D-126) | `start`, `recent_days`, `core`, `indices` |
| `manual_series.yaml` | hand-entered public cycle series (Clarksons newbuild index …) with source URLs; licensed exports go in git-ignored `local.manual_series.yaml` (plan 20, D-139) | `series`, `observations` |
| `watchlist.example.yaml` | template for the git-ignored `local.watchlist.yaml`: buy targets for the app's 观察账本 page (D-120) | `entries` |
| `business_models.yaml` | business-model archetypes A1–A12 (formula, drivers, pricing, pass-through, cycle signals, moat types, valuation methods, 68 operating-mode variants) and the SW L3 → archetype default map (D-112; Opus prior, user spot-check) | `archetypes`, `sw_l3` (346) |
| `datasets.yaml` | one entry per dataset: endpoint, sweep, primary key, known-on column, fields, curated layout | 72 datasets |
| `documents.yaml` | document sources for DocumentDownloader: metadata dataset, URL and file templates, doc-type title rules (D-101) | `sources`: cninfo, cninfo_kw, em_industry, em_stock |
| `factors.yaml` | TODO purpose |  |
| `futures_categories.yaml` | TODO purpose |  |
| `material_prices.yaml` | material node → futures contracts for the input-cost and output-price indexes (pricing power P3/P4, D-118) | |
| `sector_kpis.yaml` | sector-specific KPIs per Shenwan industry (D-106): seed from Opus, final tiers from broker reports and filings; format in its header | 31 L1, 105 groups, 728 KPIs |
| `ticker_aliases.yaml` | TODO purpose |  |
