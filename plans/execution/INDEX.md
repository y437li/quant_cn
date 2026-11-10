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
| `16_structural_deduction.md` | structural deduction pipeline: four-dimension industry metrics, structure labels, price transmission, scenarios, replay | |
| `ROADMAP.md` | every plan with what it builds, which design it implements, dependencies and status | roadmap table, status vocabulary |
