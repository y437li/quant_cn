# 20261117_more_sectors

Question: 还有什么行业吗？ (after polyester, real estate, property services, titanium).

Run from the repo root: `uv run --env-file .env python research_space/runs/20261117_more_sectors/<file>.py`. Outputs: `<lake>/meta/runs/research/20261117_more_sectors/`. `rank_l3.py` needs `20261116_cycle_screen/cycle_screen.py` to have run.

| File | Purpose |
|---|---|
| `rank_l3.py` | rank L3 industries: cheap with profit near peak, and cheap-ish with profit turning up |
| `company_panel.py` | 顺丰, 圆通, 申通, 韵达, 万华, 山西焦煤, 潞安, 淮北, 中海油服, 海油工程, 杰瑞: quarterly profit and margin, valuation, consensus, chips |
| `oil_beta.py` | daily partial beta on INE crude (CSI 300 controlled, 1y) for the candidates: 万华化学涨过了吧 / 都是跟石油相关的 |
