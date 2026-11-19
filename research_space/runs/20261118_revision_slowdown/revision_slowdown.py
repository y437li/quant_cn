"""Is a slowdown of consensus upgrades a signal? Month ends 2019-01 .. 2026-10.

Consensus per month end (ConsensusPanelBuilder, 90-day window, latest note per broker, notes
visible the session after report_date). Fixed fiscal year y = FY1 + 1 at t (FY2), its forecast at
t, t-1m, t-2m, t-3m wherever it sits (FY1..FY3). rev1 = np(t)/np(t-1m) - 1, rev1_prev = the month
before, accel = rev1 - rev1_prev, rev3 = np(t)/np(t-3m) - 1; positive forecasts, >= 3 brokers.
Forward 20 / 60-session returns from the 20261118_linear_pricing_gap panel (excess vs the panel mean).
Tests: monthly rank IC of rev3 / rev1 / accel; among the top quintile of rev3 (strong upgrades):
still accelerating vs slowing (accel < 0) vs stalled (rev1 <= 0); the same among large caps.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.calculation.consensus_panel_builder import ConsensusPanelBuilder
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
PANEL = "meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet"


def tstat(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.mean() / s.std() * np.sqrt(len(s)))


def build_long(cons: pd.DataFrame) -> pd.DataFrame:
    parts = [cons[["trade_date", "ts_code"]].assign(fy=cons["fy1"] + k, np=cons[f"np{k + 1}"]) for k in range(3)]
    return pd.concat(parts).dropna(subset=["np"])


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20180901' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    cons = ConsensusPanelBuilder(q, DateCodec()).build(ends, 90)
    cat.close()
    long = build_long(cons).set_index(["trade_date", "ts_code", "fy"])["np"]
    rows = []
    for i in range(3, len(ends)):
        t = ends[i]
        now = cons[(cons["trade_date"] == t) & (cons["n_brokers"] >= 3)]
        y = int(ConsensusPanelBuilder.get_fy1(t)) + 1
        frame = pd.DataFrame({"ts_code": now["ts_code"].to_numpy()})
        for k in range(4):
            idx = pd.MultiIndex.from_arrays([[ends[i - k]] * len(frame), frame["ts_code"], [y] * len(frame)])
            frame[f"np{k}"] = long.reindex(idx).to_numpy()
        frame["date"] = t
        rows.append(frame)
    s = pd.concat(rows, ignore_index=True)
    s = s[(s[["np0", "np1", "np2", "np3"]] > 0).all(axis=1)].copy()
    s["rev1"] = s["np0"] / s["np1"] - 1
    s["rev1_prev"] = s["np1"] / s["np2"] - 1
    s["rev3"] = s["np0"] / s["np3"] - 1
    s["accel"] = s["rev1"] - s["rev1_prev"]
    panel = pd.read_parquet(Path(cfg.lake.root) / PANEL)[["date", "ts_code", "fwd20", "fwd60", "size"]]
    s = s.merge(panel, on=["date", "ts_code"])
    for h in (20, 60):
        r = np.exp(s[f"fwd{h}"])
        s[f"ex{h}"] = (r - r.groupby(s["date"]).transform("mean")) * 100
    print(f"{s['date'].nunique()} months, median {int(s.groupby('date').size().median())} stocks (>= 3 brokers)")
    for col in ("rev3", "rev1", "accel"):
        out = []
        for h in (20, 60):
            sub = s.dropna(subset=[f"ex{h}"])
            ic = sub.groupby("date").apply(lambda f: f[col].rank().corr(f[f"ex{h}"].rank()))
            step = 1 if h == 20 else 3
            out.append(f"fwd{h} IC {ic.mean():.4f} (t {tstat(ic.iloc[::step]):.2f})")
        print(f"{col}: " + "; ".join(out))
    for label, part in (("all", s), ("large caps (top 40% size)", s[s.groupby("date")["size"].rank(pct=True) > 0.6])):
        part = part.copy()
        part["top"] = part.groupby("date")["rev3"].rank(pct=True) > 0.8
        top = part[part["top"]]
        groups = {"top-quintile upgrades: all": top,
                  "  still accelerating (accel > 0)": top[top["accel"] > 0],
                  "  slowing (accel < 0, rev1 > 0)": top[(top["accel"] < 0) & (top["rev1"] > 0)],
                  "  stalled (rev1 <= 0)": top[top["rev1"] <= 0]}
        print(f"\n## {label}")
        for g, d in groups.items():
            m20 = d.groupby("date")["ex20"].mean()
            m60 = d.dropna(subset=["ex60"]).groupby("date")["ex60"].mean()
            print(f"{g:36s} n/m {len(d) / part['date'].nunique():5.0f}  ex20 {m20.mean():+.2f}% (t {tstat(m20):.2f})  "
                  f"ex60 {m60.mean():+.2f}% (t {tstat(m60.iloc[::3]):.2f})")
        acc = top[top["accel"] > 0].groupby("date")["ex20"].mean()
        slow = top[(top["accel"] < 0) & (top["rev1"] > 0)].groupby("date")["ex20"].mean()
        d = (slow - acc).dropna()
        print(f"  slowing - accelerating fwd20: {d.mean():+.2f}%/m (t {tstat(d):.2f})")
    out = Path(cfg.lake.root) / "meta/runs/research/20261118_revision_slowdown"
    out.mkdir(parents=True, exist_ok=True)
    s.to_parquet(out / "revisions.parquet")


if __name__ == "__main__":
    main()
