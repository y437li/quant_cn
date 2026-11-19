"""Plan 21 ph6, score part: the RetailGauge as a score input and the score's style residual with the
candidate style. Month ends 2022-06 .. last full month (production derived.retail_gauge from 2022-05).

Score   = derived.features 'score' (current campaign weights, config/factors.yaml).
Score+G = mean of the score's processed factors and the processed 'retail_gauge' factor (industry +
          size neutral z of -pct, RetailGaugeFactor), equal weight, as the campaign combines them.
Forward excess: next 20 / 60 sessions' adjusted return minus the month's cross-sectional mean (%).
Reports, all stocks and large caps (top 40% total_mv):
 1. rank IC 20 / 60 (t over non-overlapping months), decile long-short Sharpe and top-decile excess
    for score, score+G and the gauge alone;
 2. the score's style residual (per month OLS of the score on the model's styles) IC 20, without and
    with retail_crowding (pct orthogonalised to size, standardised as in gauge_style_fit.py)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from gauge_style_fit import build_style  # same folder
from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]


def tstat(s: pd.Series, step: int = 1) -> float:
    s = s.dropna().iloc[::step]
    return float(s.mean() / s.std() * np.sqrt(len(s)))


def load(cfg: Config) -> tuple[pd.DataFrame, list[str], list[str]]:
    weights = cfg.campaign.weights
    parts = [k for k, v in weights.items() if v > 0]
    styles = [s.name for s in cfg.risk_model.styles]
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20220601' ORDER BY 1")[
        "trade_date"].tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: {h: days[min(days.index(d) + h, len(days) - 1)] for h in (20, 60)} for d in ends}
    f = q.sql("SELECT trade_date, ts_code, factor, value FROM derived.features WHERE trade_date IN (SELECT UNNEST(?)) "
              "AND factor IN (SELECT UNNEST(?))", [ends, [*parts, "score", "retail_gauge"]])
    ex = q.sql("SELECT trade_date, ts_code, factor, exposure FROM derived.risk_exposure WHERE trade_date IN "
               "(SELECT UNNEST(?)) AND factor IN (SELECT UNNEST(?))", [ends, styles])
    mv = q.sql("SELECT trade_date, ts_code, total_mv, circ_mv FROM curated.daily_basic WHERE trade_date IN "
               "(SELECT UNNEST(?))", [ends])
    g = q.sql("SELECT ts_code, as_of, pct FROM derived.retail_gauge")
    want = sorted(set(ends) | {v for d in nxt.values() for v in d.values()})
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [want])
    cat.close()
    m = (f.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="value").reset_index()
         .merge(ex.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="exposure")
                .add_prefix("s_").reset_index(),
                on=["trade_date", "ts_code"]).merge(mv, on=["trade_date", "ts_code"]))
    m["k"], g["k"] = m["trade_date"].astype(int), g["as_of"].astype(int)
    m = pd.merge_asof(m.sort_values("k"), g.sort_values("k")[["k", "ts_code", "pct"]], on="k", by="ts_code",
                      direction="backward", tolerance=200)
    px = px.set_index(["trade_date", "ts_code"])["px"]
    for h in (20, 60):
        fwd = pd.Series([px.get((nxt[d][h], c), np.nan) / px.get((d, c), np.nan) - 1
                         for d, c in zip(m["trade_date"], m["ts_code"], strict=True)], index=m.index)
        m[f"ex{h}"] = (fwd - fwd.groupby(m["trade_date"]).transform("mean")) * 100
    m = m.dropna(subset=["score", "ex20"]).reset_index(drop=True)
    w = pd.Series(weights)[parts]
    vals = m[parts]
    m["score_g"] = ((vals * w).sum(axis=1) + m["retail_gauge"].fillna(0) * 1.0) / (
        vals.notna().mul(w).sum(axis=1) + m["retail_gauge"].notna())
    m["size"] = m["s_size"]
    m["retail_crowding"] = m.groupby("trade_date", group_keys=False)[["pct", "size", "circ_mv"]].apply(build_style)
    return m, [f"s_{s}" for s in styles], parts


def score_lines(part: pd.DataFrame) -> pd.DataFrame:
    rows = {}
    for col in ("score", "score_g", "retail_gauge"):
        d, r = part.dropna(subset=[col]), {}
        for h, step in ((20, 1), (60, 3)):
            ic = d.dropna(subset=[f"ex{h}"]).groupby("trade_date").apply(
                lambda x, c=col, hh=h: x[c].rank().corr(x[f"ex{hh}"].rank()))
            r[f"IC{h}"], r[f"t{h}"] = round(ic.mean(), 4), round(tstat(ic, step), 2)
        grp = d.groupby("trade_date").apply(lambda x, c=col: x.assign(
            b=pd.qcut(x[c].rank(method="first"), 10, labels=False)).groupby("b")["ex20"].mean())
        ls = grp[9] - grp[0]
        r["D LS %/m"], r["D Sharpe"], r["top %/m"] = round(ls.mean(), 2), round(ls.mean() / ls.std() * 12**0.5, 2), \
            round(grp[9].mean(), 2)
        rows[col] = r
    return pd.DataFrame(rows).T


def residual_ic(part: pd.DataFrame, cols: list[str]) -> tuple[float, float]:
    ics = []
    for _, f in part.dropna(subset=[*cols, "score"]).groupby("trade_date"):
        X = np.column_stack([np.ones(len(f)), f[cols].to_numpy()])
        b, *_ = np.linalg.lstsq(X, f["score"].to_numpy(), rcond=None)
        res = pd.Series(f["score"].to_numpy() - X @ b, index=f.index)
        ics.append(res.rank().corr(f["ex20"].rank()))
    s = pd.Series(ics)
    return round(s.mean(), 4), round(tstat(s), 2)


def main() -> None:
    cfg = Config.load(REPO)
    m, styles, parts = load(cfg)
    big = m.groupby("trade_date")["total_mv"].rank(pct=True) > 0.6
    pd.set_option("display.width", 200)
    print(f"score factors: {parts}; months {m['trade_date'].min()} .. {m['trade_date'].max()}")
    for label, part in (("all", m), ("large caps", m[big])):
        print(f"\n## {label}: {part['trade_date'].nunique()} months\n", score_lines(part).to_string())
        base = residual_ic(part, styles)
        withg = residual_ic(part, [*styles, "retail_crowding"])
        print(f"score style-residual IC20 (t): styles {base}, styles + retail_crowding {withg}")


if __name__ == "__main__":
    main()
