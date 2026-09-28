# plans/architecture/

Design documents: what is built and why it is shaped this way. Each names the plans that implement it.

## Files
| File | Purpose | Contains |
|---|---|---|
| `CALCULATION_DESIGN.md` | v1.0 (D-032): calculation package, CBOE VIX method mapped to Tushare option/SHIBOR data, deviations and quality flags, datasets to add, tests | §1–§6; implemented by plan 03 |
| `DATA_LOADING_DESIGN.md` | v1.2: local env config keeping the lake outside the repo, fetcher/pipeline classes and run behaviour, flow monitoring | §1–§5; implemented by plan 01 ph1–4 |
| `FOLDER_STRUCTURE.md` | v1.3: repository tree with indexes, four-zone lake layout, layer rules, first classes per package | §1–§6; implemented by plan 01 |
| `SRC_DESIGN.md` | v1.2 (D-020, D-028, D-032, D-041): data flow, classes per package, shared frames, cross-cutting rules, plan roadmap | §1–§6; implemented by plans 01, 03–06 |
