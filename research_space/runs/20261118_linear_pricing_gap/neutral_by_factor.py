"""Quintile long-short of each campaign factor by neutralisation, month ends 2019 .. 2026, next 20
sessions, equal weight: raw value (no neutralisation), industry only (rank within SW L1), industry +
size (the campaign's processed value, D-093). Also the long and short legs vs the universe mean, the
monthly name turnover of the two legs, and Sharpe net of 0.3% per unit of turnover."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
FACTORS = ["reversal_1m", "pricing_gap", "dividend_yield", "turnover_60d", "momentum_12_1"]
COST = 0.003


def get_turnover(sel: pd.DataFrame) -> float:
    sets = sel.groupby("trade_date")["ts_code"].apply(set).sort_index()
    return float(np.mean([1 - len(a & b) / max(len(b), 1) for a, b in zip(sets.iloc[:-1], sets.iloc[1:], strict=True)]))


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]][:-1]
    nxt = {d: days[min(days.index(d) + 20, len(days) - 1)] for d in ends}
    f = q.sql("SELECT trade_date, ts_code, factor, value, value_raw FROM derived.features "
              "WHERE trade_date IN (SELECT UNNEST(?)) AND factor IN (SELECT UNNEST(?))", [ends, FACTORS])
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [sorted(set(ends) | set(nxt.values()))])
    mem = q.sql("SELECT DISTINCT ts_code, l1_name FROM curated.index_member_all WHERE is_new = 'Y'")
    cat.close()
    px = px.set_index(["trade_date", "ts_code"])["px"]
    base = f[["trade_date", "ts_code"]].drop_duplicates()
    base["fwd"] = [px.get((nxt[d], c), np.nan) / px.get((d, c), np.nan) - 1 for d, c in zip(base["trade_date"], base["ts_code"], strict=True)]
    base = base[base["trade_date"].map(nxt) > base["trade_date"]].dropna()
    base["ex"] = (base["fwd"] - base.groupby("trade_date")["fwd"].transform("mean")) * 100
    rows = {}
    for name in FACTORS:
        x = f[f["factor"] == name].merge(base, on=["trade_date", "ts_code"]).merge(mem, on="ts_code", how="left")
        scores = {"none": x.groupby("trade_date")["value_raw"].rank(pct=True),
                  "industry": x.groupby(["trade_date", "l1_name"])["value_raw"].rank(pct=True),
                  "industry+size": x.groupby("trade_date")["value"].rank(pct=True)}
        for lab, s in scores.items():
            lo, hi = x[s > 0.8], x[s <= 0.2]  # long the top quintile (higher = better), short the bottom
            L, S = lo.groupby("trade_date")["ex"].mean(), hi.groupby("trade_date")["ex"].mean()
            ls = (L - S).dropna()
            turn = get_turnover(lo) + get_turnover(hi)
            net = ls - turn * COST * 100
            rows[(name, lab)] = {"LS %/m": round(ls.mean(), 2), "Sharpe": round(ls.mean() / ls.std() * 12**0.5, 2),
                                 "long %/m": round(L.mean(), 2), "short leg %/m": round(-S.mean(), 2),
                                 "turnover": round(turn / 2, 2), "net Sharpe": round(net.mean() / net.std() * 12**0.5, 2)}
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    main()
