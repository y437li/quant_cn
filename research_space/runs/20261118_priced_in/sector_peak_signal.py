"""Sector top signal: "good news no longer lifts the price" (follows priced_in.py), 2019-2026.

Per SW L2 sector (point-in-time membership) and fiscal quarter: the sector's best-surprise events
(global SUE deciles 8-9, >= 5 events): mean pre60 and reaction [0,+1] excess. Signal date = the day
80% of the sector's events for the quarter are out. Signal = pre60 >= PRE and reaction <= REACT.
Forward = sector index excess vs the equal-weight mean of all L2 indices, +60 / +120 sessions after
the signal date; the sector's own 120-session excess before it marks a prior rally. Retail = median
shareholder-count change of the members for that quarter end (stk_holdernumber).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
PRE, REACT, RALLY, MIN_N = 15.0, 1.0, 20.0, 5
CASES = ["白酒Ⅱ", "光伏设备", "电池", "半导体", "通信设备", "元件", "医疗服务", "煤炭开采", "乘用车"]


def load(q: LakeQuery) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    mem = q.sql("SELECT ts_code, l2_code, l2_name, in_date, coalesce(out_date, '99991231') AS out_date "
                "FROM curated.index_member_all")
    sw = q.sql("SELECT ts_code, trade_date, close FROM curated.sw_daily WHERE ts_code IN "
               "(SELECT index_code FROM curated.index_classify WHERE src = 'SW2021' AND level = 'L2')")
    hold = q.sql("SELECT ts_code, end_date, arg_max(holder_num, ann_date) AS h FROM curated.stk_holdernumber "
                 "WHERE end_date >= '20180331' AND substr(end_date, 5, 4) IN ('0331','0630','0930','1231') "
                 "GROUP BY 1, 2")
    names = q.sql("SELECT index_code, industry_name FROM curated.index_classify WHERE src='SW2021' AND level='L2'")
    return mem, sw, hold, names


def build_panel(ev: pd.DataFrame, mem: pd.DataFrame, hold: pd.DataFrame) -> pd.DataFrame:
    ev = ev.dropna(subset=["first_day"]).copy()
    ev["first_day"] = ev["first_day"].astype(str)
    m = ev.merge(mem, on="ts_code")
    m = m[(m["in_date"] <= m["end_date"]) & (m["out_date"] > m["end_date"])]
    m = m.drop_duplicates(["ts_code", "end_date"])
    hold = hold.sort_values(["ts_code", "end_date"])
    hold["hchg"] = hold.groupby("ts_code")["h"].pct_change() * 100
    m = m.merge(hold[["ts_code", "end_date", "hchg"]], on=["ts_code", "end_date"], how="left")
    top = m[m["dec"] >= 8].groupby(["l2_code", "end_date"]).agg(
        n_top=("sue", "size"), pre60=("pre60", "mean"), react=("react", "mean"), post60=("post60", "mean"))
    allq = m.groupby(["l2_code", "end_date"]).agg(
        n=("sue", "size"), sig_day=("first_day", lambda s: s.sort_values().iloc[int(0.8 * (len(s) - 1))]),
        hchg=("hchg", "median"), up_share=("hchg", lambda s: (s > 0).mean() * 100))
    return allq.join(top, how="inner").reset_index().query("n_top >= @MIN_N")


def attach_forward(panel: pd.DataFrame, sw: pd.DataFrame) -> pd.DataFrame:
    px = sw.pivot(index="trade_date", columns="ts_code", values="close").sort_index()
    lr = np.log(px).diff()
    cum = lr.sub(lr.mean(axis=1), axis=0).fillna(0).cumsum()
    dates = cum.index.to_numpy()
    out = panel[panel["l2_code"].isin(cum.columns)].copy()
    i = np.searchsorted(dates, out["sig_day"].to_numpy())
    col = out["l2_code"].to_numpy()
    for name, (a, b) in {"back120": (-120, 0), "fwd60": (0, 60), "fwd120": (0, 120)}.items():
        lo, hi = i + a, i + b
        ok = (lo >= 0) & (hi < len(dates))
        vals = np.full(len(out), np.nan)
        vals[ok] = [(cum.at[dates[h], c] - cum.at[dates[l], c]) * 100 for l, h, c in zip(lo[ok], hi[ok], col[ok])]
        out[name] = vals
    return out


def summarise(p: pd.DataFrame, names: pd.Series) -> None:
    p = p.copy()
    p["name"] = p["l2_code"].map(names)
    p["signal"] = (p["pre60"] >= PRE) & (p["react"] <= REACT)
    p["rally"] = p["back120"] >= RALLY
    pd.set_option("display.width", 220)
    g = p.groupby(["rally", "signal"])[["fwd60", "fwd120", "hchg", "up_share"]].agg(["mean", "count"]).round(2)
    print("## forward sector excess by prior rally (back120 >= %.0f%%) and signal\n" % RALLY, g.to_string())
    for r in (True, False):
        sub = p[p["rally"] == r]
        a, b = sub[sub.signal]["fwd60"].dropna(), sub[~sub.signal]["fwd60"].dropna()
        t = (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
        print(f"rally={r}: fwd60 signal {a.mean():.2f} (n {len(a)}) vs no {b.mean():.2f} (n {len(b)}), t {t:.2f}")
    print("\n## all rally+signal cases\n", p[p.rally & p.signal].sort_values("sig_day")[
        ["name", "end_date", "sig_day", "back120", "pre60", "react", "hchg", "up_share", "fwd60", "fwd120"]].round(1).to_string())
    print("\n## retail: fwd60 by holder-change tercile within rally sectors")
    rp = p[p.rally].copy()
    rp["ht"] = pd.qcut(rp["hchg"], 3, labels=["holders down", "mid", "holders up"])
    print(rp.groupby(["ht", "signal"], observed=True)["fwd60"].agg(["mean", "count"]).round(2).to_string())
    print("\n## crowding: median holder change >= 10% (any sector / rally sectors)")
    for lab, sub in (("all", p), ("rally", p[p.rally])):
        hot = sub["hchg"] >= 10
        print(lab, "crowded fwd60 %.2f fwd120 %.2f (n %d) vs rest fwd60 %.2f" % (
            sub[hot]["fwd60"].mean(), sub[hot]["fwd120"].mean(), hot.sum(), sub[~hot]["fwd60"].mean()))
    print(p[p.rally & (p.hchg >= 10)].sort_values("sig_day")[["name", "end_date", "back120", "pre60", "react", "hchg", "fwd60", "fwd120"]].round(1).to_string())
    for case in CASES:
        c = p[p["name"] == case].sort_values("end_date")
        print(f"\n## {case}\n", c[["end_date", "sig_day", "back120", "pre60", "react", "post60", "hchg", "signal", "fwd60", "fwd120"]].round(1).to_string(index=False))


def main() -> None:
    cfg = Config.load(REPO)
    ev = pd.read_parquet(Path(cfg.lake.root) / "meta/runs/research/20261118_priced_in/events.parquet")
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    mem, sw, hold, names = load(LakeQuery(cat))
    cat.close()
    panel = attach_forward(build_panel(ev, mem, hold), sw)
    summarise(panel, names.set_index("index_code")["industry_name"])


if __name__ == "__main__":
    main()
