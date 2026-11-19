"""How much of the score is Barra style exposure? Month ends 2019 .. 2026.

Score = derived.features 'score' (7 factors, industry + size neutral). Exposures = derived.risk_exposure
style factors (CNE5-like core styles, config/risk_model.yaml; sensitivities to US / USD / AIDC etc.
left out). Per month: OLS of the score on the styles -> R2 and coefficients (t over months); the
residual = the score's stock-specific part. fwd20 / fwd60 = next sessions' return, excess vs the month's
mean. Compare raw score vs residual: rank IC, quintile long-short Sharpe, by year; all and large caps.
Also the share of the score's quintile long-short explained by the styles' realised returns
(risk_factor_return over the holding window, weighted by the long-short's average exposure)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
STYLES = ["size", "beta", "momentum", "residual_volatility", "non_linear_size", "book_to_price", "liquidity",
          "earnings_yield", "growth", "leverage", "cash_flow_yield", "dividend_yield"]


def tstat(s: pd.Series, step: int = 1) -> float:
    s = s.dropna().iloc[::step]
    return float(s.mean() / s.std() * np.sqrt(len(s)))


def load() -> tuple[pd.DataFrame, list[str]]:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: {h: days[min(days.index(d) + h, len(days) - 1)] for h in (20, 60)} for d in ends}
    sc = q.sql("SELECT trade_date, ts_code, value AS score FROM derived.features WHERE factor = 'score' AND trade_date IN (SELECT UNNEST(?))", [ends])
    ex = q.sql("SELECT trade_date, ts_code, factor, exposure FROM derived.risk_exposure WHERE trade_date IN (SELECT UNNEST(?)) "
               "AND factor IN (SELECT UNNEST(?))", [ends, STYLES])
    mv = q.sql("SELECT trade_date, ts_code, total_mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    want = sorted(set(ends) | {v for d in nxt.values() for v in d.values()})
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [want])
    cat.close()
    styles = [s for s in STYLES if s in set(ex["factor"])]
    w = ex.pivot_table(index=["trade_date", "ts_code"], columns="factor", values="exposure").reset_index()
    m = sc.merge(w, on=["trade_date", "ts_code"]).merge(mv, on=["trade_date", "ts_code"])
    px = px.set_index(["trade_date", "ts_code"])["px"]
    for h in (20, 60):
        fwd = pd.Series([px.get((nxt[d][h], c), np.nan) / px.get((d, c), np.nan) - 1
                         for d, c in zip(m["trade_date"], m["ts_code"], strict=True)], index=m.index)
        m[f"ex{h}"] = (fwd - fwd.groupby(m["trade_date"]).transform("mean")) * 100
    return m.dropna(subset=[*styles, "score", "ex20"]), styles


def add_residual(m: pd.DataFrame, styles: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    parts, coefs, r2 = [], {}, {}
    for d, f in m.groupby("trade_date"):
        X = np.column_stack([np.ones(len(f)), f[styles].to_numpy()])
        b, *_ = np.linalg.lstsq(X, f["score"].to_numpy(), rcond=None)
        fit = X @ b
        resid = f["score"].to_numpy() - fit
        r2[d] = 1 - resid.var() / f["score"].to_numpy().var()
        coefs[d] = dict(zip(styles, b[1:], strict=True))
        parts.append(f.assign(resid=resid))
    return pd.concat(parts), pd.DataFrame(coefs).T, pd.Series(r2)


def evaluate(m: pd.DataFrame, label: str) -> None:
    rows, yearly = {}, {}
    for col in ("score", "resid"):
        r = {}
        for h, step in ((20, 1), (60, 3)):
            ic = m.dropna(subset=[f"ex{h}"]).groupby("trade_date").apply(lambda x, c=col, hh=h: x[c].rank().corr(x[f"ex{hh}"].rank()))
            r[f"IC{h}"], r[f"t{h}"] = round(ic.mean(), 4), round(tstat(ic, step), 2)
        grp = m.groupby("trade_date").apply(lambda x, c=col: x.assign(b=pd.qcut(x[c].rank(method="first"), 5, labels=False)).groupby("b")["ex20"].mean())
        ls = grp[4] - grp[0]
        r.update({"LS %/m": round(ls.mean(), 2), "LS Sharpe": round(ls.mean() / ls.std() * 12**0.5, 2), "top %/m": round(grp[4].mean(), 2)})
        rows[col] = r
        yearly[col] = ls.groupby(ls.index.str[:4]).mean().round(2)
    print(f"\n## {label}: {m['trade_date'].nunique()} months\n", pd.DataFrame(rows).T.to_string())
    print("quintile LS %/month by year\n", pd.DataFrame(yearly).T.to_string())


def main() -> None:
    m, styles = load()
    m, coefs, r2 = add_residual(m, styles)
    pd.set_option("display.width", 220)
    print(f"styles: {styles}")
    print(f"R2 of score on styles: mean {r2.mean():.2f} (min {r2.min():.2f}, max {r2.max():.2f})")
    print("coefficient mean (t over months):",
          {s: f"{coefs[s].mean():+.3f} ({tstat(coefs[s]):.1f})" for s in styles})
    evaluate(m, "all")
    evaluate(m[m.groupby("trade_date")["total_mv"].rank(pct=True) > 0.6], "large caps (top 40% mv)")


if __name__ == "__main__":
    main()
