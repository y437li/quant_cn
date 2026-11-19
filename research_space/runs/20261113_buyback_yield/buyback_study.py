"""Plan 23 phase 4: do buybacks predict returns? (a) event study after a 预案 by planned size (% of total
market cap; < 0.1% = restricted-share cancellations, dropped), entry the session after the announcement,
20 / 60 / 120-session excess vs the equal-weight universe (float cap >= 30 亿), split pre / post 2024;
(b) month-end rank IC of dividend yield, buyback yield (BuybackLedger, 12 months executed / total market
cap) and their sum, universe float cap >= 50 亿, 20 / 60 sessions, t+1 start."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.buyback_ledger import BuybackLedger
from quant_cn.lake.shareholder_yield_reader import ShareholderYieldReader

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_buyback_yield"
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
piv = lambda d, v: d.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
px = piv(q(f"""SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS c FROM {src('daily')} d JOIN {src('adj_factor')} a
              USING (ts_code, trade_date) WHERE d.trade_date >= '20181001'"""), "c")
basic = q(f"SELECT ts_code, trade_date, circ_mv, total_mv, dv_ttm FROM {src('daily_basic')} WHERE trade_date >= '20181001'")
cm, tm = piv(basic, "circ_mv").reindex_like(px), piv(basic, "total_mv").reindex_like(px)
dv = piv(basic, "dv_ttm").reindex_like(px)
rows = q(f"SELECT DISTINCT ts_code, ann_date, end_date, proc, exp_date, vol, amount, high_limit FROM {src('events/repurchase')} ORDER BY ts_code, ann_date")
days = px.index.to_numpy(); pos = {d: i for i, d in enumerate(days)}
fwd = {h: px.shift(-h) / px - 1 for h in (20, 60, 120)}

# (a) 预案 events
ev = rows[rows["proc"] == "预案"].copy()
ev["entry"] = [days[i] if i < len(days) else None for i in np.searchsorted(days, ev["ann_date"].to_numpy(), side="right")]
ev = ev.dropna(subset=["entry"])
ev = ev[ev["ts_code"].isin(px.columns)]
ev["mv"] = [tm.at[d, c] for d, c in zip(ev["entry"], ev["ts_code"])]
ev["cap"] = [cm.at[d, c] for d, c in zip(ev["entry"], ev["ts_code"])]
ev = ev[(ev["cap"] >= 30e4) & ev["mv"].notna()]
ev["size"] = ev["amount"] / (ev["mv"] * 1e4) * 100
ev = ev[ev["size"] >= 0.1].drop_duplicates(["ts_code", "entry"])
big = cm >= 30e4
for h in fwd:
    mkt = fwd[h].where(big).mean(axis=1)
    ev[f"x{h}"] = [fwd[h].at[d, c] - mkt.at[d] for d, c in zip(ev["entry"], ev["ts_code"])]
ev["bucket"] = pd.cut(ev["size"], [0.1, 0.5, 1, 2, 1e9], labels=["0.1-0.5%", "0.5-1%", "1-2%", ">=2%"], right=False)
ev["period"] = np.where(ev["entry"] < "20240101", "2018-2023", "2024-2026")

def stat(g: pd.DataFrame) -> pd.Series:
    out = {"样本": len(g)}
    for h in (20, 60, 120):
        x = g[f"x{h}"].dropna()
        out[f"{h}日均%"] = x.mean() * 100; out[f"{h}日胜率"] = (x > 0).mean()
        out[f"{h}日t"] = x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
    out["60日中位%"] = g["x60"].median() * 100
    return pd.Series(out)

pd.set_option("display.width", 220)
cols = ["样本", "20日均%", "20日t", "60日均%", "60日中位%", "60日胜率", "60日t", "120日均%", "120日胜率", "120日t"]
print("(a) 回购预案（计划额 / 总市值）")
print(ev.groupby("bucket", observed=True).apply(stat)[cols].round(2).to_string())
print(ev.groupby(["period", "bucket"], observed=True).apply(stat)[cols].round(2).to_string())
ev.to_parquet(OUT / "plan_events.parquet")

# (b) month-end IC
ledger = BuybackLedger(None)
me = pd.Series(px.index, index=px.index).groupby(px.index.str[:6]).last()
me = [d for d in me if "20190101" <= d <= "20260815"]
nf = {h: px.shift(-1 - h) / px.shift(-1) - 1 for h in (20, 60)}
res = []
for d in me:
    executed = ledger.compute_executed(rows, d)
    b = pd.DataFrame({"dv_ttm": dv.loc[d], "total_mv": tm.loc[d]}).dropna(subset=["total_mv"])
    y = ShareholderYieldReader.compute(b, executed)
    f = y.join(pd.DataFrame({"cap": cm.loc[d], "r20": nf[20].loc[d], "r60": nf[60].loc[d]}))
    f = f[f["cap"] >= 50e4].dropna(subset=["r20"])
    for h in (20, 60):
        x = f[f"r{h}"] - f[f"r{h}"].mean()
        for s in ("dividend_yield", "buyback_yield", "shareholder_yield"):
            res.append({"date": d, "h": h, "signal": s, "ic": f[s].rank().corr(x.rank()),
                        "spread": x[f[s] >= f[s].quantile(0.8)].mean() - x[f[s] <= f[s].quantile(0.2)].mean(),
                        "has_bb": (f["buyback_yield"] > 0).mean()})
R = pd.DataFrame(res)
R["period"] = np.where(R["date"] < "20240101", "2019-2023", "2024-2026")
def ics(g: pd.DataFrame) -> pd.Series:
    return pd.Series({"月数": len(g), "IC均值": g["ic"].mean(), "t": g["ic"].mean() / g["ic"].std() * np.sqrt(len(g)),
                      "高-低组%": g["spread"].mean() * 100, "有回购的比例": g["has_bb"].mean()})
print("\n(b) 月末 IC（流通市值 ≥ 50 亿）")
print(R.groupby(["h", "signal"]).apply(ics).round(3).to_string())
print(R.groupby(["period", "h", "signal"]).apply(ics).round(3).to_string())
R.to_csv(OUT / "ic.csv", index=False)
