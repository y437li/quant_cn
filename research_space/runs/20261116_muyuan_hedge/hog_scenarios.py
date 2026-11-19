"""牧原 2027 profit and implied value under hog price paths (futures curve vs alternatives).

Inputs: monthly sales briefs (CNINFO 2026-08..11-06: heads, revenue, price), Q2/Q3 2026 attributable
profit from the lake, LH settles on 2026-11-16. Output: implied cost per kg, scenario profit, and the
hog price the current market cap implies at a given PE. Writes scenarios.csv to the lake run folder.
"""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261116_muyuan_hedge"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True)
# sales briefs (万头, 亿元, 元/kg) — 2026 monthly table in the 2026-11-06 brief
brief = pd.DataFrame({"m": range(1, 11),
    "heads": [700.9, 460.3, 675.1, 714.3, 688.3, 622.7, 666.1, 703.0, 642.3, 591.3],
    "rev": [105.66, 64.05, 86.06, 85.03, 85.65, 75.00, 88.97, 92.54, 85.20, 72.53]})
np_q = c.execute("""SELECT end_date, arg_max(n_income_attr_p, ann_date)/1e8 np FROM curated.income_vip
  WHERE ts_code='002714.SZ' AND report_type='1' AND end_date IN ('20260331','20260630','20260930') GROUP BY 1 ORDER BY 1""").df()
np_q["q"] = np_q.np - np_q.np.shift().fillna(0)
rows = []
for q, ms, npq in [("Q2", [4, 5, 6], np_q.q.iloc[1]), ("Q3", [7, 8, 9], np_q.q.iloc[2])]:
    b = brief[brief.m.isin(ms)]
    rows.append((q, b.heads.sum(), b.rev.sum(), npq))
cost = []
for q, heads, rev, npq in rows:
    w = 126.0  # kg per head (rev / (price * heads) ≈ 125–127 in the briefs)
    kg = heads * 1e4 * w
    price = rev * 1e8 / kg
    cost.append(price - npq * 1e8 / kg)
    print(f"{q}: heads {heads:.0f}万, avg {price:.2f}元/kg, attrib. profit {npq:.1f}亿 -> all-in cost {cost[-1]:.2f}元/kg")
COST = round(sum(cost) / len(cost), 1)
lh = c.execute("SELECT ts_code, settle/1000 p FROM curated.fut_daily WHERE trade_date='20261116' AND regexp_matches(ts_code,'^LH27')").df().set_index("ts_code").p
curve = [(lh["LH2701.DCE"] + lh["LH2703.DCE"]) / 2, lh["LH2705.DCE"], (lh["LH2707.DCE"] + lh["LH2709.DCE"]) / 2, lh["LH2709.DCE"]]
mv = c.execute("SELECT total_mv/1e4 FROM curated.daily_basic WHERE ts_code='002714.SZ' AND trade_date='20261116'").fetchone()[0]
KG = 7500e4 * 126 / 1e8  # 亿 kg in 2027 (7,500万头 × 126 kg)
scen = {"期货曲线": sum(curve) / 4, "期货下半年年化": (curve[2] + curve[3]) / 2, "偏弱(10.5)": 10.5, "偏强(13.5)": 13.5, "强(15)": 15.0}
res = pd.DataFrame([{"scenario": k, "price": round(p, 2), "cost": COST, "profit_yi": round((p - COST) * KG)} for k, p in scen.items()])
for pe in (13, 15):
    res[f"mv_at_{pe}x"] = (res.profit_yi.clip(lower=0) * pe).round()
res["mv_now"] = round(mv)
for pe in (13, 15):
    print(f"price implied by mv {mv:.0f}亿 at {pe}x: {COST + mv / pe / KG:.2f}元/kg")
res.to_csv(OUT / "scenarios.csv", index=False)
print("curve quarters:", [round(x, 2) for x in curve]); print(res.to_string(index=False))
