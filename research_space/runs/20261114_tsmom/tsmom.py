"""Time-series momentum on China commodity futures (ad hoc, 2026-11-14).

Main (mapped) contract daily returns from close / pre_close of the same contract (no roll jumps);
monthly rebalance; position = sign(past L-month return) x 40% / ex-ante vol (EWMA 60d), capped 3x;
portfolio = equal-weight average across families with data. Writes CSVs to the lake research folder.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import duckdb, numpy as np, pandas as pd, yaml

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom"
REPO = Path(__file__).resolve().parents[3]
fams = [f["family"] for f in yaml.safe_load(open(REPO / "config/futures_monitor.yaml"))["families"]]
names = {f["family"]: f["name"] for f in yaml.safe_load(open(REPO / "config/futures_monitor.yaml"))["families"]}
groups = {f["family"]: f["group"] for f in yaml.safe_load(open(REPO / "config/futures_monitor.yaml"))["families"]}
c = duckdb.connect()
inl = ",".join(f"'{f}'" for f in fams)
r = c.execute(f"""
select m.ts_code fam, m.trade_date, d.close/d.pre_close-1 ret
from read_parquet('{LAKE}/curated/fut_mapping/**/*.parquet') m
join read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') d on d.ts_code=m.mapping_ts_code and d.trade_date=m.trade_date
where m.ts_code in ({inl}) and d.pre_close>0 and d.close>0""").df()
r["trade_date"] = pd.to_datetime(r["trade_date"])
R = r.pivot_table(index="trade_date", columns="fam", values="ret").sort_index()
R = R.clip(-0.2, 0.2)
vol = (R.pow(2).ewm(com=60, min_periods=60).mean() * 252) ** 0.5
M = (1 + R.fillna(0)).resample("ME").prod() - 1
M = M.where(R.resample("ME").count() > 10)
V = vol.resample("ME").last()
res = {}
for L in (1, 3, 6, 12):
    past = (1 + M.fillna(0)).rolling(L).apply(np.prod, raw=True) - 1
    past = past.where(M.notna().rolling(L).sum() == L)
    w = (np.sign(past) * (0.40 / V)).clip(-3, 3).shift(1)
    pnl = (w * M).mean(axis=1, skipna=True).dropna()
    pnl = pnl[pnl.index >= "2020-01-01"]
    res[L] = pnl
    # pooled predictive: sign of past L vs next month return / vol
    nxt = (M / V.shift(1)).stack()
    sig = np.sign(past.shift(1)).stack()
    j = pd.concat([sig, nxt], axis=1, keys=["s", "y"]).dropna()
    j = j[j.index.get_level_values(0) >= "2020-01-01"]
    hit = (np.sign(j.y) == j.s).mean()
    print(f"L={L:>2}m  ann.ret {pnl.mean()*12:+.1%}  vol {pnl.std()*12**.5:.1%}  Sharpe {pnl.mean()/pnl.std()*12**.5:.2f}  "
          f"t {pnl.mean()/pnl.std()*len(pnl)**.5:.2f}  months {len(pnl)}  hit {hit:.1%}  n={len(j)}")
P = pd.DataFrame(res)
P.to_csv(OUT / "tsmom_monthly_pnl.csv")
print("\nby year (sum of monthly):")
print((P.groupby(P.index.year).sum() * 100).round(1).to_string())
# per family, 12m, full period
past12 = (1 + M.fillna(0)).rolling(12).apply(np.prod, raw=True) - 1
past12 = past12.where(M.notna().rolling(12).sum() == 12)
w12 = (np.sign(past12) * (0.40 / V)).clip(-3, 3).shift(1)
pf = (w12 * M)[M.index >= "2020-01-01"]
fam_sr = (pf.mean() / pf.std() * 12**.5)[pf.count() >= 36].dropna()  # >= 3 years of signals
g = pd.DataFrame({"name": [names[f] for f in fam_sr.index], "group": [groups[f] for f in fam_sr.index], "sharpe": fam_sr})
g.to_csv(OUT / "tsmom12_by_family.csv")
print("\n12m TSMOM Sharpe by group:"); print(g.groupby("group").sharpe.agg(["median", "mean", "count"]).round(2).to_string())
# current signals from daily returns up to the last mapped day
last = R.index[-1]
cum = lambda n: (1 + R.iloc[-n:].fillna(0)).prod() - 1
cur = pd.DataFrame({"name": [names.get(f, f) for f in R.columns], "group": [groups.get(f, "") for f in R.columns],
                    "r1m": cum(21), "r3m": cum(63), "r12m": cum(252)})
cur["signal12"] = np.sign(cur.r12m)
cur.to_csv(OUT / "current_signals.csv")
print(f"\nas of {last.date()}:")
for f in ("MA.ZCE", "PP.DCE", "SC.INE", "V.DCE", "SH.ZCE", "SA.ZCE", "AO.SHF"):
    x = cur.loc[f]; print(f"{x['name']}: 1m {x.r1m:+.1%} 3m {x.r3m:+.1%} 12m {x.r12m:+.1%}")
print("能化 12m 信号: 多", int((cur[cur.group=="能化"].signal12>0).sum()), "空", int((cur[cur.group=="能化"].signal12<0).sum()))
