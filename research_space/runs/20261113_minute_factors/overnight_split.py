"""Plan-04 follow-up: split each factor's day-1 decile long-short into overnight (close t -> open t+1)
and intraday (open t+1 -> close t+1) legs, to explain the negative h=1 Sharpe."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
OUT = LAKE / "meta/runs/research/20261113_minute_factors"; OUT.mkdir(parents=True, exist_ok=True)
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
con = duckdb.connect()
px = con.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c
  from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date)
  where d.trade_date >= '20190101'""").df()
O = px.pivot(index="trade_date", columns="ts_code", values="o").sort_index()
C = px.pivot(index="trade_date", columns="ts_code", values="c").reindex_like(O)
leg = {"close_close": C.shift(-1) / C - 1, "overnight": O.shift(-1) / C - 1, "intraday": C.shift(-1) / O.shift(-1) - 1}
fe = con.sql(f"select trade_date, ts_code, factor, value from {r('derived/features')}").df()
rows = []
for f, g in fe.groupby("factor"):
    F = g.pivot(index="trade_date", columns="ts_code", values="value").reindex(index=O.index, columns=O.columns)
    rk = F.rank(axis=1, pct=True)
    top, bot = rk >= 0.9, rk <= 0.1
    for name, R in leg.items():
        ls = (R.where(top).mean(axis=1) - R.where(bot).mean(axis=1)).dropna()
        ls = ls[ls.index >= F.dropna(how="all").index.min()]
        rows.append({"factor": f, "leg": name, "days": len(ls), "mean_bp": round(ls.mean() * 1e4, 2),
                     "ann_sharpe": round(ls.mean() / ls.std() * np.sqrt(244), 2)})
res = pd.DataFrame(rows)
res.to_csv(OUT / "overnight_split.csv", index=False)
print(res.pivot(index="factor", columns="leg", values=["mean_bp", "ann_sharpe"]).to_string())
