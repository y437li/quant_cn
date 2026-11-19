"""Do margin-trading signals predict returns? Month-end cross sections 2020-01 .. 2026-08, margin targets
with float cap >= 50 亿. Signals use margin_detail up to t (published after the close / next morning),
returns run from t+1 close for 20 and 60 sessions, excess vs the cross-section mean. Rank IC per month,
mean, t-stat (IC mean / std * sqrt(n)), top-minus-bottom quintile; plus the IC after removing the
20-day return (cross-sectional OLS residual) to see what is left beyond momentum."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_margin_signals"; OUT.mkdir(parents=True, exist_ok=True)
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
piv = lambda d, v: d.pivot(index="trade_date", columns="ts_code", values=v)
px = piv(q(f"""SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS c FROM {src('daily')} d JOIN {src('adj_factor')} a USING (ts_code, trade_date)
              WHERE d.trade_date >= '20191001'"""), "c").sort_index()
amt = piv(q(f"SELECT ts_code, trade_date, amount * 1e3 AS a FROM {src('daily')} WHERE trade_date >= '20191001'"), "a").reindex_like(px)
cm = piv(q(f"SELECT ts_code, trade_date, circ_mv * 1e4 AS m FROM {src('daily_basic')} WHERE trade_date >= '20191001'"), "m").reindex_like(px)
md = q(f"SELECT ts_code, trade_date, rzye, rzmre, rzche, rqye, rqyl FROM {src('margin_detail')} WHERE trade_date >= '20191001'")
rz, buy, rep, rq, rql = (piv(md, v).reindex_like(px) for v in ("rzye", "rzmre", "rzche", "rqye", "rqyl"))
sig = {
    "融资余额/流通市值": rz / cm,
    "融资余额20日变化": rz / rz.shift(20) - 1,
    "20日融资净买入/流通市值": (buy - rep).rolling(20, min_periods=15).sum() / cm,
    "融资买入/成交额(20日)": buy.rolling(20, min_periods=15).sum() / amt.rolling(20, min_periods=15).sum(),
    "融券余额/流通市值": rq / cm,
    "融券股数20日变化": np.log1p(rql) - np.log1p(rql.shift(20)),
    "对照:过去20日涨跌": px / px.shift(20) - 1,
}
mom = sig["对照:过去20日涨跌"]
fwd = {h: px.shift(-1 - h) / px.shift(-1) - 1 for h in (20, 60)}
dates = pd.Series(px.index, index=px.index).groupby(px.index.str[:6]).last()
dates = [d for d in dates if "20200101" <= d <= "20260815"]

def ic_row(name: str, s: pd.DataFrame, h: int, resid: bool) -> dict:
    ics, spreads = [], []
    for d in dates:
        f = pd.DataFrame({"s": s.loc[d], "r": fwd[h].loc[d], "m": mom.loc[d], "cap": cm.loc[d], "rz": rz.loc[d]})
        f = f[(f["cap"] >= 50e8) & f["rz"].notna()].replace([np.inf, -np.inf], np.nan).dropna()
        if len(f) < 100:
            continue
        f["x"] = f["r"] - f["r"].mean()
        if resid:
            b = np.polyfit(f["m"].rank(), f["s"].rank(), 1); f["s"] = f["s"].rank() - np.polyval(b, f["m"].rank())
        ics.append(f["s"].rank().corr(f["x"].rank()))
        qn = pd.qcut(f["s"].rank(method="first"), 5, labels=False)
        spreads.append(f.loc[qn == 4, "x"].mean() - f.loc[qn == 0, "x"].mean())
    ic = pd.Series(ics)
    return {"信号": name + ("（剔除动量）" if resid else ""), "期限": h, "月数": len(ic), "IC均值": ic.mean(),
            "t值": ic.mean() / ic.std() * np.sqrt(len(ic)), "IC>0比例": (ic > 0).mean(), "高-低组月均%": np.mean(spreads) * 100}

rows = []
for h in (20, 60):
    for name, s in sig.items():
        rows.append(ic_row(name, s, h, False))
        if not name.startswith("对照"):
            rows.append(ic_row(name, s, h, True))
res = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(res.round(3).to_string(index=False))
res.to_csv(OUT / "margin_ic.csv", index=False)

# stability: split at 2024 (securities lending shrank after 2023-24 rule changes)
full = dates
split = []
for label, keep in (("2020-2023", lambda d: d < "20240101"), ("2024-2026", lambda d: d >= "20240101")):
    dates = [d for d in full if keep(d)]
    for name in ("融资余额20日变化", "20日融资净买入/流通市值", "融券余额/流通市值"):
        for h in (20, 60):
            r = ic_row(name, sig[name], h, True); r["时期"] = label; split.append(r)
dates = full
sp = pd.DataFrame(split)
print("\n分时期（剔除动量）"); print(sp[["时期", "信号", "期限", "月数", "IC均值", "t值", "高-低组月均%"]].round(3).to_string(index=False))
sp.to_csv(OUT / "margin_ic_split.csv", index=False)
