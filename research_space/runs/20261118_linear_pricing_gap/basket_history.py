"""History of the shown baskets: each month end 2019 .. 2026, the 20 cheapest and 20 dearest by
pricing_gap (derived.features processed value, industry + size neutral) among stocks with market
value >= 100亿; equal-weight next-20-session return in excess of the same-size universe mean.
Cumulative, by year, hit rate. Also the user's holdings' current percentile (positions file)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
N, MIN_MV = 20, 100.0


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    days = q.sql("SELECT DISTINCT trade_date FROM curated.daily WHERE trade_date >= '20190101' ORDER BY 1")["trade_date"].astype(str).tolist()
    ends = [d for d, n in zip(days, [*days[1:], ""], strict=True) if d[:6] != n[:6]]
    nxt = {d: days[min(days.index(d) + 20, len(days) - 1)] for d in ends}
    f = q.sql("SELECT trade_date, ts_code, value FROM derived.features WHERE factor = 'pricing_gap' AND trade_date IN (SELECT UNNEST(?))", [ends])
    mv = q.sql("SELECT trade_date, ts_code, total_mv / 1e4 mv FROM curated.daily_basic WHERE trade_date IN (SELECT UNNEST(?))", [ends])
    px = q.sql("SELECT d.ts_code, d.trade_date, d.close * a.adj_factor px FROM curated.daily d JOIN curated.adj_factor a "
               "USING (ts_code, trade_date) WHERE d.trade_date IN (SELECT UNNEST(?))", [sorted(set(ends) | set(nxt.values()))])
    names = q.sql("SELECT ts_code, name FROM curated.stock_basic").set_index("ts_code")["name"]
    cat.close()
    px = px.set_index(["trade_date", "ts_code"])["px"]
    m = f.merge(mv, on=["trade_date", "ts_code"])
    m = m[m["mv"] >= MIN_MV].copy()
    m["pct"] = m.groupby("trade_date")["value"].rank(pct=True)  # 1 = cheapest
    last = ends[-1]
    hold = yaml.safe_load((REPO / "config/local.positions.yaml").read_text(encoding="utf-8"))
    codes = sorted({p["code"] for book in ([hold] if "positions" in hold else hold.values()) if isinstance(book, dict)
                    for p in book.get("positions", []) if isinstance(p, dict) and "code" in p})
    now = m[m["trade_date"] == last].set_index("ts_code")
    print(f"holdings on {last} (percentile among >= {MIN_MV:.0f}亿, 1 = cheapest):",
          {f"{names.get(c, c)}": round(float(now.at[c, 'pct']), 2) for c in codes if c in now.index})
    m = m[m["trade_date"].map(nxt) > m["trade_date"]]
    m["fwd"] = [px.get((nxt[d], c), np.nan) / px.get((d, c), np.nan) - 1 for d, c in zip(m["trade_date"], m["ts_code"], strict=True)]
    m = m.dropna(subset=["fwd"])
    m["ex"] = (m["fwd"] - m.groupby("trade_date")["fwd"].transform("mean")) * 100
    cheap = m[m.groupby("trade_date")["value"].rank(ascending=False) <= N].groupby("trade_date")["ex"].mean()
    dear = m[m.groupby("trade_date")["value"].rank() <= N].groupby("trade_date")["ex"].mean()
    out = pd.DataFrame({"cheap20": cheap, "dear20": dear, "cheap-dear": cheap - dear})
    st = {c: {"mean %/m": round(out[c].mean(), 2), "t": round(out[c].mean() / out[c].std() * np.sqrt(len(out)), 2),
              "hit": round((out[c] > 0).mean(), 2), "Sharpe": round(out[c].mean() / out[c].std() * 12**0.5, 2),
              "cum %": round(((1 + out[c] / 100).prod() - 1) * 100, 1)} for c in out}
    print(f"\nmonthly baskets of {N}, mv >= {MIN_MV:.0f}亿, {len(out)} months, excess vs the same-size universe\n", pd.DataFrame(st).T.to_string())
    yr = ((1 + out / 100).groupby(out.index.str[:4]).prod() - 1) * 100
    print("\ncompounded excess by year %\n", yr.round(1).to_string())
    print("\nlast 6 months %/m\n", out.tail(6).round(2).to_string())


if __name__ == "__main__":
    main()
