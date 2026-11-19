"""Cost-floor breaks (as cost_break.py) split by retail flow, the thing RetailGauge estimates.
(a) point in time: the latest announced holder-count change (ann_date <= break day);
(b) realised (look-ahead, descriptive): holder count change from the last period end before the break to the
    first period end >= 30 days after it; RetailGauge nowcasts this (rank IC 0.69) so (b) shows what a perfect
    gauge would separate. The same splits on the all-stock baseline show whether the effect is break-specific."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_cost_break"
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
piv = lambda d, v: d.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
d = q(f"""SELECT d.ts_code, d.trade_date, d.close, d.close * a.adj_factor AS px, b.circ_mv, c.cost_5pct
          FROM {src('daily')} d JOIN {src('adj_factor')} a USING (ts_code, trade_date)
          JOIN {src('daily_basic')} b USING (ts_code, trade_date) JOIN {src('cyq_perf')} c USING (ts_code, trade_date)
          WHERE d.trade_date >= '20210101'""")
close, px, cap, c5 = (piv(d, v) for v in ("close", "px", "circ_mv", "cost_5pct"))
below = close < c5
first = below & ~below.shift(1).rolling(60, min_periods=1).max().fillna(0).astype(bool)
big = cap >= 50e4
hn = q(f"""SELECT ts_code, min(ann_date) AS ann_date, end_date, max(holder_num) AS h
           FROM {src('events/stk_holdernumber')} WHERE holder_num > 0 GROUP BY ts_code, end_date""")
hn = hn.sort_values(["ts_code", "end_date"])
hn["chg_ann"] = hn.groupby("ts_code")["h"].pct_change()
for c in ("ann_date", "end_date"):
    hn[c] = pd.to_datetime(hn[c])


def tag(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.reset_index().rename(columns={"level_0": "trade_date", "level_1": "ts_code"})
    ev["dt"] = pd.to_datetime(ev["trade_date"])
    ev = ev.sort_values("dt")
    pit = hn.dropna(subset=["chg_ann"]).sort_values("ann_date")[["ts_code", "ann_date", "chg_ann"]]
    ev = pd.merge_asof(ev, pit, left_on="dt", right_on="ann_date", by="ts_code", direction="backward")
    pre = hn.sort_values("end_date")[["ts_code", "end_date", "h"]].rename(columns={"h": "h0"})
    ev = pd.merge_asof(ev, pre, left_on="dt", right_on="end_date", by="ts_code", direction="backward")
    ev["dt30"] = ev["dt"] + pd.Timedelta(days=30)
    post = hn.sort_values("end_date")[["ts_code", "end_date", "h"]].rename(columns={"end_date": "end1", "h": "h1"})
    ev = pd.merge_asof(ev.sort_values("dt30"), post, left_on="dt30", right_on="end1", by="ts_code",
                       direction="forward", tolerance=pd.Timedelta(days=120))
    ev["chg_real"] = ev["h1"] / ev["h0"] - 1
    return ev


rows = []
for h in (20, 60):
    f = px.shift(-h) / px - 1
    mkt = f.where(big).mean(axis=1)
    low = px.rolling(h, min_periods=1).min().shift(-h) / px - 1
    ok = (big & f.notna()).copy()
    ok.loc[ok.index < "20210301"] = False
    samp = ok.copy()
    samp.loc[~samp.index.isin(samp.index[::20])] = False
    for who, m in (("跌破", ok & first), ("对照", samp)):
        ev = tag(pd.DataFrame({"x": f[m].sub(mkt, axis=0).stack(), "low": low[m].stack()}).dropna())
        ev["real_q"] = ev.groupby(ev["dt"].dt.year)["chg_real"].transform(lambda s: pd.qcut(s, 5, labels=False, duplicates="drop"))
        groups = {
            "全部": ev,
            "PIT 最近公告户数增加": ev[ev["chg_ann"] > 0],
            "PIT 最近公告户数减少": ev[ev["chg_ann"] <= 0],
            "事后 户数增幅最大 1/5（散户涌入）": ev[ev["real_q"] == 4],
            "事后 户数增幅中间 3/5": ev[ev["real_q"].between(1, 3)],
            "事后 户数降幅最大 1/5（散户离场）": ev[ev["real_q"] == 0],
        }
        for name, g in groups.items():
            rows.append({"期限": h, "样本组": who, "分组": name, "样本": len(g), "超额均%": g["x"].mean() * 100,
                         "超额中位%": g["x"].median() * 100, "跑赢率": (g["x"] > 0).mean(),
                         "再跌≥10%": (g["low"] <= -0.10).mean(), "户数变化中位%": g["chg_real"].median() * 100})
res = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print(res.round(3).to_string(index=False))
res.to_csv(OUT / "cost_break_retail.csv", index=False)
