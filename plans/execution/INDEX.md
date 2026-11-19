# plans/execution/

Execution plans, `NN_<slug>.md`, from the `plan` skill template. `ROADMAP.md` is the single status board.

## Files
| File | Purpose | Contains |
|---|---|---|
| `00_model_roles.md` | pin Fable to planning/review and Opus to execution via agent, settings, hook, skill routing | 5 phases, exact config files, risks |
| `01_data_lake.md` | build the lake, Tushare client, pattern fetchers, compaction, PIT views, first charts, research entry | 6 phases, class table with planned callers, risks, log |
| `02_project_catalog.md` | load INDEX tree, registry, decisions, plans, datasets and AST into a `project` schema in the lake DuckDB | 4 phases, 12 tables, views, risks |
| `03_vix_calculation.md` | calculation package with CBOE-method VIX from option data: datasets, building blocks, formulas, pipeline step, iVIX validation | 5 phases, class table, risks |
| `04_factors.md` | read API, statistic tests, universe, six factors, evaluation with significance, feature pipeline, chart, notebook | 6 phases, class table, risks |
| `05_risk_model.md` | Barra-style multi-factor risk model: industry data, descriptors, factor returns, covariance, specific risk, validation | 6 phases, class table, risks |
| `09_positioning_flows.md` | dealer gamma exposure, futures positioning, margin liquidation ladder for the CSI 300; datasets, notebook, event-study validation | 6 phases, class table, risks |
| `10_macro_commodity_sectors.md` | commodity futures, gold, macro and sector data; second source; continuous series; factors and risk descriptors | 5 phases, class table, risks |
| `11_lake_expansion.md` | multi-source data loading and every dataset the research asks need, in nine ordered phases with permission checks and reconciliations | 9 phases, class table, risks |
| `12_industry_chain_graph.md` | evidence-backed A-share industry-chain graph: Opus taxonomy, CNINFO documents, DeepSeek extraction/validation, graph query | 6 phases, class table, risks |
| `13_broker_valuation.md` | broker valuation logic from research reports: method, multiples, target price, comparables, assumptions; per-industry induction | 4 phases, risks |
| `15_chain_web_app.md` | industry-chain web app: React front end, Go read-only API, Python graph export | |
| `16_structural_deduction.md` | opportunity discovery and market-implied deduction: cycle panel, priced-in expectations, screens, deep-dive workflow, replay | |
| `17_peer_groups.md` | peer groups from labeled evidence: pair signals, scoring, held-out evaluation, clustering, wiring into peer comparisons | |
| `18_guidance_tracking.md` | company guidance tracking: preview tracker, acquisition fixes, Ark guidance extraction, outcome matching, credibility | |
| `19_app_store_charts.md` | App Store game charts: daily capture per country, publisher link, per-company rank view | |
| `20_manual_series.md` | Manual and public cycle series (Clarksons newbuild index, TiO2, freight, hog cycle) as PIT rows with sources; feeds position notes, watchlist and morning report | |
| `21_retail_nowcast_screen.md` | Retail-participation (shareholder-count) nowcast and weekly opportunity list | |
| `24_index_trend_position.md` | trend blend + volatility sizing per broad index on the 波动率监测 page, fear × trend context, optional phone line | 3 phases, evidence from research runs, class table, risks, open questions |
| `25_intraday_reversal.md` | intraday high-turnover reversal factor: class, campaign test, score decision | 3 phases, research evidence, class table, risks, open question |
| `26_qdii_premium_alert.md` | QDII ETF premium over NAV in the ETF panel and e-mail, buy-threshold flag | 2 phases, research evidence, class table, risks, open questions |
| `27_etf_cta_book.md` | long-only ETF risk-budget book with A股 / bond timing, weekly weights and paper record | 4 phases, research evidence, class table, risks, open questions |
| `28_temporal_chain_graph.md` | period-keyed chain graph: company leaves, industry nodes, supplier/buyer and finance/invest edges; parquet label store; every document type labelled | 6 phases, class table, risks, open questions |
| `29_capital_gains_overhang.md` | capital gains overhang (CGO) chip model: research match and IC test, then factor class and campaign if it passes | 3 phases, model formulas, class table, risks, open questions |
| `30_smallcap_bottom_watch.md` | daily small-cap bottom watch: panic, index levels, vol gap, broad-ETF flows in the morning e-mail and on #volatility | 3 phases, evidence, class table, risks, open questions |
| `31_sector_monitor.md` | sector monitor tab for 房地产 and 游戏 with game ↔ company links | 5 phases, class table, risks, open questions |
| `32_buyback_monitor.md` | market-wide buyback monitor with Ark LLM labels (purpose, funding, amount, price cap) | 4 phases, class table, risks, open questions |
| `34_bond_monitor.md` | China rates and RMB monitor (国债利率与人民币汇率): curve, spreads, 股债性价比, FX vs majors, fixing, triggers | 4 phases, class table, risks, open questions |
| `35_sector_earnings_top.md` | Sector earnings-season top signal (好消息涨不动): earnings events with SUE and windows, SW L2 signal, app table and e-mail line | 3 phases, class table, risks |
| `36_pricing_gap_factor.md` | Linear-pricing gap factor (线性定价差): consensus panel, factor class, campaign, veto in the app | 4 phases, class table, risks |
| `37_risk_analyst_descriptors.md` | Analyst descriptors (远期 EP, 预期增长) in the risk model with a gate | 3 phases, class table, risks |
| `38_update_all.md` | Update task ledger and `update-all` (任务表与一键更新): ordered steps, failures recorded, dependents skipped, status panel and e-mail line (plan 38) |
| `33_sector_signals.md` | 行业监控 signals: sales yoy, 70-city breadth, game launches, valuation percentile, analyst revisions, surveys | 4 phases, class table, risks, log |
| [`22_phone_alerts.md`](22_phone_alerts.md) | phone alerts by iMessage (plan 22) |
| [`23_buybacks.md`](23_buybacks.md) | buybacks and shareholder yield (plan 23) |
| `ROADMAP.md` | every plan with what it builds, which design it implements, dependencies and status | roadmap table, status vocabulary |
