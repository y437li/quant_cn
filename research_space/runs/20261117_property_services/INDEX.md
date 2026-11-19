# 20261117_property_services

Question: 物业相关的呢？ (after 20261117_real_estate).

Run from the repo root: `uv run --env-file .env python research_space/runs/20261117_property_services/company_panel.py`. Outputs: `<lake>/meta/runs/research/20261117_property_services/`. Hong Kong-listed managers (碧桂园服务, 华润万象生活, 中海物业, 保利物业, 万物云) are not in the lake and are not covered.

| File | Purpose |
|---|---|
| `company_panel.py` | 招商积余, 我爱我家, 世联行, 特发服务, 新大正, 南都物业, 中天服务: single-quarter profit and gross margin, valuation, consensus, dividend, returns, RetailGauge, holder change, winner rate (same code as the real-estate panel) |
| `cmsk_pair.py` | 招商蛇口 vs 招商积余 (question: 招商蛇口和招商积余): balance sheet, cash flow, impairment, parent stake, dividends |
