"""Does pricing_gap add to the existing factors? Month ends 2019 .. 2026 from derived.features
(processed values: winsorised, standardised, Shenwan L1 + log mcap neutral, D-093).
(1) rank correlation of pricing_gap with each factor and the score; (2) score IC and decile
long-short vs a score with pricing_gap added at the same weight; (3) Fama-MacBeth: pricing_gap
net of the six score factors; (4) veto: the score's top quintile with and without the dearest
10% by pricing_gap. fwd20 = next-20-session return from close x adj_factor, excess vs the
universe mean; equal weight; all stocks and large caps (top 40% total_mv)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
SIX = ["dividend_yield", "roe_ttm", "profit_growth_ttm", "momentum_12_1", "reversal_1m", "turnover_60d"]


def tstat(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.mean() / s.std() * np.sqrt(len(s)))


def load(q: LakeQuery) -> pd.DataFrame:
    cal = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")
    days = cal["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: days[min(days.index(d) + 20, len(days) - 1)] for d in ends}
    feats = q.sql("SELECT trade_date, ts_code, factor, value FROM derived.features "
                  "WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    wide = feats.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="value").reset_index()
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS px FROM curated.daily d "
               "JOIN curated.adj_factor a USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))",
               [sorted(set(ends) | set(nxt.values()))])
    mv = q.sql("SELECT trade_date, ts_code, total_mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    px = px.set_index(["trade_date", "ts_code"])["px"]
    wide["fwd"] = [px.get((nxt[d], c), np.nan) / px.get((d, c), np.nan) - 1 for d, c in zip(wide["trade_date"], wide["ts_code"], strict=True)]
    wide = wide.merge(mv, on=["trade_date", "ts_code"], how="left")
    wide = wide[wide["trade_date"].map(nxt) > wide["trade_date"]]
    wide["ex"] = (wide["fwd"] - wide.groupby("trade_date")["fwd"].transform("mean")) * 100
    return wide.dropna(subset=["fwd"])


def summarise(w: pd.DataFrame, label: str) -> None:
    w = w.dropna(subset=["pricing_gap", "score"]).copy()
    print(f"\n######## {label}: {w['trade_date'].nunique()} months, median {int(w.groupby('trade_date').size().median())} stocks")
    corr = {c: round(w.groupby("trade_date")[["pricing_gap", c]].apply(lambda f: f.rank().corr().iloc[0, 1]).mean(), 2)
            for c in [*SIX, "score"]}
    print("(1) rank corr of pricing_gap with:", corr)
    w["score7"] = w[[*SIX, "pricing_gap"]].mean(axis=1)
    out = {}
    for col in ("score", "score7", "pricing_gap"):
        ic = w.groupby("trade_date").apply(lambda f: f[col].rank().corr(f["ex"].rank()))
        dec = w.groupby("trade_date").apply(lambda f: f.assign(d=pd.qcut(f[col].rank(method="first"), 10, labels=False)).groupby("d")["ex"].mean())
        ls = dec[9] - dec[0]
        out[col] = {"IC": round(ic.mean(), 4), "IC t": round(tstat(ic), 2), "top10 ex%": round(dec[9].mean(), 2),
                    "LS %/m": round(ls.mean(), 2), "LS Sharpe": round(ls.mean() / ls.std() * np.sqrt(12), 2)}
    print("(2) score vs score + pricing_gap\n", pd.DataFrame(out).T.to_string())
    fm = []
    for _, f in w.dropna(subset=SIX).groupby("trade_date"):
        X = np.column_stack([np.ones(len(f)), *(f[c].rank(pct=True) - 0.5 for c in ["pricing_gap", *SIX])])
        y = f["ex"].rank(pct=True) - 0.5
        fm.append(np.linalg.lstsq(X, y, rcond=None)[0][1])
    print(f"(3) FM slope of pricing_gap net of the six: {np.mean(fm):.4f} (t {tstat(pd.Series(fm)):.2f})")
    w["sq"] = w.groupby("trade_date")["score"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    w["dear"] = w.groupby("trade_date")["pricing_gap"].rank(pct=True) <= 0.1  # lowest = dearest
    top = w[w["sq"] == 4]
    res = {name: top[m].groupby("trade_date")["ex"].mean() for name, m in
           (("score top 20%", top["sq"] == 4), ("… minus dearest 10%", ~top["dear"]), ("… the vetoed ones", top["dear"]))}
    print("(4) veto inside the score's top quintile (fwd20 excess %/month):",
          {k: (round(v.mean(), 2), round(tstat(v), 2), f"{int(top[top['dear'] if 'vetoed' in k else ~top['dear'] if 'minus' in k else top['sq'] == 4].groupby('trade_date').size().mean())}/m") for k, v in res.items()})
    diff = res["… minus dearest 10%"] - res["score top 20%"]
    print(f"    veto gain {diff.mean():.3f}%/month (t {tstat(diff):.2f}), {diff.mean() * 12:.2f}%/yr")


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    w = load(LakeQuery(cat))
    cat.close()
    pd.set_option("display.width", 200)
    summarise(w, "all")
    big = w.groupby("trade_date")["total_mv"].rank(pct=True) > 0.6
    summarise(w[big], "large caps (top 40% market value)")


if __name__ == "__main__":
    main()
