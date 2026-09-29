# 10 — Commodity, macro and sector data

| | |
|---|---|
| Status | drafted, awaiting approval |
| Owner | user (approve) / executor (build) |
| Created | 2026-09-28 |
| Notion | pending |
| Decisions | D-062 |
| Depends on plans | 03 (calculation base), 09 ph1 (`fut_daily`/`fut_basic`/`fut_holding` config), 05 ph1 (Shenwan classification) for sectors |

## Goal
Roll-adjusted commodity series (oil, gold, metals, agriculturals), daily macro series (rates, FX, monthly
releases PIT-aligned) and sector index panels in the lake, usable by the risk model as macro-sensitivity
factors, by the factor library as spillover and regime variables, and by pairs/positioning research.

## Scope
- In: datasets of MACRO_COMMODITY_DESIGN §1 (small initial product set, §6 Q3), a second data source client (FRED; AkShare only where FRED lacks), `ContinuousFutures`, `TermStructure`, `MacroSeries`, `SectorIndexPanel`, four frames, commodity-links config, `OilBeta`/`GoldBeta`/`MetalsBeta`/`RatesBeta`/`CnyBeta` descriptors for the risk model (gated), sector momentum factor, a notebook.
- Out: intraday commodities, options on commodities, full CNE6 v3 (separate plan), trading strategies on commodities.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Tushare datasets (delivered by plan 11 ph4–5; this phase = verification only) | `fut_basic`/`fut_daily`/`fut_holding` extended to INE/SHFE/DCE/CZCE, `fut_mapping`, `sge_daily`, `yc_cb`, `fx_daily`, `shibor_lpr`, `cn_cpi`/`cn_ppi`/`cn_pmi`/`cn_m` with `release_lag_days`; `sw_daily` tier check with member-computed fallback | live pulls 2019+ for the small product set; every product has a main-contract mapping every session; macro `known_on` = release date | 09 ph1 | todo |
| 2 | Second source (delivered by plan 11 ph6; this phase = verification only) | `DatasetSpec.source`, `FredClient` (`BaseApiClient`), FRED series Brent, WTI, gold (LBMA), DGS10, DXY; `AkShareClient` only if LME copper is required; raw copies kept | fetch + curate for 2019+; next-China-session visibility rule tested | 1 | todo |
| 3 | Derived series | `ContinuousFutures` (ratio back-adjust, roll log), `TermStructure`, `MacroSeries`, `SectorIndexPanel`; frames; `CalculationStep` entries | continuous series has no roll jumps (test on a synthetic roll); term structure sign matches manual check; monthly macro not visible before release date (PIT test) | 1, 2 | todo |
| 4 | Uses | `config/commodity_links.yaml`; `factor.library.CommoditySpilloverFactor`, `SectorMomentumFactor`; risk descriptors `OilBeta`…`CnyBeta` in `DescriptorBuilder` behind a config flag; regime variables exported | factors evaluated per FACTOR_TESTING_DESIGN §6; risk descriptors reported with ΔR² and bias stats (gate per D-061 v3) | 3, 04 ph5, 05 ph5 | todo |
| 5 | Notebook | `YYYYMMDD_commodities_macro_sectors.ipynb`: continuous series, term structures, macro panel, sector heatmap, betas by industry; outputs committed | runs top to bottom | 3, 4 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `FredClient`, (`AkShareClient`) | new (`BaseApiClient`) | data_loading | 2 | fetchers via `FetcherFactory` (source-aware) |
| `ContinuousFutures`, `TermStructure`, `MacroSeries`, `SectorIndexPanel` | new (`BaseCalculation`) | calculation | 3 | `CalculationStep`, factors, risk descriptors, pairs research, `FuturesPositioning` |
| `CONTINUOUS_PANEL`, `MACRO_PANEL`, `TERM_STRUCTURE`, `SECTOR_PANEL`, `COMMODITY_LINKS` | new schemas | core.frames | 3 | producers/consumers above |
| `CommoditySpilloverFactor`, `SectorMomentumFactor` | new (`BaseFactor`) | factor.library | 4 | `FeaturePipeline`, `FactorEvaluator` |
| `DescriptorBuilder` (macro betas) | extend | risk | 4 | `RiskModel` (gated) |

## Risks
- Second-source fragility (AkShare scraping) and licence terms: prefer FRED; keep raw copies; document provenance in `external/` if files are placed by hand.
- Main-contract mapping gaps around holidays and new products: `ContinuousFutures` must refuse silent gaps.
- Monthly macro release dates are not in Tushare: the lag rule is an approximation; flag it in `known_on` and keep the official calendar as a manual table where available.
- `sw_daily` tier may be unavailable: fallback computes Shenwan index returns from members (cap-weighted), which differ from the published index slightly.

## Open questions
See MACRO_COMMODITY_DESIGN §6 (second source, adjustment method, initial product set, `sw_daily` tier).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-28 | — | Drafted from user request: add oil, gold and other commodity prices, and sectors |
