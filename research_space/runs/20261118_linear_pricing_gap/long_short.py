"""Long-short of the linear-pricing gap, monthly (month end to next month end ~ fwd20 sessions).

Legs, equal weight: raw deciles (cheapest − dearest); industry-neutral (within SW L1: bottom 10% −
top 10% of the gap rank); industry-neutral with the long leg excluding FY1 consensus cut > 10% over
90 days (same FY1 in both windows). Excess vs the covered universe. Stats: annualised mean, vol,
Sharpe, max drawdown, hit rate, by year, name turnover, net of 0.3% per unit of turnover per leg.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
COST = 0.003
_FY1 = """
WITH l AS (SELECT ts_code, org_name, arg_max(np, report_date) AS np FROM curated.report_rc
           WHERE report_date > ? AND report_date <= ? AND quarter = ? AND np IS NOT NULL GROUP BY 1, 2)
SELECT ts_code, median(np) AS np FROM l GROUP BY 1
"""


def add_revision(q: LakeQuery, p: pd.DataFrame) -> pd.DataFrame:
    out = []
    for d, f in p.groupby("date"):
        y, m = int(d[:4]), int(d[4:6])
        fy1 = y if m >= 5 else y - 1
        t = pd.Timestamp(d)
        before = (t - pd.Timedelta(days=90)).strftime("%Y%m%d")
        fy_before = int(before[:4]) if int(before[4:6]) >= 5 else int(before[:4]) - 1
        if fy_before != fy1:
            out.append(f.assign(rev=np.nan))
            continue
        old = q.sql(_FY1, [(t - pd.Timedelta(days=180)).strftime("%Y%m%d"), before, f"{fy1}Q4"]).set_index("ts_code")["np"]
        f = f.assign(rev=(f["f1"] / f["ts_code"].map(old) - 1).where(f["ts_code"].map(old) > 0))
        out.append(f)
    return pd.concat(out)


def stats(r: pd.Series) -> dict[str, float]:
    r = r.dropna() / 100
    nav = (1 + r).cumprod()
    return {"ann%": round(((1 + r).prod() ** (12 / len(r)) - 1) * 100, 1), "vol%": round(r.std() * np.sqrt(12) * 100, 1),
            "sharpe": round(r.mean() / r.std() * np.sqrt(12), 2), "maxDD%": round((nav / nav.cummax() - 1).min() * 100, 1),
            "hit": round((r > 0).mean(), 2), "months": len(r)}


def get_turnover(sel: pd.DataFrame) -> float:
    sets = sel.groupby("date")["ts_code"].apply(set).sort_index()
    ch = [1 - len(a & b) / max(len(b), 1) for a, b in zip(sets.iloc[:-1], sets.iloc[1:])]
    return float(np.mean(ch))


def main() -> None:
    cfg = Config.load(REPO)
    p = pd.read_parquet(Path(cfg.lake.root) / "meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet")
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    mem = q.sql("SELECT DISTINCT ts_code, l1_name FROM curated.index_member_all WHERE is_new = 'Y'")
    p = add_revision(q, p.dropna(subset=["fwd20"]))
    cat.close()
    p = p.merge(mem, on="ts_code", how="left")
    p["ex"] = (np.exp(p["fwd20"]) - np.exp(p["fwd20"]).groupby(p["date"]).transform("mean")) * 100
    p["dec"] = p.groupby("date")["gap"].transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
    p["gi"] = p.groupby(["date", "l1_name"])["gap"].rank(pct=True)
    legs = {
        "raw": (p[p.dec == 0], p[p.dec == 9]),
        "ind_neutral": (p[p.gi <= 0.1], p[p.gi > 0.9]),
        "ind_neutral+rev": (p[(p.gi <= 0.1) & ~(p.rev < -0.10)], p[p.gi > 0.9]),
    }
    rows, yearly = {}, {}
    for name, (lo, hi) in legs.items():
        L, S = lo.groupby("date")["ex"].mean(), hi.groupby("date")["ex"].mean()
        tl, ts = get_turnover(lo), get_turnover(hi)
        ls = L - S
        net = ls - (tl + ts) * COST * 100
        for k, s in ((f"{name} long", L), (f"{name} short", -S), (f"{name} L-S", ls), (f"{name} L-S net", net)):
            rows[k] = stats(s)
        rows[f"{name} L-S"]["turnover"] = round((tl + ts) / 2, 2)
        yearly[name] = ((1 + ls / 100).groupby(ls.index.str[:4]).prod() - 1).mul(100).round(1)
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).T.to_string())
    print("\n## long-short compounded by year (%)\n", pd.DataFrame(yearly).to_string())
    print("\nrevision available share", round(p["rev"].notna().mean(), 2), "; cut > 10% share", round((p["rev"] < -0.1).mean(), 3))


if __name__ == "__main__":
    main()
