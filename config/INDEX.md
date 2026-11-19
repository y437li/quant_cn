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
| `label_sources.yaml` | label files imported into derived/labels: set, path, period, key / date fields, anchor set, taxonomy version (plan 28, D-161) | `sources` |
| `manual_series.yaml` | hand-entered public cycle series (Clarksons newbuild index …) with source URLs; licensed exports go in git-ignored `local.manual_series.yaml` (plan 20, D-139) | `series`, `observations` |
| `update_all.yaml` | update-all (plan 38, D-181): the daily update steps in order with make targets, needs, output JSON for `as_of`, timeouts and retries |  |
| `watchlist.example.yaml` | template for the git-ignored `local.watchlist.yaml`: buy targets for the app's 观察账本 page (D-120) | `entries` |
| `business_models.yaml` | business-model archetypes A1–A12 (formula, drivers, pricing, pass-through, cycle signals, moat types, valuation methods, 68 operating-mode variants) and the SW L3 → archetype default map (D-112; Opus prior, user spot-check) | `archetypes`, `sw_l3` (346) |
| `datasets.yaml` | one entry per dataset: endpoint, sweep, primary key, known-on column, fields, curated layout | 72 datasets |
| `documents.yaml` | document sources for DocumentDownloader: metadata dataset, URL and file templates, doc-type title rules (D-101) | `sources`: cninfo, cninfo_kw, em_industry, em_stock |
| `factors.yaml` | TODO purpose |  |
| `futures_monitor.yaml` | 期货监测: 73 commodity families by group, 8 value-chain spreads + 金银比, 金油比 and 铜金比 (legs and coefficients), OI floor and flag bounds (plan 15 ph7i, D-145) |  |
| `volatility_monitor.yaml` | 波动率监测: US VIX (CBOE) and A-share VIX lines (50 / 300 / 500 / 1000 / 科创50 option families), percentile window and alerts (plan 03 ph6, D-152) |  |
| `rates_fx_monitor.yaml` | 利率与汇率 (plan 34, D-171): lines (中债 curve points, spreads, 股债性价比, FX vs majors, SAFE fixing, 中美利差), units, percentile window and alerts |  |
| `sector_earnings_signal.yaml` | 财报季信号 (plan 35, D-172): SUE window, best-surprise decile, windows (pre 60, reaction 1, back 120, fwd 60 / 120), report share, thresholds pre 15% / reaction 1% / rally 20% | |
| `retail_gauge.yaml` | 散户温度计 RetailGauge (plan 21; D-142, D-155, D-167): v5 feature windows, LightGBM params, label clip, avoid 0.9 / leaving 0.3 / inflow 0.8, 3 checkpoints 3 sessions apart, retrain months 5 / 9 / 11 |
| `discovery_rules.yaml` | idea / opportunity rules: section `opportunity` = plan 21 ph4 daily list (cap ≥ 50亿, retail leaving, 3 of 4 inflow weeks, profit YoY ≥ 20% with QoQ ≥ 0, pb below its 5-year median, style fit at 5%; top 10 + 5 near-misses); plan 16 ph3 adds its screens |
| `smallcap_watch.yaml` | 小盘观察 (plan 30): indices, panic / breadth / vol / gap triggers, near rules, windows and broad ETFs; personal 中证1000 levels in the git-ignored `local.smallcap_watch.yaml` |  |
| `app_publishers.yaml` | App Store seller account (artist_id) → company and listed code (plan 19 ph2, D-137 u1) | publishers |
| `sector_monitors.yaml` | 行业监控 (plan 31): 70-city tier lists, realised-vol windows, chart lengths, sectors (房地产, 游戏) with companies and chart metrics | tiers, sectors |
| `notify.example.yaml` | template for git-ignored `local.notify.yaml`: iMessage recipients of phone alerts, triggers, max lines (plan 22, D-153) |  |
| `futures_categories.yaml` | TODO purpose |  |
| `material_prices.yaml` | material node → futures contracts for the input-cost and output-price indexes (pricing power P3/P4, D-118) | |
| `sector_kpis.yaml` | sector-specific KPIs per Shenwan industry (D-106): seed from Opus, final tiers from broker reports and filings; format in its header | 31 L1, 105 groups, 728 KPIs |
| `ticker_aliases.yaml` | TODO purpose |  |
| `mail.example.yaml` | template for the git-ignored `local.mail.yaml`: sender, recipients and the env variable holding the SMTP app password (plan 15 ph7e) | `host`, `port`, `sender`, `recipients`, `password_env` |
| `etf_cta.yaml` | ETF CTA book (plan 27, D-160): 股票 / 黄金 / 商品 groups at equal risk (60%), 5y + 30y bonds with switch (40%), A股 trend timing, weekly decisions, 2-point band, premium guard; view subsets and `views_file` (git-ignored `local.etf_cta_views.yaml`, D-163) | `EtfCtaSettings` |
