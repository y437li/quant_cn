"""Can we reproduce Tushare cyq_perf with a turnover-decay chip model? (plan 29 ph1a, 2026-11-15).

User: "可以，写个计划，先在A股算CGO验证" -> "先考虑能不能复现".

Model per stock on the backward-adjusted (hfq) price, a log grid of B bins between its history min and max:
    chips_t = chips_{t-1} * (1 - a*V_t) + a*V_t * day_t,   V_t = turnover / 100
day_t spreads the session's volume over [low, high]: triangular peaking at the VWAP (amount / vol), uniform, or all
at the close. Suspended sessions are skipped. Winner rate = share of chips at or below the close; cost percentiles
and the mean cost are read off the cumulative distribution.

Match against cyq_perf from 2021 on a random sample (seed 0) of stocks listed before 2019:
- winner_rate: time-series corr and MAE per stock, cross-sectional Spearman per day;
- shape ratios (cost_5 / cost_50 / cost_95 over weight_avg), scale-free;
- price basis of the vendor costs: weight_avg vs our mean cost in qfq-to-t and in qfq-to-latest terms.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

OUT = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_cgo_reproduce")
OUT.mkdir(parents=True, exist_ok=True)
N_STOCKS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
B = 400
START, MATCH = "20100101", "20210101"
VARIANTS = {
    "tri_vwap_float": ("tri", "turnover_rate", 1.0),
    "uni_float": ("uni", "turnover_rate", 1.0),
    "close_float": ("close", "turnover_rate", 1.0),
    "tri_vwap_free": ("tri", "turnover_rate_f", 1.0),
    "tri_vwap_float_a0.5": ("tri", "turnover_rate", 0.5),
    "tri_vwap_free_a1.5": ("tri", "turnover_rate_f", 1.5),
    "tri_vwap_free_a2": ("tri", "turnover_rate_f", 2.0),
    "tri_vwap_free_a3": ("tri", "turnover_rate_f", 3.0),
    "uni_free_a2": ("uni", "turnover_rate_f", 2.0),
}
ONLY = sys.argv[2].split(",") if len(sys.argv) > 2 else list(VARIANTS)
pd.set_option("display.width", 240)


def load(q: LakeQuery) -> tuple[pd.DataFrame, pd.DataFrame]:
    codes = q.sql(
        """SELECT ts_code FROM curated.cyq_perf WHERE trade_date = '20210104'
           INTERSECT SELECT ts_code FROM curated.daily WHERE trade_date < '20190101' GROUP BY 1"""
    )["ts_code"].sort_values()
    codes = list(codes.sample(min(N_STOCKS, len(codes)), random_state=0))
    d = q.sql(
        """SELECT d.ts_code, d.trade_date, d.high, d.low, d.close, d.vol, d.amount, a.adj_factor,
                  b.turnover_rate, b.turnover_rate_f
           FROM curated.daily d JOIN curated.adj_factor a USING (ts_code, trade_date)
           LEFT JOIN curated.daily_basic b USING (ts_code, trade_date)
           WHERE list_contains(?, d.ts_code) AND d.trade_date >= ? ORDER BY 2, 1""",
        [codes, START],
    )
    v = q.sql(
        """SELECT ts_code, trade_date, cost_5pct, cost_50pct, cost_95pct, weight_avg, winner_rate
           FROM curated.cyq_perf WHERE list_contains(?, ts_code) AND trade_date >= ?""",
        [codes, MATCH],
    )
    return d, v


def run(
    d: pd.DataFrame, shape: str, tcol: str, alpha: float, step: pd.Series | None = None
) -> pd.DataFrame:
    """step: vendor grid step per stock in hfq units (linear grid anchored at 0), for bin-edge winner rates."""
    d = d.copy()
    f = d["adj_factor"]
    d["H"], d["L"], d["C"] = d["high"] * f, d["low"] * f, d["close"] * f
    d["M"] = (d["amount"] * 10 / d["vol"]).where(d["vol"] > 0) * f  # amount in 千元, vol in 手
    d["M"] = d["M"].clip(d["L"], d["H"]).fillna(d["C"])
    codes = sorted(d["ts_code"].unique())
    ix = {c: i for i, c in enumerate(codes)}
    lo = np.log(d.groupby("ts_code")["L"].min().reindex(codes).to_numpy() * 0.98)
    hi = np.log(d.groupby("ts_code")["H"].max().reindex(codes).to_numpy() * 1.02)
    grid = np.exp(lo[:, None] + (hi - lo)[:, None] * np.linspace(0, 1, B)[None, :])
    chips = np.zeros((len(codes), B))
    last = (
        d.sort_values("trade_date")
        .groupby("ts_code")["adj_factor"]
        .last()
        .reindex(codes)
        .to_numpy()
    )
    rows = []
    for day, g in d.groupby("trade_date", sort=True):
        g = g[g[tcol].notna() & (g["vol"] > 0)]
        if g.empty:
            continue
        i = g["ts_code"].map(ix).to_numpy()
        p = grid[i]
        L, H, M, C = (g[k].to_numpy()[:, None] for k in ("L", "H", "M", "C"))
        if shape == "tri":
            w = np.where(
                p <= M, (p - L) / np.maximum(M - L, 1e-12), (H - p) / np.maximum(H - M, 1e-12)
            )
            w = np.clip(w, 0, None) * ((p >= L) & (p <= H))
        elif shape == "uni":
            w = ((p >= L) & (p <= H)).astype(float)
        else:
            w = np.zeros_like(p)
        empty = w.sum(1) <= 0
        if (
            empty.any()
        ):  # range narrower than a bin, or the close variant: all at the nearest bin to the close
            near = np.abs(np.log(p[empty]) - np.log(C[empty])).argmin(1)
            w[empty] = 0.0
            w[empty, near] = 1.0
        w /= w.sum(1, keepdims=True)
        v = np.clip(alpha * g[tcol].to_numpy() / 100.0, 0, 1)[:, None]
        new = chips[i] * (1 - v) + v * w
        new /= new.sum(1, keepdims=True)
        chips[i] = new
        if day < MATCH:
            continue
        cum = new.cumsum(1)
        win = (new * (p <= C)).sum(1)
        sh = (step.reindex(g["ts_code"]).to_numpy() if step is not None else C[:, 0] * 0 + np.nan)[
            :, None
        ]
        up, dn = np.ceil(C / sh) * sh, np.floor(C / sh) * sh
        win_up, win_dn = (new * (p <= up)).sum(1), (new * (p <= dn)).sum(1)
        win_mid = (new * (p <= (np.floor(C / sh) + 0.5) * sh)).sum(1)
        win_rnd = (new * (np.round(p / sh) * sh <= C)).sum(1)
        raw_up = (
            C * (last[i] / g["adj_factor"].to_numpy())[:, None]
        )  # raw close in latest-basis hfq units
        win_raw = (new * (np.round(p / sh) * sh <= raw_up)).sum(1)
        q = {k: p[np.arange(len(i)), (cum >= k / 100).argmax(1)] for k in (5, 50, 95)}
        rows.append(
            pd.DataFrame(
                {
                    "ts_code": g["ts_code"].to_numpy(),
                    "trade_date": day,
                    "win": win * 100,
                    "win_up": win_up * 100,
                    "win_dn": win_dn * 100,
                    "win_mid": win_mid * 100,
                    "win_rnd": win_rnd * 100,
                    "win_raw": win_raw * 100,
                    "c5": q[5],
                    "c50": q[50],
                    "c95": q[95],
                    "avg": (new * p).sum(1),
                    "close_hfq": C[:, 0],
                    "adj": g["adj_factor"].to_numpy(),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def infer_step(v: pd.DataFrame) -> pd.Series:
    """Vendor grid step per stock: gcd of the cost levels it reported in 2021-2025 (one backfill basis)."""
    cols = ["cost_5pct", "cost_50pct", "cost_95pct"]
    old = v[v["trade_date"] < "20260101"]

    def gcd(z: pd.DataFrame) -> float:
        x = np.unique(np.round(z[cols].to_numpy().ravel() * 100).astype(np.int64))
        return float(np.gcd.reduce(x[x > 0])) / 100

    return old.groupby("ts_code").apply(gcd, include_groups=False)


def score(ours: pd.DataFrame, vendor: pd.DataFrame, latest_adj: pd.Series) -> dict[str, float]:
    m = ours.merge(vendor, on=["ts_code", "trade_date"])
    m["err"] = m["win"] - m["winner_rate"]
    ts = m.groupby("ts_code").apply(lambda z: z["win"].corr(z["winner_rate"]), include_groups=False)
    xs = m.groupby("trade_date").apply(
        lambda z: z["win"].rank().corr(z["winner_rate"].rank()), include_groups=False
    )
    out = {
        "n_rows": len(m),
        "win_mae_pp": m["err"].abs().mean(),
        "win_bias_pp": m["err"].mean(),
        "win_ts_corr_median": ts.median(),
        "win_xs_spearman_median": xs.median(),
    }
    for k in ("win_up", "win_dn", "win_mid", "win_rnd", "win_raw"):
        e = (m[k] - m["winner_rate"])[m["trade_date"] < "20260101"]
        out[f"{k}_mae_pp"], out[f"{k}_bias_pp"] = e.abs().mean(), e.mean()
    for k in ("c5", "c50", "c95"):
        ours_r, vend_r = m[k] / m["avg"], m[f"cost_{k[1:]}pct"] / m["weight_avg"]
        out[f"{k}_over_avg_mae"] = (ours_r - vend_r).abs().median()
    to_t = m["avg"] / m["adj"]
    to_last = m["avg"] / m["ts_code"].map(latest_adj)
    out["avg_logerr_qfq_t"] = np.log(to_t / m["weight_avg"]).abs().median()
    out["avg_logerr_qfq_latest"] = np.log(to_last / m["weight_avg"]).abs().median()
    m.to_parquet(OUT / "last_variant_rows.parquet")
    return out


def main() -> None:
    cfg = Config.load()
    q = LakeQuery(LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True))
    d, v = load(q)
    latest_adj = d.sort_values("trade_date").groupby("ts_code")["adj_factor"].last()
    step = (
        infer_step(v) * latest_adj
    )  # vendor grid (qfq to the backfill date ~ latest) in hfq units
    print(f"{d['ts_code'].nunique()} stocks, {len(d):,} bars, {len(v):,} vendor rows")
    res = {}
    for name in ONLY:
        shape, tcol, alpha = VARIANTS[name]
        ours = run(d, shape, tcol, alpha, step)
        res[name] = score(ours, v, latest_adj)
        ours.to_parquet(OUT / f"ours_{name}.parquet")
        print(name, {k: round(x, 4) for k, x in res[name].items()}, flush=True)
    table = pd.DataFrame(res).T
    table.to_csv(OUT / "match.csv")
    print(table.round(3))


if __name__ == "__main__":
    main()
