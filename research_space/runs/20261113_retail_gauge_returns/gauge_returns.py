"""Does the RetailGauge prediction (known at the quarter-end close) predict returns, compared with what is
actually knowable then (last announced holder change, `prev`) and with the realised change (`y`, look-ahead,
announced 30-50 days later: an upper bound only)?  Entry open(d+1), exit close(d+H), excess vs cross-section."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root); OUT = LAKE / "meta/runs/research/20261113_retail_gauge_returns"
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
G = pd.read_parquet(OUT / "gauge_walkforward.parquet"); G = G[G.q != "20261112"]
con = duckdb.connect()
px = con.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c, b.circ_mv
  from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date)
  left join {r('curated/daily_basic')} b using (ts_code, trade_date) where d.trade_date >= '20211201'""").df()
P = lambda v: px.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
O, C, CM = P("o"), P("c"), P("circ_mv"); idx, cols = C.index, C.columns
HS = (20, 40, 60)
FWD = {h: C.shift(-h) / O.shift(-1) - 1 for h in HS}
ex = con.sql(f"""select trade_date, ts_code, factor, value from {r('derived/features')} where trade_date >= '20211201'
  and factor in ('reversal_1m','turnover_60d','momentum_12_1')""").df()
EX = {f: g.pivot(index="trade_date", columns="ts_code", values="value").reindex(index=idx, columns=cols) for f, g in ex.groupby("factor")}
EX["size"] = np.log(CM)
rows = []
for q, g in G.groupby("q"):
    d = idx[idx <= q][-1]
    f = g.set_index("ts_code")[["gauge", "prev", "y", "ann_y"]].join(pd.DataFrame(
        {"cmv": CM.loc[d], **{f"f{h}": FWD[h].loc[d] for h in HS}, **{k: v.loc[d] for k, v in EX.items()}}), how="inner")
    f = f[f.cmv.notna() & f.f20.notna()]
    for h in HS: f[f"x{h}"] = f[f"f{h}"] - f[f"f{h}"].mean()
    f["q"] = q; f["d"] = d; rows.append(f.reset_index())
E = pd.concat(rows)
lag = (pd.to_datetime(E.ann_y) - pd.to_datetime(E.d)).dt.days
print(f"quarters {E.q.nunique()}  stocks/quarter {len(E)/E.q.nunique():.0f}  announcement lag after signal date: median {lag.median():.0f} days, p25 {lag.quantile(.25):.0f}, p75 {lag.quantile(.75):.0f}")

def ic(g: pd.DataFrame, x: str, y: str, ctrl: list[str]) -> float:
    g = g.dropna(subset=[x, y] + ctrl)
    v = g[x].rank()
    if ctrl:
        Z = g[ctrl].rank(); Z = (Z - Z.mean()) / Z.std(); Z["c"] = 1.0
        v = v - Z.values @ np.linalg.lstsq(Z.values, v.values, rcond=None)[0]
    return pd.Series(v.values).corr(g[y].rank().reset_index(drop=True))

CTRL = list(EX)
specs = [("gauge (prediction)", "gauge", []), ("gauge net of controls", "gauge", CTRL),
         ("gauge net of controls + prev", "gauge", CTRL + ["prev"]),
         ("prev (last announced, known)", "prev", []), ("prev net of controls", "prev", CTRL),
         ("realised y (look-ahead)", "y", []), ("realised y net of controls", "y", CTRL)]
res = []
for uni, m in [("all", E.cmv > 0), ("float cap >= 50亿", E.cmv >= 50e4)]:
    for label, x, ctrl in specs:
        for h in HS:
            s = E[m].groupby("q").apply(lambda g: ic(g, x, f"x{h}", ctrl), include_groups=False).dropna()
            res.append({"universe": uni, "signal": label, "H": h, "IC": round(s.mean(), 4),
                        "t": round(s.mean() / s.std() * np.sqrt(len(s)), 2), "IC<0 qtrs": f"{(s < 0).sum()}/{len(s)}"})
res = pd.DataFrame(res); res.to_csv(OUT / "gauge_ic.csv", index=False)
pd.set_option("display.width", 220)
w = res.pivot_table(index=["universe", "signal"], columns="H", values=["IC", "t"], aggfunc="first", sort=False)
print(w.to_string())
for uni, m in [("all", E.cmv > 0), ("float cap >= 50亿", E.cmv >= 50e4)]:
    e = E[m].copy(); e["dec"] = e.groupby("q").gauge.transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=range(1, 11)))
    t = e.groupby("dec", observed=True)[[f"x{h}" for h in HS]].mean() * 100
    t["hit60"] = e.groupby("dec", observed=True).x60.apply(lambda s: (s > 0).mean())
    t["top-bottom by qtr x60 >0"] = ""
    sp = e[e.dec == 10].groupby("q").x60.mean() - e[e.dec == 1].groupby("q").x60.mean()
    print(f"\n{uni}: gauge decile (10 = most retail inflow predicted), excess %  | D10-D1 x60 mean {sp.mean()*100:.2f}% t {sp.mean()/sp.std()*np.sqrt(len(sp)):.2f}, negative in {(sp<0).sum()}/{len(sp)} qtrs")
    print(t.drop(columns="top-bottom by qtr x60 >0").round(3).to_string())
    t.to_csv(OUT / f"gauge_deciles_{'all' if uni=='all' else 'cap50'}.csv")
