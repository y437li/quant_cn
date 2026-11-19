# 20261115_retail_gauge_q4_table

Per-company 2026-12-31 shareholder-count forecast from RetailGauge v5 (as-of 2026-11-12 nowcast, `meta/runs/holder_nowcast/holders_forecast_q4.parquet`), with names, industry, decile, Q3 count, forecast count and IQR range, holdings flagged.

| File | Purpose |
|---|---|
| `export_table.py` | joins the v5 forecast with stock_basic and positions → `meta/runs/research/20261115_retail_gauge_q4_table/retail_gauge_q4_20261231.csv` |
