"""turnover_60d, pricing_gap and the RetailGauge against the Barra styles: per month OLS of each signal
on the 12 style exposures -> R2; rank IC (fwd20 / fwd60) of the raw signal and of its style residual.
Month ends 2023-01 .. 2026-10 (the gauge's history); turnover_60d and pricing_gap also 2019 .. 2026.
Large caps = top 40% market value."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from score_vs_barra import STYLES, tstat  # same folder
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
GAUGE = "meta/runs/research/20261117_gauge_daily/gauge_daily.parquet"


def load() -> pd.DataFrame:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: {h: days[min(days.index(d) + h, len(days) - 1)] for h in (20, 60)} for d in ends}
    f = q.sql("SELECT trade_date, ts_code, factor, value FROM derived.features WHERE trade_date IN (SELECT UNNEST(?)) "
              "AND factor IN ('turnover_60d', 'pricing_gap')", [ends])
    ex = q.sql("SELECT trade_date, ts_code, factor, exposure FROM derived.risk_exposure WHERE trade_date IN (SELECT UNNEST(?)) "
               "AND factor IN (SELECT UNNEST(?))", [ends, STYLES])
    mv = q.sql("SELECT trade_date, ts_code, total_mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    want = sorted(set(ends) | {v for d in nxt.values() for v in d.values()})
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [want])
    cat.close()
    m = (f.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="value").reset_index()
         .merge(ex.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="exposure").reset_index(), on=["trade_date", "ts_code"])
         .merge(mv, on=["trade_date", "ts_code"]))
    g = pd.read_parquet(Path(cfg.lake.root) / GAUGE)[["ts_code", "asof", "pct"]]
    g["k"] = g["asof"].astype(str).astype(int)
    m["k"] = m["trade_date"].astype(int)
    m = pd.merge_asof(m.sort_values("k"), g.sort_values("k")[["k", "ts_code", "pct"]], on="k", by="ts_code",
                      direction="backward", tolerance=40)
    m["gauge"] = -m["pct"]  # sign: higher = colder = expected better
    px = px.set_index(["trade_date", "ts_code"])["px"]
    for h in (20, 60):
        fwd = pd.Series([px.get((nxt[d][h], c), np.nan) / px.get((d, c), np.nan) - 1
                         for d, c in zip(m["trade_date"], m["ts_code"], strict=True)], index=m.index)
        m[f"ex{h}"] = (fwd - fwd.groupby(m["trade_date"]).transform("mean")) * 100
    return m.dropna(subset=[*STYLES, "ex20"])


def test(m: pd.DataFrame, col: str) -> dict[str, float]:
    d = m.dropna(subset=[col])
    r2, parts = [], []
    for _, f in d.groupby("trade_date"):
        X = np.column_stack([np.ones(len(f)), f[STYLES].to_numpy()])
        y = f[col].to_numpy()
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = y - X @ b
        r2.append(1 - res.var() / y.var())
        parts.append(f.assign(res=res))
    d = pd.concat(parts)
    out = {"R2": round(float(np.mean(r2)), 2), "months": d["trade_date"].nunique()}
    for c, lab in ((col, "raw"), ("res", "resid")):
        for h, step in ((20, 1), (60, 3)):
            ic = d.dropna(subset=[f"ex{h}"]).groupby("trade_date").apply(lambda x, cc=c, hh=h: x[cc].rank().corr(x[f"ex{hh}"].rank()))
            out[f"{lab} IC{h}"] = round(ic.mean(), 4)
            out[f"{lab} t{h}"] = round(tstat(ic, step), 2)
    return out


def main() -> None:
    m = load()
    big = m.groupby("trade_date")["total_mv"].rank(pct=True) > 0.6
    rows = {}
    for period, part in (("2019-26", m), ("2023-26", m[m["trade_date"] >= "20230101"])):
        for uni, sub in (("all", part), ("large", part[big.loc[part.index]])):
            for col in ("turnover_60d", "pricing_gap", "gauge"):
                if col == "gauge" and period == "2019-26":
                    continue
                rows[(period, uni, col)] = test(sub, col)
    pd.set_option("display.width", 220)
    print(pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    main()
