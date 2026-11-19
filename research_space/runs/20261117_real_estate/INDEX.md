# 20261117_real_estate

Question: 房地产呢？ (2026-11-17 China date, after the cycle screen and the polyester deep dive).

Run from the repo root: `uv run --env-file .env python research_space/runs/20261117_real_estate/company_panel.py`. Outputs: `<lake>/meta/runs/research/20261117_real_estate/`. The L3 cycle rows come from `research_space/runs/20261116_cycle_screen/cycle_screen.py`. Housing prices: NBS 70-city release for October 2026 (read on the web, 2026-11-16).

| File | Purpose |
|---|---|
| `company_panel.py` | 保利, 招商蛇口, 万科, 滨江, 金地, 新城, 海螺水泥, 东方雨虹, 欧派, 格力: single-quarter profit and gross margin 2024Q1–2026Q3, PE / 2027E PE, consensus 3m revision, PB percentile, debt, returns, RetailGauge, holders, winner rate (same code as the polyester panel with a different name list) |
