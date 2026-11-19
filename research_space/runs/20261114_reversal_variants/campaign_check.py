"""Plan 25 ph2 checks on the campaign features (month ends 2019 .. 2026): raw (pre-processing) 20-day
rank IC of reversal_intraday_1m against the research 0.076 (research: next-open entry; here close to
close), rank correlation with reversal_1m (raw and processed), and the Fama-MacBeth slope of the
processed intraday factor net of processed reversal_1m (20-day excess vs the month's mean)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
PAIR = ["reversal_intraday_1m", "reversal_1m"]


def tstat(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.mean() / s.std() * np.sqrt(len(s)))


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: days[min(days.index(d) + 20, len(days) - 1)] for d in ends}
    f = q.sql("SELECT trade_date, ts_code, factor, value, value_raw FROM derived.features WHERE trade_date IN (SELECT UNNEST(?)) "
              "AND factor IN (SELECT UNNEST(?))", [ends, PAIR])
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [sorted(set(ends) | set(nxt.values()))])
    cat.close()
    w = f.pivot_table(index=["trade_date", "ts_code"], columns="factor", values=["value", "value_raw"])
    w.columns = [f"{a}:{b}" for a, b in w.columns]
    w = w.reset_index()
    px = px.set_index(["trade_date", "ts_code"])["px"]
    fwd = pd.Series([px.get((nxt[d], c), np.nan) / px.get((d, c), np.nan) - 1 for d, c in zip(w["trade_date"], w["ts_code"], strict=True)], index=w.index)
    w["ex"] = fwd - fwd.groupby(w["trade_date"]).transform("mean")
    w = w[w["trade_date"].map(nxt) > w["trade_date"]].dropna()
    by = w.groupby("trade_date")
    for col in ("value_raw:reversal_intraday_1m", "value_raw:reversal_1m", "value:reversal_intraday_1m", "value:reversal_1m"):
        ic = by.apply(lambda x, c=col: x[c].rank().corr(x["ex"].rank()))
        print(f"{col:32s} IC20 {ic.mean():.4f} (t {tstat(ic):.2f}, {len(ic)} months)")
    for kind in ("value_raw", "value"):
        rc = by.apply(lambda x, k=kind: x[f"{k}:reversal_intraday_1m"].rank().corr(x[f"{k}:reversal_1m"].rank()))
        print(f"rank corr intraday vs reversal_1m ({kind}): {rc.mean():.2f}")
    fm = []
    for _, x in by:
        X = np.column_stack([np.ones(len(x)), x["value:reversal_intraday_1m"].rank(pct=True) - 0.5, x["value:reversal_1m"].rank(pct=True) - 0.5])
        fm.append(np.linalg.lstsq(X, x["ex"].rank(pct=True) - 0.5, rcond=None)[0][1:])
    fm = pd.DataFrame(fm, columns=["intraday", "reversal_1m"])
    print("FM together:", {c: f"{fm[c].mean():+.4f} (t {tstat(fm[c]):.2f})" for c in fm})


if __name__ == "__main__":
    main()
