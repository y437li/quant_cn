"""History of the 驰宏 watch rule: average return over the next 3 months (63 sessions).

Quarter ends 2020-12 .. 2026-06 (winner rate from meta/runs/holder_nowcast/cyq_qe.parquet), float
cap >= 50 亿. Layers, all point-in-time (announced on or before the date):
  A 下杀: close <= 65% of the 250-session high
  B + winner rate <= 10%
  C + large orders (大单+特大单) net positive in >= 2 of the last 4 weeks (5-session blocks)
  D + latest announced holder count fell vs the period before
  E + margin balance not lower than 20 sessions ago
  F + latest announced single-quarter gross margin above the same quarter a year earlier
Excess = stock return - equal-weight mean of the same universe on the same date.
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root); L = LAKE / "curated"
OUT = LAKE / "meta/runs/research/20261113_niche_industries"
src = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda sql: duckdb.sql(sql).df()
H = 63
px = q(f"""SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS c FROM {src('daily')} d
          JOIN {src('adj_factor')} a USING (ts_code, trade_date) WHERE d.trade_date >= '20191201'""")
px = px.pivot(index="trade_date", columns="ts_code", values="c").sort_index()
cm = q(f"SELECT ts_code, trade_date, circ_mv FROM {src('daily_basic')} WHERE trade_date >= '20191201'")
cm = cm.pivot(index="trade_date", columns="ts_code", values="circ_mv").reindex(index=px.index, columns=px.columns)
mg = q(f"SELECT ts_code, trade_date, rzye FROM {src('margin_detail')} WHERE trade_date >= '20191201'")
mg = mg.pivot(index="trade_date", columns="ts_code", values="rzye").reindex(index=px.index, columns=px.columns)
lg = q(f"""SELECT ts_code, trade_date, buy_lg_amount + buy_elg_amount - sell_lg_amount - sell_elg_amount AS f
          FROM {src('moneyflow')} WHERE trade_date >= '20191201'""")
lg = lg.pivot(index="trade_date", columns="ts_code", values="f").reindex(index=px.index, columns=px.columns)
dd = px / px.rolling(250, min_periods=200).max() - 1
fwd = px.shift(-H) / px - 1
mg_up = mg / mg.shift(20) - 1
weeks = sum((lg.rolling(5, min_periods=4).sum().shift(5 * k) > 0).astype(float) for k in range(4))

hn = q(f"""SELECT ts_code, end_date, min(ann_date) AS ann, arg_min(holder_num, ann_date) AS n
          FROM {src('events/stk_holdernumber')} WHERE end_date >= '20190101' AND ann_date IS NOT NULL GROUP BY 1, 2""")
hn = hn.sort_values(["ts_code", "end_date"]); hn["hchg"] = hn.groupby("ts_code")["n"].pct_change()
hn = hn.dropna(subset=["hchg"]).assign(di=lambda d: d["ann"].astype(int)).sort_values("di")

inc = q(f"""SELECT ts_code, end_date, f_ann_date, revenue, oper_cost FROM {src('fundamentals/income')}
           WHERE end_date >= '20190101' AND report_type = '1' AND f_ann_date IS NOT NULL""")
inc = inc.sort_values("f_ann_date").drop_duplicates(["ts_code", "end_date"], keep="first")  # first print = PIT
inc = inc.sort_values(["ts_code", "end_date"]); inc["y"] = inc["end_date"].str[:4]
for col in ("revenue", "oper_cost"):
    inc["q_" + col] = inc[col] - inc.groupby(["ts_code", "y"])[col].shift().fillna(0)
inc["gm"] = 1 - inc["q_oper_cost"] / inc["q_revenue"]
inc["gm_ly"] = inc.groupby([inc["ts_code"], inc["end_date"].str[4:]])["gm"].shift()
inc = inc.dropna(subset=["gm", "gm_ly"]).assign(gm_up=lambda d: d["gm"] > d["gm_ly"], di=lambda d: d["f_ann_date"].astype(int))
inc = inc.sort_values("di")

cy = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/cyq_qe.parquet")
cy["d"] = cy["trade_date"].astype(str)
rows = []
for d, g in cy.groupby("d"):
    if d not in px.index or fwd.loc[d].notna().sum() == 0:
        continue
    big = cm.loc[d] >= 50e4
    f = pd.DataFrame({"dd": dd.loc[d], "r": fwd.loc[d], "weeks": weeks.loc[d], "mg_up": mg_up.loc[d]})[big & fwd.loc[d].notna()]
    f["x"] = f["r"] - f["r"].mean()
    f = f.join(g.set_index("ts_code")[["winner_rate"]], how="inner")
    f["date"] = d; rows.append(f)
E = pd.concat(rows).rename_axis("ts_code").reset_index()
E["di"] = E["date"].astype(int); E = E.sort_values("di")
E = pd.merge_asof(E, hn[["ts_code", "di", "hchg"]], on="di", by="ts_code", direction="backward")
E = pd.merge_asof(E, inc[["ts_code", "di", "gm_up"]], on="di", by="ts_code", direction="backward")
E.to_parquet(OUT / "rule_backtest_events.parquet")

nq = E["date"].nunique()
def stat(name: str, m: pd.Series) -> dict:
    g = E[m]
    return {"条件": name, "样本": len(g), "每季只数": round(len(g) / nq, 1),
            "3月绝对均值%": round(g["r"].mean() * 100, 1), "3月超额均值%": round(g["x"].mean() * 100, 1),
            "超额中位%": round(g["x"].median() * 100, 1), "跑赢比例": round((g["x"] > 0).mean(), 2),
            "最差%": round(g["r"].min() * 100, 0) if len(g) else np.nan}
A = E["dd"] <= -0.35; B = E["winner_rate"] <= 10; C = E["weeks"] >= 2
D = E["hchg"] < 0; Ee = E["mg_up"] >= 0; F = E["gm_up"].fillna(False).astype(bool)
r = [stat("全部（流通≥50亿，季末）", E["dd"].notna()), stat("A 下杀≥35%", A), stat("A+B 获利盘≤10%", A & B),
     stat("A+B+C 大单4周≥2周流入", A & B & C), stat("A+B+C+D 户数下降", A & B & C & D),
     stat("A+B+C+D+E 融资止跌", A & B & C & D & Ee), stat("A..F 毛利率同比改善", A & B & C & D & Ee & F),
     stat("对照：A+B 但大单4周≤1周流入", A & B & ~C), stat("对照：A+B+C 但户数上升", A & B & C & ~D)]
pd.set_option("display.width", 220)
print(f"quarter ends {nq}: {sorted(E['date'].unique())[0]} .. {sorted(E['date'].unique())[-1]}")
print(pd.DataFrame(r).to_string(index=False))
full = E[A & B & C & D & Ee]
print("\nA..E by quarter"); print(full.groupby("date").agg(n=("x", "size"), abs_pct=("r", "mean"), x_pct=("x", "mean")).mul([1, 100, 100]).round(1).to_string())
