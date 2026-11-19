"""Can the CGO findings be bought long-only? (plan 29 follow-up, 2026-11-15). User: "用这个反过来买呗".

From panel.parquet of cgo_ic.py (month-ends 2019-01..2026-10, derived/universe, entry open t+1):
1. deciles of CGO and |CGO|, raw and as residuals net of the five controls: mean 20d / 60d excess;
2. long-only books (equal weight, monthly, 20d holding): low-|CGO| 20%, low-CGO 20%, and the existing score top 20%
   with and without the high-|CGO| 20% removed; excess over the universe mean, annualised, t, hit rate.
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
pd.set_option("display.width", 240)


def residual(g: pd.DataFrame, x: str) -> pd.Series:
    g = g.dropna(subset=[x, *CTRL])
    v = g[x].rank().to_numpy()
    Z = g[CTRL].rank().to_numpy()
    Z = np.column_stack([(Z - Z.mean(0)) / Z.std(0), np.ones(len(g))])
    return pd.Series(v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0], index=g.index)


def deciles(E: pd.DataFrame, x: str) -> pd.DataFrame:
    q = E.groupby("d")[x].transform(lambda z: pd.qcut(z.rank(method="first"), 10, labels=False))
    return pd.DataFrame(
        {
            f"y{h}": E.groupby(["d", q])[f"y{h}"].mean().groupby(level=1).mean() * 100
            for h in (20, 60)
        }
    ).T


def book(E: pd.DataFrame, pick: pd.Series) -> dict[str, float]:
    r = E.loc[pick, ["d", "y20"]].groupby("d")["y20"].mean().dropna()
    return {
        "ann_excess_%": r.mean() * 12 * 100,
        "t": r.mean() / r.std() * np.sqrt(len(r)),
        "hit": (r > 0).mean(),
        "n_avg": pick.groupby(E["d"]).sum().mean(),
    }


def main() -> None:
    E = pd.read_parquet(OUT / "panel.parquet").reset_index()
    E["abs_cgo"] = E["cgo_tri_a1.5"].abs()
    src = f"read_parquet('{LAKE}/derived/features/**/*.parquet', hive_partitioning=true, union_by_name=true)"
    sc = (
        duckdb.connect()
        .sql(f"SELECT trade_date d, ts_code, value score FROM {src} WHERE factor = 'score'")
        .df()
    )
    E = E.merge(sc, on=["d", "ts_code"], how="left")
    for x in ("cgo_tri_a1.5", "abs_cgo"):
        E[f"{x}_net"] = pd.concat([residual(g, x) for _, g in E.groupby("d")])
    for x in ("cgo_tri_a1.5", "abs_cgo", "cgo_tri_a1.5_net", "abs_cgo_net"):
        print(f"\n{x} deciles (excess %, 0 = lowest)\n", deciles(E, x).round(2).to_string())
    pct = lambda x: E.groupby("d")[x].rank(pct=True)  # noqa: E731
    top_score = pct("score") > 0.8
    books = {
        "low |CGO| 20%": pct("abs_cgo") <= 0.2,
        "low |CGO| net 20%": pct("abs_cgo_net") <= 0.2,
        "low CGO 20% (deep loss)": pct("cgo_tri_a1.5") <= 0.2,
        "score top 20%": top_score,
        "score top 20%, drop high |CGO| 20%": top_score & (pct("abs_cgo") <= 0.8),
        "score top 20%, drop high |CGO| net 20%": top_score & (pct("abs_cgo_net") <= 0.8),
        "score top 20%, drop high CGO 20%": top_score & (pct("cgo_tri_a1.5") <= 0.8),
    }
    B = pd.DataFrame({k: book(E, v.fillna(False)) for k, v in books.items()}).T
    B.to_csv(OUT / "long_only.csv")
    print(
        "\nlong-only, equal weight, monthly, 20d holding, excess over universe\n",
        B.round(3).to_string(),
    )


if __name__ == "__main__":
    main()
