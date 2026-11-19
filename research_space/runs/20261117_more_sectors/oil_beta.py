"""Partial beta of daily returns on the INE crude (SC main) daily change, CSI 300 controlled, past year,
for the candidate names (万华 run-up check and "都是跟石油相关的"). Writes oil_beta.csv."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261117_more_sectors"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True)
N = {"600309.SH": "万华化学", "600346.SH": "恒力石化", "601233.SH": "桐昆股份", "603225.SH": "新凤鸣", "601808.SH": "中海油服",
     "600233.SH": "圆通速递", "002352.SZ": "顺丰控股", "600985.SH": "淮北矿业", "002078.SZ": "太阳纸业", "001914.SZ": "招商积余",
     "001979.SZ": "招商蛇口", "002601.SZ": "龙佰集团", "002714.SZ": "牧原股份"}
IN = ",".join(repr(k) for k in N)
r = c.execute(f"SELECT trade_date, ts_code, pct_chg FROM curated.daily WHERE ts_code IN ({IN}) AND trade_date>'20251116'").df().pivot(index="trade_date", columns="ts_code", values="pct_chg")
m = c.execute("SELECT trade_date, pct_chg m FROM curated.index_daily WHERE ts_code='000300.SH' AND trade_date>'20251116'").df().set_index("trade_date").m
sc = c.execute("SELECT trade_date, settle FROM curated.fut_daily WHERE ts_code='SC.INE' AND trade_date>'20251110' ORDER BY 1").df().set_index("trade_date").settle.pct_change() * 100
rows = []
for k, n in N.items():
    d = pd.concat([r[k], m, sc.rename("sc")], axis=1).dropna()
    X = np.column_stack([np.ones(len(d)), d.m, d.sc]); b, *_ = np.linalg.lstsq(X, d[k], rcond=None)
    e = d[k] - X @ b; se = np.sqrt(e @ e / (len(d) - 3) * np.linalg.inv(X.T @ X)[2, 2])
    rows.append({"name": n, "beta_per_1pct_sc": round(b[2], 2), "t": round(b[2] / se, 1)})
res = pd.DataFrame(rows).sort_values("beta_per_1pct_sc", ascending=False)
res.to_csv(OUT / "oil_beta.csv", index=False); print(res.to_string(index=False))
