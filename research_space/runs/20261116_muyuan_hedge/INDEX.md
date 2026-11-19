# 20261116_muyuan_hedge

Question: 查一下牧原的套期保值公告，如果升水的话价格，市值大概要修复多少 / 豆粕受化肥影响，有粮食缺口还是贴水吗.

Sources read by hand: CNINFO 牧原 announcements 2025-12-10 关于开展商品期货套期保值业务的公告 (margin cap 8亿, 2026-01-01..12-31, corn / soymeal / hogs, OTC allowed) and the monthly 销售简报 2025-12..2026-11.

Run from the repo root: `uv run --env-file .env python research_space/runs/20261116_muyuan_hedge/hog_scenarios.py`. Output: `<lake>/meta/runs/research/20261116_muyuan_hedge/scenarios.csv`.

| File | Purpose |
|---|---|
| `hog_scenarios.py` | implied all-in cost per kg (Q2/Q3 2026), 2027 profit under the LH curve and alternative prices, value at 13x / 15x, hog price implied by the current market cap |
