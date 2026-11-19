# 20261115_clean_chips

Question: 我想看看个股那些筹码比较干净 (2026-11-15). Screen as of the latest lake date (2026-11-13), float cap ≥ 50亿, non-ST.

| File | Purpose |
|---|---|
| `clean_chips_screen.py` | six conditions (Q3 holders ≤ −5%, RetailGauge decile ≤ 3, 70% cost band in bottom 30%, band narrowing over 60d, 20d large+extra-large net inflow, cost95/price ≤ 20%); strict A/B shapes and a ≥5-of-6 list → `meta/runs/research/20261115_clean_chips/` |
| `gauge_clean.py` | RetailGauge standard: Q4 decile 0–1, Q3 ≤ −5%, Q2 also down → `gauge_clean_20261113.csv` |
| `gauge_top50_outflow.py` | top 50 lowest RetailGauge percentile (cap ≥ 50亿, non-ST) with chips, flows, PE, yield |
| `chip_top50.py` | composite chip score (holders Q2 / Q3, gauge, band, band change, overhead) → top 50 |
| `dispersed_low_gauge.py` | 2026-11-13 screen: dispersed chips (band top third) + gauge ≤ 0.3 + turnover floor, with valuation |
| `two_profiles.py` | quick profiles of 一拖股份 and 思特威: business, segment mix, growth, valuation, consensus |
