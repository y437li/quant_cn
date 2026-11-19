"""Does capital gains overhang (CGO, 筹码浮盈) predict A-share returns? (plan 29 ph1b, 2026-11-15).

User: "可以，写个计划，先在A股算CGO验证" -> "先考虑能不能复现" -> "ok" (plan approved).

Mean chip cost per stock by the turnover-decay recursion (Grinblatt & Han 2005 reference price) on hfq prices:
    RP_t = RP_{t-1} * (1 - a*V_t) + a*V_t * m_t,   V_t = turnover_rate_f / 100,   CGO_t = 1 - RP_t / C_t
m_t = mean of the session's volume spread: triangular on [low, high] at the VWAP -> (L + H + VWAP) / 3, or the close.
Recursion from 2010 (no truncation; the plan's N in {250, 500} is replaced by a, the same memory knob).
Winner rate (our 400-bin model, the 20261115_cgo_reproduce best variant) and the vendor cyq_perf winner_rate (2021+)
are tested beside it.

Test: month-end signal 2019-01..2026-10, universe = derived/universe, entry open(t+1), exit close(t+H), excess =
minus the cross-sectional mean. Rank IC per month, raw and net of size (log circ_mv), reversal_1m,
reversal_intraday_1m (plan 25 formula), momentum_12_1 and turnover_60d (rank regression residual). Newey-West t with
ceil(H/20) lags. Sub-periods 2019-21 / 2022-23 / 2024-26. Pre-chosen variant (plan 29 bar): cgo_tri_a1.5, net,
H = 20: NW t >= 3 and the same sign in all three sub-periods.
"""

from __future__ import annotations

import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load().lake.root)
OUT = LAKE / "meta/runs/research/20261115_cgo_ic"
OUT.mkdir(parents=True, exist_ok=True)
START, TEST = "20100101", "20190101"
B, W, TOP = 400, 21, 10
HS = (20, 60)
PRE = "cgo_tri_a1.5"
CTRL = ["size", "reversal_1m", "reversal_intraday_1m", "momentum_12_1", "turnover_60d"]
SUBS = (
    ("2019-21", "20190101", "20211231"),
    ("2022-23", "20220101", "20231231"),
    ("2024-26", "20240101", "20261231"),
)
pd.set_option("display.width", 240)


def src(t: str) -> str:
    return f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"


def load(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    px = con.sql(
        f"""SELECT d.ts_code, d.trade_date, d.open * a.adj_factor AS o, d.high * a.adj_factor AS h,
                   d.low * a.adj_factor AS l, d.close * a.adj_factor AS c,
                   CASE WHEN d.vol > 0 THEN d.amount * 10 / d.vol * a.adj_factor END AS m,
                   b.turnover_rate_f AS tv, b.circ_mv AS mv
            FROM {src("curated/daily")} d JOIN {src("curated/adj_factor")} a USING (ts_code, trade_date)
            LEFT JOIN {src("curated/daily_basic")} b USING (ts_code, trade_date)
            WHERE d.trade_date >= '{START}'"""
    ).df()
    out = {
        k: px.pivot(index="trade_date", columns="ts_code", values=k).sort_index().astype("float32")
        for k in ("o", "h", "l", "c", "m", "tv", "mv")
    }
    out["m"] = out["m"].clip(out["l"], out["h"]).fillna(out["c"])
    return out


def mean_cost(P: dict[str, pd.DataFrame], shape: str, alpha: float) -> pd.DataFrame:
    m = (P["l"] + P["h"] + P["m"]) / 3 if shape == "tri" else P["c"]
    v = np.clip(alpha * P["tv"].to_numpy() / 100, 0, 1)
    mm = m.to_numpy()
    rp = np.full(mm.shape[1], np.nan, dtype="float64")
    out = np.full(mm.shape, np.nan, dtype="float32")
    for t in range(len(mm)):
        ok = ~np.isnan(v[t]) & ~np.isnan(mm[t])
        first = ok & np.isnan(rp)
        rp[first] = mm[t][first]
        upd = ok & ~first
        rp[upd] = rp[upd] * (1 - v[t][upd]) + v[t][upd] * mm[t][upd]
        out[t] = rp
    return pd.DataFrame(out, index=m.index, columns=m.columns)


def winner(P: dict[str, pd.DataFrame], alpha: float, keep: list[str]) -> pd.DataFrame:
    """Share of chips at or below the close on a 400-bin log grid (triangular at the VWAP); rows `keep` only."""
    L, H, M, C, V = (P[k].to_numpy(dtype="float64") for k in ("l", "h", "m", "c", "tv"))
    lo = np.log(np.nanmin(L, 0) * 0.98)
    hi = np.log(np.nanmax(H, 0) * 1.02)
    grid = np.exp(lo[:, None] + (hi - lo)[:, None] * np.linspace(0, 1, B)[None, :])
    chips = np.zeros((L.shape[1], B))
    keep_ix = set(np.flatnonzero(P["c"].index.isin(keep)))
    rows = {}
    for t in range(len(L)):
        i = np.flatnonzero(~np.isnan(V[t]) & ~np.isnan(C[t]) & ~np.isnan(L[t]))
        if len(i):
            p = grid[i]
            lo_, hi_, m_ = L[t, i, None], H[t, i, None], M[t, i, None]
            w = np.where(
                p <= m_,
                (p - lo_) / np.maximum(m_ - lo_, 1e-12),
                (hi_ - p) / np.maximum(hi_ - m_, 1e-12),
            )
            w = np.clip(w, 0, None) * ((p >= lo_) & (p <= hi_))
            empty = w.sum(1) <= 0
            if empty.any():
                near = np.abs(np.log(p[empty]) - np.log(C[t, i[empty], None])).argmin(1)
                w[empty] = 0.0
                w[empty, near] = 1.0
            w /= w.sum(1, keepdims=True)
            v = np.clip(alpha * V[t, i] / 100, 0, 1)[:, None]
            new = chips[i] * (1 - v) + v * w
            chips[i] = new / new.sum(1, keepdims=True)
        if t in keep_ix:
            rows[P["c"].index[t]] = (chips * (grid <= C[t][:, None])).sum(1) / np.where(
                chips.sum(1) > 0, 1, np.nan
            )
    return pd.DataFrame(rows, index=P["c"].columns).T


def intraday_reversal(P: dict[str, pd.DataFrame], days: list[str]) -> pd.DataFrame:
    intra = np.log(P["c"] / P["o"])
    idx = P["c"].index
    out = {}
    for d in days:
        i = idx.get_loc(d)
        win = idx[i - W + 1 : i + 1]
        tv = P["tv"].loc[win]
        top = tv.rank(axis=0, ascending=False, method="first") <= TOP
        val = -intra.loc[win].where(top).sum()
        out[d] = val.where(tv.notna().sum() >= 15)
    return pd.DataFrame(out).T


def nw_t(s: pd.Series, lags: int) -> float:
    x = s.to_numpy() - s.mean()
    n = len(x)
    var = (x @ x) / n
    for k in range(1, lags + 1):
        var += 2 * (1 - k / (lags + 1)) * (x[k:] @ x[:-k]) / n
    return float(s.mean() / math.sqrt(var / n))


def rank_ic(g: pd.DataFrame, x: str, y: str, ctrl: list[str]) -> float:
    g = g.dropna(subset=[x, y, *ctrl])
    if len(g) < 100:
        return float("nan")
    v = g[x].rank().to_numpy()
    if ctrl:
        Z = g[ctrl].rank().to_numpy()
        Z = np.column_stack([(Z - Z.mean(0)) / Z.std(0), np.ones(len(g))])
        v = v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
    return float(pd.Series(v).corr(g[y].rank().reset_index(drop=True)))


def main() -> None:
    con = duckdb.connect()
    P = load(con)
    idx = P["c"].index
    months = [d for d in pd.Series(idx, index=idx).groupby(idx.str[:6]).last() if d >= TEST][:-1]
    print(f"{P['c'].shape[1]} stocks, {len(idx)} sessions, {len(months)} month-ends", flush=True)
    sig: dict[str, pd.DataFrame] = {}
    for shape in ("tri", "close"):
        for a in (1.0, 1.5):
            rp = mean_cost(P, shape, a)
            sig[f"cgo_{shape}_a{a:g}"] = (1 - rp / P["c"]).loc[months]
    sig["abs_cgo"] = sig[PRE].abs()
    sig["winner_ours"] = winner(P, 1.5, months)
    print("signals done", flush=True)
    vend = con.sql(
        f"SELECT trade_date, ts_code, winner_rate FROM {src('curated/cyq_perf')} WHERE list_contains(?, trade_date)",
        params=[months],
    ).df()
    sig["winner_vendor"] = vend.pivot(index="trade_date", columns="ts_code", values="winner_rate")
    feats = con.sql(
        f"""SELECT trade_date, ts_code, factor, value_raw FROM {src("derived/features")}
            WHERE factor IN ('reversal_1m', 'momentum_12_1', 'turnover_60d') AND list_contains(?, trade_date)""",
        params=[months],
    ).df()
    ctl = {
        f: g.pivot(index="trade_date", columns="ts_code", values="value_raw")
        for f, g in feats.groupby("factor")
    }
    ctl["size"] = np.log(P["mv"].loc[months])
    ctl["reversal_intraday_1m"] = intraday_reversal(P, months)
    uni = con.sql(
        f"SELECT trade_date, ts_code FROM {src('derived/universe')} WHERE in_universe AND list_contains(?, trade_date)",
        params=[months],
    ).df()
    fwd = {h: P["c"].shift(-h) / P["o"].shift(-1) - 1 for h in HS}
    frames = []
    for d in months:
        codes = uni.loc[uni["trade_date"] == d, "ts_code"]
        f = pd.DataFrame(index=pd.Index(codes, name="ts_code"))
        for k, s in (sig | ctl).items():
            f[k] = s.loc[d].reindex(f.index) if d in s.index else np.nan
        for h in HS:
            y = fwd[h].loc[d].reindex(f.index)
            f[f"y{h}"] = y - y.mean()
        f["d"] = d
        frames.append(f)
    E = pd.concat(frames)
    E.to_parquet(OUT / "panel.parquet")
    rows = []
    for x in sig:
        for cname, ctrl in (("raw", []), ("net", CTRL)):
            for h in HS:
                s = (
                    E.groupby("d")
                    .apply(lambda g: rank_ic(g, x, f"y{h}", ctrl), include_groups=False)
                    .dropna()
                )
                rec = {"signal": x, "ctrl": cname, "H": h, "months": len(s), "IC": s.mean()}
                rec["NW_t"] = nw_t(s, math.ceil(h / 20))
                for name, a, b in SUBS:
                    z = s[(s.index >= a) & (s.index <= b)]
                    rec[name] = z.mean()
                    rec[f"t_{name}"] = nw_t(z, math.ceil(h / 20)) if len(z) > 3 else np.nan
                rows.append(rec)
                print(x, cname, h, round(rec["IC"], 4), round(rec["NW_t"], 2), flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "ic.csv", index=False)
    print(R.round(3).to_string(index=False))
    dec = E.dropna(subset=[PRE, "y20"]).copy()
    dec["q"] = dec.groupby("d")[PRE].transform(
        lambda z: pd.qcut(z.rank(method="first"), 10, labels=False)
    )
    D = dec.groupby(["d", "q"])["y20"].mean().unstack().mean() * 100
    D.to_csv(OUT / "deciles_20d.csv")
    print("\n20d excess by CGO decile (%, 0 = deepest loss):", D.round(2).to_dict())
    keys = [PRE, "winner_ours", "winner_vendor", *CTRL]
    C = (
        E[keys]
        .groupby(E["d"])
        .rank(pct=True)
        .groupby(E["d"])
        .corr()
        .groupby(level=1)
        .mean()
        .loc[keys, keys]
    )
    C.to_csv(OUT / "corr.csv")
    print("\nmean cross-sectional rank corr\n", C.round(2).to_string())


if __name__ == "__main__":
    main()
