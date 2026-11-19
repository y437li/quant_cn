"""Short the high-CGO decile? (plan 29 follow-up, 2026-11-15). User: "用这个反过来买呗" -> "我的意思是要short".

From panel.parquet of cgo_ic.py. Each month-end, short the top 10% by CGO (raw, and net of controls) among:
all universe names, 融资融券 targets on that day (margin_secs), and targets with short interest outstanding (rqyl > 0,
a proxy for lendable stock). Return = minus the 20d excess over the universe mean (the hedge leg is the universe;
in practice CSI 1000 / IM futures). Costs: borrow 8% / yr on the short leg, one-way trading cost 0.15% x turnover.
Reported by year to see the 2024+ regime after 转融券 was suspended.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load().lake.root)
OUT = LAKE / "meta/runs/research/20261115_cgo_ic"
CTRL = ["size", "reversal_1m", "reversal_intraday_1m", "momentum_12_1", "turnover_60d"]
BORROW, COST = 0.08, 0.0015
pd.set_option("display.width", 240)


def src(t: str) -> str:
    return f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"


def residual(g: pd.DataFrame, x: str) -> pd.Series:
    g = g.dropna(subset=[x, *CTRL])
    v = g[x].rank().to_numpy()
    Z = g[CTRL].rank().to_numpy()
    Z = np.column_stack([(Z - Z.mean(0)) / Z.std(0), np.ones(len(g))])
    return pd.Series(v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0], index=g.index)


def run(E: pd.DataFrame, x: str, pool: pd.Series) -> tuple[dict[str, float], pd.Series]:
    sub = E[pool & E[x].notna() & E["y20"].notna()]
    top = sub[sub.groupby("d")[x].rank(pct=True) > 0.9]
    gross = -top.groupby("d")["y20"].mean()
    names = top.groupby("d")["ts_code"].apply(set)
    turn = [1.0] + [
        1 - len(a & b) / max(len(b), 1)
        for a, b in zip(names.iloc[:-1], names.iloc[1:], strict=True)
    ]
    net = gross - BORROW / 12 - 2 * COST * pd.Series(turn, index=gross.index)
    stats = {
        "n_short": top.groupby("d").size().mean(),
        "gross_ann_%": gross.mean() * 1200,
        "t_gross": gross.mean() / gross.std() * np.sqrt(len(gross)),
        "turnover": float(np.mean(turn[1:])),
        "net_ann_%": net.mean() * 1200,
        "t_net": net.mean() / net.std() * np.sqrt(len(net)),
        "hit_net": (net > 0).mean(),
        "worst_month_%": net.min() * 100,
    }
    return stats, net


def main() -> None:
    E = pd.read_parquet(OUT / "panel.parquet").reset_index()
    E["cgo_net"] = pd.concat([residual(g, "cgo_tri_a1.5") for _, g in E.groupby("d")])
    con = duckdb.connect()
    months = sorted(E["d"].unique())
    tg = con.sql(f"SELECT DISTINCT trade_date d, ts_code FROM {src('margin_secs')}").df()
    # margin_secs is not daily for every month-end: use the latest list on or before d
    lists = {d: set(g["ts_code"]) for d, g in tg.groupby("d")}
    keys = sorted(lists)
    E["target"] = [
        c in lists[k[-1]] if (k := [x for x in keys if x <= d]) else False
        for d, c in zip(E["d"], E["ts_code"], strict=True)
    ]
    sh = con.sql(
        f"SELECT trade_date d, ts_code FROM {src('margin_detail')} WHERE rqyl > 0 AND list_contains(?, trade_date)",
        params=[months],
    ).df()
    E = E.merge(sh.assign(lendable=True), on=["d", "ts_code"], how="left")
    E["lendable"] = E["lendable"].fillna(False).astype(bool)
    rows, nets = {}, {}
    for x in ("cgo_tri_a1.5", "cgo_net"):
        for pname, pool in (
            ("all", E["d"].notna()),
            ("两融标的", E["target"]),
            ("有融券余量", E["lendable"]),
        ):
            rows[(x, pname)], nets[(x, pname)] = run(E, x, pool)
    R = pd.DataFrame(rows).T
    R.to_csv(OUT / "short_side.csv")
    print(R.round(2).to_string())
    N = pd.DataFrame(nets)
    Y = N.groupby(N.index.str[:4]).mean() * 1200
    Y.to_csv(OUT / "short_side_by_year.csv")
    print("\nnet annualised % by year\n", Y.round(1).to_string())


if __name__ == "__main__":
    main()
