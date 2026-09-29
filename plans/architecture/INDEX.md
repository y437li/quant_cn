# plans/architecture/

Design documents: what is built and why it is shaped this way. Each names the plans that implement it.

## Files
| File | Purpose | Contains |
|---|---|---|
| `CALCULATION_DESIGN.md` | v1.1 (D-032, D-046–D-052): calculation package, CBOE VIX method mapped to Tushare option/SHIBOR data, deviations and quality flags, datasets to add, tests | §1–§6; implemented by plan 03 |
| `DATA_LOADING_DESIGN.md` | v2.0 (§3c multi-source expansion, D-063): local env config keeping the lake outside the repo, fetcher/pipeline classes and run behaviour, flow monitoring | §1–§5; implemented by plan 01 ph1–4 |
| `ETF_PAIRS_DESIGN.md` | v1.0 (D-056): long/short ETF pairs research track: shortable legs in A-shares, pair families, cointegration method, costs, datasets, promotion criteria | §1–§7 |
| `FACTOR_LIBRARY.md` | v0.4 (D-055 proposed): catalogue of value, quality, growth, analyst-revision, momentum/reversal, risk-style factors with construction, data mapping, evaluation protocol, first-six selection | §1–§9; input to plan 04 |
| `FACTOR_TESTING_DESIGN.md` | v1.0 (D-060): binding formulas (§10) and end-to-end point-in-time control (§11); IC/ICIR estimands; single-factor tests (Newey-West t, block bootstrap, Pesaran-Timmermann, breaks, decay); multiple-testing (Holm, BHY, Romano-Wolf, HLZ hurdle, White/Hansen SPA, Harvey-Liu); backtest tests (PSR/DSR, CSCV PBO, Ledoit-Wolf); classes; acceptance bar | §1–§9; implemented in plan 04 |
| `FOLDER_STRUCTURE.md` | v1.4: repository tree with indexes, four-zone lake layout, layer rules, first classes per package | §1–§6; implemented by plan 01 |
| `MACRO_COMMODITY_DESIGN.md` | v0.1 (D-062 proposed): commodity, macro and sector datasets (Tushare + FRED), continuous futures and term structure, macro PIT rules, uses in risk model, factor library, pairs and positioning | §1–§6; implemented by plan 10 |
| `POSITIONING_FLOWS_DESIGN.md` | v1.0 (D-057–D-059): GEX and gamma flip, futures positioning regimes and basis, FIFO margin vintages and liquidation ladder; assumptions, frames, datasets, validation | §1–§6; implemented by plan 09 |
| `RISK_FACTOR_LIST.md` | v0.2 (D-061 proposed, §4b per D-062): CNE5 10 factors / 21 descriptors with published weights, CNE6 9 groups / ~46 descriptors, USE4 cross-reference, Tushare mapping, v1/v2/v3 sets for plan 05, data additions | §1–§5 |
| `RISK_MODEL_DESIGN.md` | v1.1 (D-045, D-061): CNE5-style model for A-shares, package classes, descriptor data mapping, six risk frames, datasets to add, tests | §1–§7; implemented by plan 05 |
| `SRC_DESIGN.md` | v1.3 (D-020, D-028, D-032, D-041, D-045): data flow, classes per package, shared frames, cross-cutting rules, plan roadmap | §1–§6; implemented by plans 01, 03–06 |
