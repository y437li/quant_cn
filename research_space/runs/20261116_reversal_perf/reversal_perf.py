"""How have reversal_1m and reversal_intraday_1m performed, recently and over the full history?
Month-end signals from derived/features (value), universe = derived/universe, entry open(t+1), exit close(t+20)
(the last month runs to the latest close, partial). Per month: rank IC, D10-D1 decile spread (equal weight, before costs).
Also the cumulative long-short path and the top-decile names on the latest date."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
OUT = LAKE / "meta/runs/research/20261116_reversal_perf"; OUT.mkdir(parents=True, exist_ok=True)
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
F = ("reversal_1m", "reversal_intraday_1m")
px = duckdb.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c
  from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date) where d.trade_date >= '20181201'""").df()
O = px.pivot(index="trade_date", columns="ts_code", values="o").sort_index(); C = px.pivot(index="trade_date", columns="ts_code", values="c").sort_index()
idx = C.index; last = idx[-1]
ends = list(pd.Series(idx, index=idx).groupby(idx.str[:6]).last().values)
ends = [d for d in ends if d >= "20190131" and d < last] 
fe = duckdb.sql(f"select trade_date, ts_code, factor, value from {r('derived/features')} where factor in {F} and trade_date in {tuple(ends + [last])}").df()
un = duckdb.sql(f"select trade_date, ts_code from {r('derived/universe')} where in_universe and trade_date in {tuple(ends + [last])}").df()
fe = fe.merge(un, on=["trade_date", "ts_code"])
rows = []
for d in ends:
    i = idx.get_loc(d); j = min(i + 20, len(idx) - 1)
    if i + 1 > len(idx) - 1: continue
    y = (C.iloc[j] / O.iloc[i + 1] - 1).rename("y"); mkt = y.mean()
    g = fe[fe.trade_date == d].pivot(index="ts_code", columns="factor", values="value").join(y, how="inner").dropna()
    for f in F:
        if f not in g: continue
        ic = g[f].rank().corr(g.y.rank()); dec = pd.qcut(g[f].rank(method="first"), 10, labels=False)
        m = g.y.groupby(dec).mean()
        rows.append({"d": d, "f": f, "ic": ic, "ls": m[9] - m[0], "top": m[9] - g.y.mean(), "bot": m[0] - g.y.mean(), "days": j - i, "n": len(g)})
R = pd.DataFrame(rows); R.to_csv(OUT / "reversal_perf_monthly.csv", index=False)
pd.set_option("display.width", 220)
def summ(s):
    return pd.Series({"months": len(s), "IC": s.ic.mean(), "IC_t": s.ic.mean() / s.ic.std() * np.sqrt(len(s)), "IC>0": (s.ic > 0).mean(),
                      "LS%/m": s.ls.mean() * 100, "LS_t": s.ls.mean() / s.ls.std() * np.sqrt(len(s)), "top%": s.top.mean() * 100, "bot%": s.bot.mean() * 100, "worst%": s.ls.min() * 100})
full = R[R.days == 20]
for lab, sel in (("2019-2026 full", full), ("2019-22", full[full.d < "20230101"]), ("2023-25", full[(full.d >= "20230101") & (full.d < "20260101")]),
                 ("2026 YTD", full[full.d >= "20260101"]), ("last 12m", full[full.d >= ends[-13]])):
    print(f"\n== {lab} =="); print(sel.groupby("f").apply(summ, include_groups=False).round(3).to_string())
print("\n== monthly, last 13 signals (last row partial) ==")
t = R[R.d >= ends[-13]].pivot(index="d", columns="f", values=["ic", "ls"]).round(3); t["days"] = R[R.d >= ends[-13]].groupby("d").days.first(); print(t.to_string())
cum = full.pivot(index="d", columns="f", values="ls").add(1).cumprod(); cum.to_csv(OUT / "reversal_perf_cum.csv")
print("\n== cumulative D10-D1 by year-end =="); print(cum.groupby(cum.index.str[:4]).last().round(2).to_string())
g = fe[fe.trade_date == last].pivot(index="ts_code", columns="factor", values="value")
g["rk"] = g.reversal_intraday_1m.rank(pct=True); g["rk_old"] = g.reversal_1m.rank(pct=True)
print(f"\n== {last}: top decile of reversal_intraday_1m: {int((g.rk>0.9).sum())} names; book/watch names ==")
NM = {"600150.SH": "中国船舶", "300308.SZ": "中际旭创", "300502.SZ": "新易盛", "601886.SH": "江河集团", "603369.SH": "今世缘", "603766.SH": "隆鑫通用", "601888.SH": "中国中免", "000657.SZ": "中钨高新"}
look = list(NM); nm = pd.Series(NM)
print(g.reindex(look)[["rk", "rk_old"]].assign(name=nm.reindex(look).values).round(2).to_string())
