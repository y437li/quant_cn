"""Nonlinear use of the industry-neutral pricing gap (gi = gap percentile within SW L1 and month).

(a) shape: fwd20 / fwd60 excess by 20 gi bins; (b) double sorts gi quintile x momentum, 20d
reversal, turnover, size, consensus growth quintiles (fwd20 excess, dearest − cheapest spread per
control quintile, t); (c) gi x RetailGauge quintile from 2023 (gauge_daily, latest reading on or
before the month end); (d) rules: avoid = gi > 0.9 alone or with a hot condition, add = gi <= 0.1
alone or with a cold condition. Excess vs the covered universe, equal weight; t over months.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
GAUGE = "meta/runs/research/20261117_gauge_daily/gauge_daily.parquet"


def tstat(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.mean() / s.std() * np.sqrt(len(s))) if len(s) > 2 else np.nan


def cell(p: pd.DataFrame, mask: pd.Series, y: str = "ex20") -> tuple[float, float, float, int]:
    m = p[mask].groupby("date")[y].mean()
    return round(m.mean(), 2), round(tstat(m), 2), round((m > 0).mean(), 2), int(mask.sum() / p["date"].nunique())


def load() -> pd.DataFrame:
    cfg = Config.load(REPO)
    root = Path(cfg.lake.root)
    p = pd.read_parquet(root / "meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet")
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    mem = LakeQuery(cat).sql("SELECT DISTINCT ts_code, l1_name FROM curated.index_member_all WHERE is_new = 'Y'")
    cat.close()
    p = p.merge(mem, on="ts_code", how="left")
    for h in (20, 60):
        r = np.exp(p[f"fwd{h}"])
        p[f"ex{h}"] = (r - r.groupby(p["date"]).transform("mean")) * 100
    p["gi"] = p.groupby(["date", "l1_name"])["gap"].rank(pct=True)
    g = pd.read_parquet(root / GAUGE)[["ts_code", "asof", "pct"]].rename(columns={"pct": "gauge"})
    g["asof"] = g["asof"].astype(str)
    p = p.sort_values("date")
    p["k"], g["k"] = p["date"].astype(int), g["asof"].astype(int)
    p = pd.merge_asof(p.sort_values("k"), g.sort_values("k")[["k", "ts_code", "gauge"]], on="k", by="ts_code",
                      tolerance=10000, direction="backward")  # within ~a month (YYYYMMDD ints)
    return p.dropna(subset=["gi", "ex20"])


def main() -> None:
    p = load()
    pd.set_option("display.width", 220)
    b = pd.cut(p["gi"], np.linspace(0, 1, 21), labels=False)
    shape = pd.DataFrame({h: p.groupby(["date", b])[h].mean().unstack().mean() for h in ("ex20", "ex60")}).round(2).T
    print("## (a) excess % by 20 bins of industry-neutral gap (0 = cheapest 5%)\n", shape.to_string())
    p["gq"] = pd.cut(p["gi"], [0, .2, .4, .6, .8, 1.0], labels=False)
    for c in ["mom", "rev20", "turn", "size", "grow"]:
        p["cq"] = p.groupby("date")[c].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
        m = p.groupby(["date", "gq", "cq"])["ex20"].mean().unstack(["gq", "cq"])
        tab = m.mean().unstack("cq").round(2)
        spread = pd.Series({k: tstat(m[(4, k)] - m[(0, k)]) for k in range(5)}).round(2)
        tab.loc["dear−cheap"] = (tab.loc[4] - tab.loc[0]).round(2)
        tab.loc["t"] = spread
        print(f"\n## (b) fwd20 excess %: gap quintile (rows, 0 cheap) x {c} quintile (cols, 0 low)\n", tab.to_string())
    gp = p.dropna(subset=["gauge"]).copy()
    gp["cq"] = gp.groupby("date")["gauge"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    m = gp.groupby(["date", "gq", "cq"])["ex20"].mean().unstack(["gq", "cq"])
    tab = m.mean().unstack("cq").round(2)
    tab.loc["t dear−cheap"] = pd.Series({k: tstat(m[(4, k)] - m[(0, k)]) for k in range(5)}).round(2)
    print(f"\n## (c) gap quintile x RetailGauge quintile (from {gp.date.min()}, {gp.date.nunique()} months)\n", tab.to_string())
    mom_hi = p.groupby("date")["mom"].rank(pct=True) > 0.7
    turn_hi = p.groupby("date")["turn"].rank(pct=True) > 0.7
    rev_lo = p.groupby("date")["rev20"].rank(pct=True) <= 0.3
    gauge_hi = p["gauge"] >= 0.7
    gauge_lo = p["gauge"] <= 0.3
    rules = {
        "avoid gi>0.9": p.gi > 0.9,
        "avoid gi>0.9 & mom top30%": (p.gi > 0.9) & mom_hi,
        "avoid gi>0.9 & turnover top30%": (p.gi > 0.9) & turn_hi,
        "avoid gi>0.9 & gauge>=0.7": (p.gi > 0.9) & gauge_hi,
        "avoid gi>0.8 & turnover top30%": (p.gi > 0.8) & turn_hi,
        "add gi<=0.1": p.gi <= 0.1,
        "add gi<=0.1 & rev20 bottom30%": (p.gi <= 0.1) & rev_lo,
        "add gi<=0.1 & turnover not top30%": (p.gi <= 0.1) & ~turn_hi,
        "add gi<=0.1 & gauge<=0.3": (p.gi <= 0.1) & gauge_lo,
        "add gi<=0.2 & gauge<=0.3": (p.gi <= 0.2) & gauge_lo,
    }
    rev_hi = p.groupby("date")["rev20"].rank(pct=True) > 0.8
    grow_hi = p.groupby("date")["grow"].rank(pct=True) > 0.6
    mom_lo = p.groupby("date")["mom"].rank(pct=True) <= 0.2
    rules |= {
        "avoid gi>0.8 & rev20 top20%": (p.gi > 0.8) & rev_hi,
        "add gi<=0.2 & growth top40%": (p.gi <= 0.2) & grow_hi,
        "add gi<=0.2 & growth top40% & mom not bottom20%": (p.gi <= 0.2) & grow_hi & ~mom_lo,
    }
    big = p.groupby("date")["size"].rank(pct=True) > 0.6
    print("large caps (top 40% size) median mv 亿:", round(float((np.exp(p.loc[big, "size"]) / 1e4).median())))
    for k in list(rules):
        rules[f"[large] {k}"] = rules[k] & big
    out = {k: dict(zip(["ex20%", "t", "hit", "n/month"], cell(p, v))) | {"ex60%": cell(p, v, "ex60")[0]} for k, v in rules.items()}
    print("\n## (d) rules (gauge rules from 2023 only)\n", pd.DataFrame(out).T.to_string())


if __name__ == "__main__":
    main()
