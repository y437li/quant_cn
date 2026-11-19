"""Glass (FG.ZCE) curve: each listed month's settle now vs 1 week / 1 month ago, calendar spreads, OI by month."""
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

c = Config.load(Path("."))
OUT = Path(c.lake.root) / "meta/runs/research/20261113_glass_curve"
OUT.mkdir(parents=True, exist_ok=True)
cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
q = LakeQuery(cat)
d = q.sql("""
SELECT d.ts_code, d.trade_date, coalesce(d.settle, d.close) AS px, d.oi, d.vol, b.d_month
FROM curated.fut_daily d JOIN curated.fut_basic b USING (ts_code)
WHERE b.fut_code IN ('FG', 'SA') AND b.exchange = 'CZCE' AND d.trade_date >= '20250601'
""")
cat.close()
d["fam"] = d["ts_code"].str[:2]
d = d[d["d_month"] >= d["trade_date"].str[:6]]
days = sorted(d["trade_date"].unique())
last, wk, mo = days[-1], days[-6], days[-22]
pd.set_option("display.width", 200)
for fam in ("FG", "SA"):
    f = d[d["fam"] == fam]
    piv = f.pivot_table(index="d_month", columns="trade_date", values="px")
    oi = f[f["trade_date"] == last].set_index("d_month")["oi"]
    tab = pd.DataFrame({"now": piv[last], "1w_ago": piv[wk], "1m_ago": piv[mo], "oi": oi}).dropna(subset=["now"])
    tab["chg_1w"] = tab["now"] - tab["1w_ago"]
    tab["chg_1m"] = tab["now"] - tab["1m_ago"]
    tab["vs_front"] = tab["now"] - tab["now"].iloc[0]
    tab["vs_front_1m_ago"] = tab["1m_ago"] - tab["1m_ago"].iloc[0]
    print(f"\n{fam}  {last} (1w {wk}, 1m {mo})")
    print(tab.round(1).to_string())
    tab.to_csv(OUT / f"curve_{fam}.csv")
# key spreads over time: FG 2601-2605, 2605-2609, 01-09 (main contracts)
fg = d[d["fam"] == "FG"].pivot_table(index="trade_date", columns="d_month", values="px")
sp = pd.DataFrame({
    "01-05": fg.get("202601") - fg.get("202605"),
    "05-09": fg.get("202605") - fg.get("202609"),
    "01-09": fg.get("202601") - fg.get("202609"),
}).dropna(how="all")
print("\nFG calendar spreads (near minus far; falling = far strengthening)")
print(sp.iloc[-25::3].round(1).to_string())
sp.to_csv(OUT / "fg_spreads.csv")

# corrected calendar spreads for the live contracts (2701 / 2705 / 2709)
sp = pd.DataFrame({
    "2701-2705": fg.get("202701") - fg.get("202705"),
    "2705-2709": fg.get("202705") - fg.get("202709"),
}).dropna()
print("\nFG live calendar spreads (near minus far; falling = far strengthening vs near)")
print(sp.iloc[-45::5].round(1).to_string())
sp.to_csv(OUT / "fg_spreads_live.csv")

# does glass (FG) move 中国巨石 (fiberglass)? weekly returns, 2 years; 旗滨 (float glass) for contrast
cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
q = LakeQuery(cat)
st = q.sql("""
SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS px FROM curated.daily d
JOIN curated.adj_factor a USING (ts_code, trade_date)
WHERE d.ts_code IN ('600176.SH', '601636.SH', '000300.SH') AND d.trade_date >= '20241101'
""")
ix = q.sql("SELECT ts_code, trade_date, close AS px FROM curated.index_daily WHERE ts_code = '000300.SH' AND trade_date >= '20241101'")
fut = q.sql("""
SELECT d.trade_date, b.fut_code, coalesce(d.settle, d.close) AS px, d.oi, d.ts_code
FROM curated.fut_daily d JOIN curated.fut_basic b USING (ts_code)
WHERE b.fut_code IN ('FG', 'SA') AND b.exchange = 'CZCE' AND d.trade_date >= '20241101'
""")
cat.close()
dom = fut.loc[fut.groupby(["fut_code", "trade_date"])["oi"].idxmax()]
# same-contract daily returns chained, so rolls do not jump
fut = fut.sort_values(["ts_code", "trade_date"])
fut["r"] = fut.groupby("ts_code")["px"].pct_change()
dom = dom.merge(fut[["ts_code", "trade_date", "r"]], on=["ts_code", "trade_date"])
rets = dom.pivot_table(index="trade_date", columns="fut_code", values="r")
px = pd.concat([st, ix]).pivot_table(index="trade_date", columns="ts_code", values="px").pct_change()
allr = px.join(rets, how="inner").fillna(0.0)
allr.index = pd.to_datetime(allr.index)
wk = (1 + allr).resample("W-FRI").prod() - 1
print("\nweekly return correlation since 2024-11")
print(wk.corr().round(2).to_string())
ex = wk[["600176.SH", "601636.SH"]].sub(wk["000300.SH"], axis=0)
print("\nexcess vs CSI 300 correlated with FG / SA weekly returns")
print(pd.DataFrame({k: [ex[k].corr(wk["FG"]), ex[k].corr(wk["SA"])] for k in ex}, index=["FG", "SA"]).round(2).to_string())
wk.to_csv(OUT / "weekly_returns.csv")
