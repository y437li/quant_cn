"""Overlap of turnover_60d (score factor) and the RetailGauge (散户温度计), month ends 2023-01 .. 2026-10.
Gauge = latest reading on or before the month end (research run 20261117_gauge_daily). turnover_60d =
derived.features processed value (industry + size neutral; higher = lower turnover). fwd20 / fwd60 =
next 20 / 60 sessions, excess vs the month's mean. Tests: rank correlation; rank IC of each; Fama-MacBeth
with both; the gauge's hot decile split by turnover tercile; all stocks and large caps (top 40% mv)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
GAUGE = "meta/runs/research/20261117_gauge_daily/gauge_daily.parquet"


def tstat(s: pd.Series, step: int = 1) -> float:
    s = s.dropna().iloc[::step]
    return float(s.mean() / s.std() * np.sqrt(len(s)))


def load() -> pd.DataFrame:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20230101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: {h: days[min(days.index(d) + h, len(days) - 1)] for h in (20, 60)} for d in ends}
    f = q.sql("SELECT trade_date, ts_code, value AS turn FROM derived.features WHERE factor = 'turnover_60d' AND trade_date IN (SELECT UNNEST(?))", [ends])
    mv = q.sql("SELECT trade_date, ts_code, total_mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    want = sorted(set(ends) | {v for d in nxt.values() for v in d.values()})
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [want])
    cat.close()
    px = px.set_index(["trade_date", "ts_code"])["px"]
    g = pd.read_parquet(Path(cfg.lake.root) / GAUGE)[["ts_code", "asof", "pct"]]
    g["k"] = g["asof"].astype(str).astype(int)
    m = f.merge(mv, on=["trade_date", "ts_code"])
    m["k"] = m["trade_date"].astype(int)
    m = pd.merge_asof(m.sort_values("k"), g.sort_values("k")[["k", "ts_code", "pct"]], on="k", by="ts_code",
                      direction="backward", tolerance=40).rename(columns={"pct": "gauge"})
    for h in (20, 60):
        fwd = [px.get((nxt[d][h], c), np.nan) / px.get((d, c), np.nan) - 1 for d, c in zip(m["trade_date"], m["ts_code"], strict=True)]
        m[f"ex{h}"] = (pd.Series(fwd, index=m.index) - pd.Series(fwd, index=m.index).groupby(m["trade_date"]).transform("mean")) * 100
    m = m[m["trade_date"].map(lambda d: nxt[d][20]) > m["trade_date"]]
    return m.dropna(subset=["gauge", "turn", "ex20"])


def summarise(m: pd.DataFrame, label: str) -> None:
    print(f"\n######## {label}: {m['trade_date'].nunique()} months, median {int(m.groupby('trade_date').size().median())} stocks")
    rc = m.groupby("trade_date").apply(lambda f: f["turn"].rank().corr(f["gauge"].rank()))
    print(f"rank corr(turnover_60d score, gauge) {rc.mean():.2f}  (turnover score is high for LOW turnover)")
    for col in ("turn", "gauge"):
        for h, step in ((20, 1), (60, 3)):
            ic = m.dropna(subset=[f"ex{h}"]).groupby("trade_date").apply(lambda f, c=col, hh=h: f[c].rank().corr(f[f"ex{hh}"].rank()))
            print(f"  IC {col:5s} fwd{h}: {ic.mean():+.4f} (t {tstat(ic, step):.2f})")
    fm = {"turn": [], "gauge": []}
    for _, f in m.groupby("trade_date"):
        X = np.column_stack([np.ones(len(f)), f["turn"].rank(pct=True) - 0.5, f["gauge"].rank(pct=True) - 0.5])
        b = np.linalg.lstsq(X, f["ex20"].rank(pct=True) - 0.5, rcond=None)[0]
        fm["turn"].append(b[1])
        fm["gauge"].append(b[2])
    print("  FM fwd20 both together:", {k: f"{np.mean(v):+.4f} (t {tstat(pd.Series(v)):.2f})" for k, v in fm.items()})
    m = m.copy()
    m["hot"] = m["gauge"] >= 0.9
    m["tt"] = m.groupby("trade_date")["turn"].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=["high turnover", "mid", "low turnover"]))
    tab = m.groupby(["tt", "hot"], observed=True)["ex20"].mean().unstack().round(2)
    tab.columns = ["gauge < 0.9", "gauge >= 0.9 (hot)"]
    tab["n hot/month"] = (m[m["hot"]].groupby("tt", observed=True).size() / m["trade_date"].nunique()).round(0)
    print("  fwd20 excess % by turnover tercile x gauge hot\n", tab.to_string())


def main() -> None:
    m = load()
    pd.set_option("display.width", 200)
    summarise(m, "all")
    summarise(m[m.groupby("trade_date")["total_mv"].rank(pct=True) > 0.6], "large caps")


if __name__ == "__main__":
    main()
