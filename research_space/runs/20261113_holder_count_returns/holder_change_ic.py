"""Does the change in shareholder count (散户人数) predict returns?  Point-in-time:
at each month-end d, use the latest holder count announced by d (ann_date <= d, announced within 90 days)
and the count of the previous period end; chg = latest / previous - 1.  Forward return enters at the
open of d+1 and exits at the close of d+H.  Rank IC raw and net of size / reversal / turnover / momentum."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
OUT = LAKE / "meta/runs/research/20261113_holder_count_returns"; OUT.mkdir(parents=True, exist_ok=True)
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
con = duckdb.connect()
px = con.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c, b.circ_mv
  from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date)
  left join {r('curated/daily_basic')} b using (ts_code, trade_date) where d.trade_date >= '20181001'""").df()
P = lambda v: px.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
O, C, CM = P("o"), P("c"), P("circ_mv"); idx, cols = C.index, C.columns
FWD = {h: C.shift(-h) / O.shift(-1) - 1 for h in (20, 60, 120)}
PAST = C / C.shift(60) - 1   # same-window price move, for the 2x2
ex = con.sql(f"""select trade_date, ts_code, factor, value from {r('derived/features')}
  where factor in ('reversal_1m','turnover_60d','momentum_12_1')""").df()
EX = {f: g.pivot(index="trade_date", columns="ts_code", values="value").reindex(index=idx, columns=cols) for f, g in ex.groupby("factor")}
EX["size"] = np.log(CM)
hn = con.sql(f"""select ts_code, end_date, min(ann_date) ann, arg_min(holder_num, ann_date) n
  from {r('curated/events/stk_holdernumber')} where ann_date is not null and holder_num > 0 group by 1, 2""").df()
hn = hn.sort_values(["ts_code", "end_date"])
hn["prev"] = hn.groupby("ts_code").n.shift(1); hn["prev_end"] = hn.groupby("ts_code").end_date.shift(1)
gap = (pd.to_datetime(hn.end_date) - pd.to_datetime(hn.prev_end)).dt.days
hn = hn[(gap >= 60) & (gap <= 130)].copy()               # one quarter apart
hn["chg"] = hn.n / hn.prev - 1
months = pd.Series(idx, index=idx).groupby(idx.str[:6]).last()
months = [d for d in months if "20190601" <= d <= "20260930"]
rows = []
for d in months:
    a = hn[(hn.ann <= d) & (pd.to_datetime(hn.ann) >= pd.to_datetime(d) - pd.Timedelta(days=90))]
    a = a.sort_values("ann").groupby("ts_code").last()
    f = pd.DataFrame({"chg": a.chg}).join(pd.DataFrame({"cmv": CM.loc[d], "past": PAST.loc[d],
        **{f"f{h}": FWD[h].loc[d] for h in FWD}, **{k: v.loc[d] for k, v in EX.items()}}), how="inner")
    f["date"] = d; rows.append(f.reset_index())
E = pd.concat(rows).rename(columns={"index": "ts_code"})
E = E[E.chg.between(-0.8, 3)]
for h in (20, 60, 120):
    E[f"x{h}"] = E[f"f{h}"] - E.groupby("date")[f"f{h}"].transform("mean")

def ic(g: pd.DataFrame, y: str, resid: bool) -> float:
    g = g.dropna(subset=["chg", y] + (list(EX) if resid else []))
    if len(g) < 100: return np.nan
    x = g.chg.rank()
    if resid:
        Z = g[list(EX)].rank(); Z = (Z - Z.mean()) / Z.std(); Z["c"] = 1.0
        x = x - Z.values @ np.linalg.lstsq(Z.values, x.values, rcond=None)[0]
    return pd.Series(x.values).corr(g[y].rank().reset_index(drop=True))

def summary(sub: pd.DataFrame, label: str) -> list[dict]:
    out = []
    for h in (20, 60, 120):
        for resid in (False, True):
            s = sub.groupby("date").apply(lambda g: ic(g, f"x{h}", resid), include_groups=False).dropna()
            n_eff = len(s) * 20 / h
            out.append({"universe": label, "H": h, "net_of_controls": resid, "months": len(s),
                        "IC": round(s.mean(), 4), "t": round(s.mean() / s.std() * np.sqrt(n_eff), 2),
                        "IC>0 share": round((s > 0).mean(), 2)})
    return out

res = []
for label, m in [("all", E.cmv.notna()), ("float cap >= 50亿", E.cmv >= 50e4), ("float cap < 50亿", E.cmv < 50e4),
                 ("2019-2022", E.date < "20230101"), ("2023-2026", E.date >= "20230101")]:
    res += summary(E[m], label)
res = pd.DataFrame(res); res.to_csv(OUT / "holder_change_ic.csv", index=False)
pd.set_option("display.width", 220)
print(f"stock-months {len(E):,}  months {E.date.nunique()}  stocks/month {len(E)/E.date.nunique():.0f}")
print(res.to_string(index=False))
# quintiles of holder change: mean excess return
E["q"] = E.groupby("date").chg.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]))
q = E.groupby("q", observed=True).agg(chg_med=("chg", "median"), x20=("x20", "mean"), x60=("x60", "mean"), x120=("x120", "mean"),
                                       hit60=("x60", lambda s: (s > 0).mean()), n=("chg", "size"))
q[["x20", "x60", "x120"]] *= 100; print("\nquintile (1 = holders fell most), excess return %"); print(q.round(3).to_string())
# 2x2: holder change sign x same-window price move
E["holders"] = np.where(E.chg <= -0.05, "fell >=5%", np.where(E.chg >= 0.05, "rose >=5%", "flat"))
E["price"] = np.where(E.past > 0, "price up 60d", "price down 60d")
t = E.pivot_table(index="holders", columns="price", values="x60", aggfunc=["mean", "size"])
t["mean"] *= 100; print("\n60-day excess % by holder change x past 60-day price move"); print(t.round(2).to_string())
q.to_csv(OUT / "holder_change_quintiles.csv"); t.to_csv(OUT / "holder_change_2x2.csv")
