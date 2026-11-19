"""Immediate vs confirmation entry for the washout rule (events from rule_backtest.py).

Events: quarter ends 2020-12..2026-06, float cap >= 50 亿; 下杀 + winner <= 10% (+ large orders >= 2 of 4
weeks). Entries: (1) close of the event day; (2) first close above its 20-session mean within 40 sessions;
(3) first close above the event-day cost_50pct (cyq_qe) within 40 sessions; no entry = no trade.
Hold 63 sessions. Costs 0.15% a side. A limit-up close cannot be bought (move to the next session), a
limit-down close cannot be sold (move on). Excess = stock return - equal-weight universe return over the
same sessions."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261113_niche_industries"
src = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
H, WAIT, COST = 63, 40, 0.0015
raw = q(f"SELECT ts_code, trade_date, close FROM {src('daily')} WHERE trade_date >= '20200901'")
adj = q(f"SELECT ts_code, trade_date, adj_factor FROM {src('adj_factor')} WHERE trade_date >= '20200901'")
lim = q(f"SELECT ts_code, trade_date, up_limit, down_limit FROM {src('stk_limit')} WHERE trade_date >= '20200901'")
cm = q(f"SELECT ts_code, trade_date, circ_mv FROM {src('daily_basic')} WHERE trade_date >= '20200901'")
d = raw.merge(adj, on=["ts_code", "trade_date"]).merge(lim, on=["ts_code", "trade_date"], how="left").merge(cm, on=["ts_code", "trade_date"], how="left")
piv = lambda v: d.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
close, px, up, dn, cap = piv("close"), piv("close") * piv("adj_factor"), piv("up_limit"), piv("down_limit"), piv("circ_mv")
ma20 = px.rolling(20, min_periods=15).mean()
ret = px.pct_change(fill_method=None).where(cap.shift() >= 50e4)
mkt = (1 + ret.mean(axis=1).fillna(0.0)).cumprod()
days = list(px.index); pos = {x: i for i, x in enumerate(days)}
E = pd.read_parquet(OUT / "rule_backtest_events.parquet")
cy = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/cyq_qe.parquet").assign(date=lambda x: x["trade_date"].astype(str))
E = E.merge(cy[["ts_code", "date", "cost_50pct"]], on=["ts_code", "date"], how="left")
A, B, C = E["dd"] <= -0.35, E["winner_rate"] <= 10, E["weeks"] >= 2

def trade(code: str, date: str, mode: str) -> dict | None:
    if code not in px.columns or date not in pos:
        return None
    i0 = pos[date]
    s, c, u, l, m = px[code], close[code], up[code], dn[code], ma20[code]
    entry = None
    for i in range(i0, min(i0 + WAIT + 1, len(days))):
        ok = (mode == "now" and i == i0) or (mode == "ma20" and s.iloc[i] > m.iloc[i]) or \
             (mode == "cost50" and c.iloc[i] > cost50.get((code, date), np.inf))
        if mode == "now" and i > i0 + 5:
            break
        if (ok or (mode == "now" and entry is None and i > i0)) and pd.notna(s.iloc[i]) and not (pd.notna(u.iloc[i]) and c.iloc[i] >= u.iloc[i] - 1e-6):
            entry = i; break
    if entry is None or entry + H >= len(days):
        return None
    ex = entry + H
    while ex < len(days) - 1 and pd.notna(l.iloc[ex]) and c.iloc[ex] <= l.iloc[ex] + 1e-6:
        ex += 1
    if pd.isna(s.iloc[ex]) or pd.isna(s.iloc[entry]):
        return None
    r = (s.iloc[ex] / s.iloc[entry]) * (1 - COST) ** 2 - 1
    path = s.iloc[entry:ex + 1] / s.iloc[entry] - 1
    return {"r": r, "x": r - (mkt.iloc[ex] / mkt.iloc[entry] - 1), "wait": entry - i0, "mdd": path.min()}

cost50 = {(t, dte): v for t, dte, v in zip(E["ts_code"], E["date"], E["cost_50pct"])}
rows = []
for label, mask in (("下杀+获利盘≤10%+大单≥2周", A & B & C), ("下杀+获利盘≤10%", A & B)):
    ev = E[mask]
    for mode, name in (("now", "立即买"), ("ma20", "站上20日均线再买"), ("cost50", "站上成本中位再买")):
        res = [t for t in (trade(a, b, mode) for a, b in zip(ev["ts_code"], ev["date"])) if t]
        f = pd.DataFrame(res)
        rows.append({"事件": label, "进场": name, "事件数": len(ev), "成交": len(f), "成交率": len(f) / len(ev),
                     "平均等待天": f["wait"].mean(), "3月绝对%": f["r"].mean() * 100, "超额均%": f["x"].mean() * 100,
                     "超额中位%": f["x"].median() * 100, "跑赢率": (f["x"] > 0).mean(), "持有期再跌10%比例": (f["mdd"] <= -0.10).mean(),
                     "最差%": f["r"].min() * 100})
res = pd.DataFrame(rows)
pd.set_option("display.width", 230)
print(res.round(2).to_string(index=False))
res.to_csv(OUT / "confirm_entry.csv", index=False)
