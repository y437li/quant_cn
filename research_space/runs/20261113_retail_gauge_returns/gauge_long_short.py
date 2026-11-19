"""Long/short portfolios on the RetailGauge decile, quarterly: built at the quarter-end close signal, entry
open(d+1), exit close(d+60) (~one quarter, little overlap). Equal weight. Legs: long D1-4, long D1, short D10,
and long D1-4 hedged with an index (CSI 500 / CSI 1000) over the same open->close window."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root); OUT = LAKE / "meta/runs/research/20261113_retail_gauge_returns"
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
H, COST = 60, 0.003   # 0.3% per side per full turnover (commission + stamp + slippage, rough)
G = pd.read_parquet(OUT / "gauge_walkforward.parquet"); G = G[G.q != "20261112"]
con = duckdb.connect()
px = con.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c, b.circ_mv
  from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date)
  left join {r('curated/daily_basic')} b using (ts_code, trade_date) where d.trade_date >= '20211201'""").df()
P = lambda v: px.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
O, C, CM = P("o"), P("c"), P("circ_mv"); idx = C.index
FWD = C.shift(-H) / O.shift(-1) - 1
ix = con.sql(f"""select ts_code, trade_date, open, close from {r('curated/index_global')} where 1=0""").df() if False else None
ix = con.sql(f"""select ts_code, trade_date, open, close from read_parquet('{LAKE}/raw/index_daily/**/*.parquet', hive_partitioning=true, union_by_name=true)
  where ts_code in ('000905.SH','000852.SH','000300.SH') and trade_date >= '20211201'""").df().drop_duplicates(["ts_code", "trade_date"])
IO = ix.pivot(index="trade_date", columns="ts_code", values="open").reindex(idx)
IC_ = ix.pivot(index="trade_date", columns="ts_code", values="close").reindex(idx)
IFWD = IC_.shift(-H) / IO.shift(-1) - 1
rows = []
for uni in ("all", "cap50"):
    for q, g in G.groupby("q"):
        d = idx[idx <= q][-1]
        f = g.set_index("ts_code")[["gauge"]].join(pd.DataFrame({"cmv": CM.loc[d], "ret": FWD.loc[d]}), how="inner").dropna()
        if uni == "cap50": f = f[f.cmv >= 50e4]
        if len(f) < 100: continue
        f["dec"] = pd.qcut(f.gauge.rank(method="first"), 10, labels=range(1, 11)).astype(int)
        m = lambda s: f.ret[s].mean()
        rows.append({"uni": uni, "q": q, "n": len(f), "mkt_ew": f.ret.mean(), "D1_4": m(f.dec <= 4), "D1": m(f.dec == 1),
                     "D10": m(f.dec == 10), "csi500": IFWD.loc[d, "000905.SH"], "csi1000": IFWD.loc[d, "000852.SH"], "csi300": IFWD.loc[d, "000300.SH"]})
R = pd.DataFrame(rows)
R["LS D1_4-D10"] = R.D1_4 - R.D10; R["LS D1-D10"] = R.D1 - R.D10
R["D1_4 - mkt_ew"] = R.D1_4 - R.mkt_ew; R["mkt_ew - D10 (avoid)"] = R.mkt_ew - R.D10
R["D1_4 hedged csi500"] = R.D1_4 - R.csi500; R["D1_4 hedged csi1000"] = R.D1_4 - R.csi1000
R.to_csv(OUT / "gauge_long_short_quarters.csv", index=False)
cols = ["D1_4", "D1", "D10", "mkt_ew", "LS D1_4-D10", "LS D1-D10", "D1_4 - mkt_ew", "mkt_ew - D10 (avoid)", "D1_4 hedged csi500", "D1_4 hedged csi1000"]
pd.set_option("display.width", 250)
for uni, g in R.groupby("uni", sort=False):
    s = pd.DataFrame({"mean %/qtr": g[cols].mean() * 100, "median %": g[cols].median() * 100,
                      "t": g[cols].mean() / g[cols].std() * np.sqrt(len(g)), "win qtrs": (g[cols] > 0).sum().astype(str) + f"/{len(g)}",
                      "worst %": g[cols].min() * 100,
                      "ann % (4 qtrs)": ((1 + g[cols]).prod() ** (4 / len(g)) - 1) * 100,
                      "Sharpe (ann)": g[cols].mean() / g[cols].std() * 2})
    print(f"\n== {uni}: {len(g)} quarters, {g.n.mean():.0f} stocks; returns over 60 sessions, before costs (two-sided LS round trip ≈ {4*COST*100:.1f}%/qtr if fully turned over)")
    print(s.round(2).to_string())
    print("by quarter LS D1_4-D10 %:", " ".join(f"{q[2:6]}:{v*100:+.1f}" for q, v in zip(g.q, g["LS D1_4-D10"])))
# turnover of the D10 / D1-4 lists between quarters (share of names that stay)
for uni in ("all",):
    keep = []
    qs = sorted(G.q.unique())
    for a, b in zip(qs, qs[1:]):
        ga, gb = G[G.q == a], G[G.q == b]
        ta = set(ga.ts_code[ga.gauge >= 0.9]); tb = set(gb.ts_code[gb.gauge >= 0.9])
        la = set(ga.ts_code[ga.gauge <= 0.4]); lb = set(gb.ts_code[gb.gauge <= 0.4])
        keep.append((len(ta & tb) / len(ta), len(la & lb) / len(la)))
    k = np.array(keep).mean(axis=0); print(f"\nnames kept quarter to quarter: D10 {k[0]:.0%}, D1-4 {k[1]:.0%}")
