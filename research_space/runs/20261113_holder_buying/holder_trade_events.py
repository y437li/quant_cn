"""Do major-holder / executive purchases (增持) predict returns? Event study on stk_holdertrade 2019-01..2026-09.

Event = announcement of an increase (IN) or decrease (DE) by holder type C (company / major holder),
G (executive), P (individual); same stock, direction and type within 20 sessions = one event. Entry at the
close of the first session after ann_date (PIT); excess = return - equal-weight mean of the universe
(float cap >= 30 亿) over 20 / 60 / 120 sessions. Buckets: size (change_ratio, % of float), period
(pre-2024 / 2024+), prior drawdown from the 250-session high."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_holder_buying"; OUT.mkdir(parents=True, exist_ok=True)
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
px = q(f"""SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS c FROM {src('daily')} d JOIN {src('adj_factor')} a USING (ts_code, trade_date)
          WHERE d.trade_date >= '20180101'""").pivot(index="trade_date", columns="ts_code", values="c").sort_index()
cm = q(f"SELECT ts_code, trade_date, circ_mv FROM {src('daily_basic')} WHERE trade_date >= '20180101'").pivot(
    index="trade_date", columns="ts_code", values="circ_mv").reindex_like(px)
big = cm >= 30e4
dd = px / px.rolling(250, min_periods=120).max() - 1
fwd = {h: px.shift(-h) / px - 1 for h in (20, 60, 120)}
mkt = {h: fwd[h].where(big).mean(axis=1) for h in fwd}
ev = q(f"""SELECT ts_code, ann_date, in_de, holder_type, sum(change_ratio) AS ratio, count(*) AS rows
          FROM {src('events/stk_holdertrade')} WHERE ann_date >= '20190101' GROUP BY 1, 2, 3, 4""")
days = px.index.to_numpy()
ev["entry"] = [days[i] if i < len(days) else None for i in np.searchsorted(days, ev["ann_date"].to_numpy(), side="right")]
ev = ev.dropna(subset=["entry"]).sort_values(["ts_code", "in_de", "holder_type", "entry"])
pos = {d: i for i, d in enumerate(days)}
ev["i"] = ev["entry"].map(pos)
keep, last = [], {}
for r in ev.itertuples():
    k = (r.ts_code, r.in_de, r.holder_type)
    if k not in last or r.i - last[k] >= 20:
        keep.append(r.Index); last[k] = r.i
ev = ev.loc[keep]
ev = ev[ev["ts_code"].isin(px.columns)]
ev["big"] = [bool(big.at[d, c]) if pd.notna(big.at[d, c]) else False for d, c in zip(ev["entry"], ev["ts_code"])]
ev = ev[ev["big"]]
ev["dd"] = [dd.at[d, c] for d, c in zip(ev["entry"], ev["ts_code"])]
for h in fwd:
    ev[f"x{h}"] = [fwd[h].at[d, c] - mkt[h].at[d] for d, c in zip(ev["entry"], ev["ts_code"])]
ev["period"] = np.where(ev["entry"] < "20240101", "2019-2023", "2024-2026")
ev["size"] = pd.cut(ev["ratio"].abs(), [-1, 0.1, 0.5, 1, 1e9], labels=["<0.1%", "0.1-0.5%", "0.5-1%", ">=1%"])
ev.to_parquet(OUT / "events.parquet")
TYPES = {"C": "公司/大股东", "G": "高管", "P": "个人股东"}

def stat(g: pd.DataFrame) -> pd.Series:
    out = {"样本": len(g)}
    for h in (20, 60, 120):
        x = g[f"x{h}"].dropna()
        out[f"{h}日均%"] = x.mean() * 100
        out[f"{h}日中位%"] = x.median() * 100
        out[f"{h}日胜率"] = (x > 0).mean()
        out[f"{h}日t"] = x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
    return pd.Series(out)

pd.set_option("display.width", 250)
cols = ["样本", "20日均%", "20日t", "60日均%", "60日中位%", "60日胜率", "60日t", "120日均%", "120日胜率"]
a = ev.groupby(["in_de", "holder_type"]).apply(stat).rename(index=TYPES, level=1)
print("按方向和类型"); print(a[cols].round(2).to_string())
inc = ev[ev["in_de"] == "IN"]
print("\n增持：按规模（占流通 %）"); print(inc.groupby(["holder_type", "size"], observed=True).apply(stat).rename(index=TYPES, level=0)[cols].round(2).to_string())
print("\n增持：按时期"); print(inc.groupby(["holder_type", "period"]).apply(stat).rename(index=TYPES, level=0)[cols].round(2).to_string())
inc = inc.assign(fell=np.where(inc["dd"] <= -0.3, "跌≥30%后", "其他"))
print("\n增持：是否在大跌后"); print(inc.groupby(["holder_type", "fell"]).apply(stat).rename(index=TYPES, level=0)[cols].round(2).to_string())
