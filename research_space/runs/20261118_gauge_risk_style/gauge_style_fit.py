"""Plan 21 ph6, risk part: the RetailGauge as a candidate style `retail_crowding` beside the fitted model.

Daily, 2022-06 .. latest: the model's own constrained WLS (FactorReturnEstimator.compute_monitor, D-130)
is rerun on the stored exposures (derived.risk_exposure at t-1, the 14 model styles + SW L1 industries)
with one extra style, so the model itself is unchanged:
    retail_crowding = latest derived.retail_gauge pct known at t-1 (<= 40 days old), OLS-orthogonalised
    to size, standardised like every style (circ_mv-weighted mean 0, equal-weighted sd 1, clipped at
    +-3, restandardised); stocks without a reading get 0.
Returns t-1 -> t from adjusted closes; weights sqrt(circ_mv) capped as in the model.
Check: the base regression's R2 must equal derived.risk_factor_return's r2 (panel replication).
Output: daily ret / t / R2 gain -> meta/runs/research/20261118_gauge_risk_style/monitor.parquet;
summary printed: share of days |t| > 2, annualised vol, mean return (t), mean R2 gain, the same for the
model's styles over the same days, a factor bias statistic (returns over an EWMA hl-90 vol forecast,
21-day blocks), and the average cap-weighted correlation of the exposure with each style.
Usage: gauge_style_fit.py [start YYYYMMDD]."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.risk.factor_return_estimator import FactorReturnEstimator

REPO = Path(__file__).resolve().parents[3]
NAME = "retail_crowding"
OUT = "meta/runs/research/20261118_gauge_risk_style"


def standardise(x: pd.Series, w: pd.Series) -> pd.Series:
    for _ in range(5):
        x = (x - np.average(x, weights=w)) / x.std()
        if x.abs().max() <= 3:
            break
        x = x.clip(-3, 3)
    return x


def build_style(part: pd.DataFrame) -> pd.Series:
    has = part["pct"].notna() & part["size"].notna() & (part["circ_mv"] > 0)
    out = pd.Series(0.0, index=part.index)
    if has.sum() < 100:
        return out
    f = part[has]
    X = np.column_stack([np.ones(len(f)), f["size"].to_numpy()])
    b, *_ = np.linalg.lstsq(X, f["pct"].to_numpy(), rcond=None)
    out[has] = standardise(pd.Series(f["pct"].to_numpy() - X @ b, index=f.index), f["circ_mv"])
    return out


def load_chunk(q: LakeQuery, days: list[str], a: int, b: int, styles: list[str]) -> pd.DataFrame:
    dates = days[a:b]
    ret_days = days[a : b + 1]
    ex = q.sql("SELECT trade_date, ts_code, factor, exposure FROM derived.risk_exposure "
               "WHERE trade_date IN (SELECT UNNEST(?))", [dates])
    ind = ex["factor"].str.startswith("ind_")
    x = ex[~ind & ex["factor"].isin(styles)].pivot_table(index=["trade_date", "ts_code"], columns="factor",
                                                        values="exposure")
    l1 = ex[ind].assign(l1_code=lambda f: f["factor"].str[4:]).set_index(["trade_date", "ts_code"])["l1_code"]
    x = x.join(l1, how="outer").reset_index()
    caps = q.sql("SELECT trade_date, ts_code, circ_mv * 1e4 AS circ_mv FROM curated.daily_basic "
                 "WHERE trade_date IN (SELECT UNNEST(?))", [dates])
    x = x.merge(caps, on=["trade_date", "ts_code"], how="left")
    g = q.sql("SELECT ts_code, as_of, pct FROM derived.retail_gauge WHERE as_of <= ? AND as_of >= ?",
              [dates[-1], str(int(dates[0]) - 10000)])
    x["k"] = x["trade_date"].astype(int)
    g["k"] = g["as_of"].astype(int)
    x = pd.merge_asof(x.sort_values("k"), g.sort_values("k")[["k", "ts_code", "pct"]], on="k", by="ts_code",
                      direction="backward", tolerance=200)  # YYYYMMDD ints: 200 ~ under 2 months
    x[NAME] = x.groupby("trade_date", group_keys=False)[["pct", "size", "circ_mv"]].apply(build_style)
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS px FROM curated.daily d "
               "JOIN curated.adj_factor a USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))",
               [ret_days]).pivot(index="trade_date", columns="ts_code", values="px").sort_index()
    ret = (px / px.shift(1) - 1).iloc[1:].reset_index().melt(id_vars="trade_date", var_name="ts_code",
                                                              value_name="ret").dropna()
    nxt = dict(zip(ret_days[:-1], ret_days[1:], strict=True))
    x["trade_date"] = x["trade_date"].map(nxt)
    return x.merge(ret, on=["trade_date", "ts_code"], how="inner")


def exposure_corr(panel: pd.DataFrame, styles: list[str]) -> pd.Series:
    rows = []
    for _, f in panel.groupby("trade_date"):
        f = f.dropna(subset=[NAME, *styles])
        w = f["circ_mv"].to_numpy()
        c = np.cov(f[[NAME, *styles]].to_numpy().T, aweights=w)
        sd = np.sqrt(np.diag(c))
        rows.append(c[0, 1:] / (sd[0] * sd[1:]))
    return pd.Series(np.nanmean(rows, axis=0), index=styles)


def bias_stat(ret: pd.Series, half_life: int = 90, horizon: int = 21) -> float:
    var = (ret**2).ewm(halflife=half_life, min_periods=63).mean().shift(1)
    blocks = []
    for i in range(63, len(ret) - horizon, horizon):
        realised = ret.iloc[i : i + horizon].sum()
        blocks.append(realised / np.sqrt(var.iloc[i] * horizon))
    return float(np.std(blocks))


def main() -> None:
    start = sys.argv[1] if len(sys.argv) > 1 else "20220601"
    cfg = Config.load(REPO)
    styles = [s.name for s in cfg.risk_model.styles]
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM derived.risk_exposure WHERE trade_date >= ? ORDER BY 1",
                 [start])["trade_date"].tolist()
    model = q.sql("SELECT trade_date, factor, ret, t_stat, r2 FROM derived.risk_factor_return WHERE trade_date > ?",
                  [start])
    est = FactorReturnEstimator(styles, cfg.risk_model.weight_cap_quantile)
    monitors, corrs, checks = [], [], []
    for a in range(0, len(days) - 1, 60):
        panel = load_chunk(q, days, a, min(a + 60, len(days) - 1), styles)
        monitors.append(est.compute_monitor(panel, [NAME]))
        corrs.append(exposure_corr(panel, styles))
        d0 = panel["trade_date"].iloc[0]
        base = est.compute_date(panel[panel["trade_date"] == d0])
        if base is not None:
            checks.append((d0, float(base[0]["r2"].iloc[0]),
                           float(model.loc[model["trade_date"] == d0, "r2"].iloc[0])))
        print(f"{days[a]}: {len(panel)} rows", flush=True)
    cat.close()
    mon = pd.concat(monitors, ignore_index=True)
    out = Path(cfg.lake.root) / OUT
    out.mkdir(parents=True, exist_ok=True)
    mon.to_parquet(out / "monitor.parquet")
    print("\nreplication (session, rebuilt R2, model R2):", *[f"{d} {r:.4f} {m:.4f}" for d, r, m in checks],
          sep="\n  ")
    model = model[model["trade_date"].isin(set(mon["trade_date"]))]
    rows = {}
    for name, f in [(NAME, mon), *[(s, model[model["factor"] == s]) for s in styles]]:
        r = f.set_index("trade_date")["ret"].sort_index()
        rows[name] = {
            "days": len(f), "share |t|>2": (f["t_stat"].abs() > 2).mean(), "vol % pa": r.std() * np.sqrt(252) * 100,
            "mean % pa": r.mean() * 252 * 100, "t(mean)": r.mean() / r.std() * np.sqrt(len(r)),
            "bias": bias_stat(r),
        }
    table = pd.DataFrame(rows).T
    table.loc[NAME, "R2 gain"] = mon["r2"].mean()
    pd.set_option("display.width", 200)
    print("\n", table.round(3).to_string())
    print("\nmean cap-weighted correlation of retail_crowding with the styles:\n",
          pd.concat(corrs, axis=1).mean(axis=1).round(3).to_string())
    by_year = mon.assign(y=mon["trade_date"].str[:4]).groupby("y").agg(
        share_t2=("t_stat", lambda t: (t.abs() > 2).mean()), ret_pa=("ret", lambda r: r.mean() * 252 * 100),
        r2_gain=("r2", "mean"))
    print("\nby year:\n", by_year.round(4).to_string())


if __name__ == "__main__":
    main()
