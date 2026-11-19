"""SHFE metal futures curves on the last lake session: shape vs the front, front-vs-4th spread percentile since 2021."""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load().lake.root)
L = str(LAKE / "curated")
OUT = LAKE / "meta/runs/research/20261113_metal_curves"
OUT.mkdir(parents=True, exist_ok=True)
s = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
rows = []
for p, ex in [("CU", "SHF"), ("AL", "SHF"), ("AO", "SHF"), ("SN", "SHF"), ("NI", "SHF")]:
    pat = f"^{p}[0-9]{{4}}\\.{ex}$"
    d = duckdb.sql(f"""select trade_date, ts_code, close, oi from {s('fut_daily')}
      where regexp_matches(ts_code,'{pat}') and trade_date in (select max(trade_date) from {s('fut_daily')}) order by ts_code""").df()
    d = d[d.oi > 1000]
    d["vs_front_pct"] = (d.close / d.close.iloc[0] - 1) * 100
    print(p, d.trade_date.iloc[0]); print(d[["ts_code", "close", "oi", "vs_front_pct"]].round(2).to_string(index=False))
    h = duckdb.sql(f"""with x as (select trade_date, close, row_number() over (partition by trade_date order by ts_code) rn
      from {s('fut_daily')} where regexp_matches(ts_code,'{pat}') and oi>1000 and trade_date>='20210101')
      select trade_date, max(close) filter (where rn=1)/max(close) filter (where rn=4)-1 spr, max(close) filter (where rn=1) front
      from x group by 1 order by 1""").df().dropna(subset=["spr"])
    cur, c = h.spr.iloc[-1], h.front
    rows.append({"family": p, "front": c.iloc[-1], "spread_pct": cur * 100, "spread_5y_pctile": (h.spr < cur).mean(),
                 "front_5y_pctile": (c < c.iloc[-1]).mean(), "front_1y_pctile": (c.tail(250) < c.iloc[-1]).mean(),
                 "chg_3m_pct": (c.iloc[-1] / c.iloc[-63] - 1) * 100})
    d.to_csv(OUT / f"curve_{p}.csv", index=False)
summary = pd.DataFrame(rows)
print(summary.round(3).to_string(index=False))
summary.to_csv(OUT / "summary.csv", index=False)
