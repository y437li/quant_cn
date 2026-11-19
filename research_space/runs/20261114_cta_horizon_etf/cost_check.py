"""Cost sensitivity of the ETF equal-capital book (part C of horizon_etf.py): 0 / 5 / 15 / 30 bp per unit traded (2026-11-14)."""
from __future__ import annotations
import contextlib, importlib.util, io
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("he", HERE / "horizon_etf.py")
he = importlib.util.module_from_spec(spec); spec.loader.exec_module(he)
rows = []
for bp in (0, 5, 15, 30):
    with contextlib.redirect_stdout(io.StringIO()):
        T = he.part_c(bp / 1e4)
    rows.append(T.assign(cost_bp=bp)[["signal", "cost_bp", "ann", "sharpe", "max_dd", "turnover_y"]])
A = pd.concat(rows); A.to_csv(he.OUT / "etf_cost_check.csv", index=False)
P = A.pivot_table(index="signal", columns="cost_bp", values=["ann", "sharpe"], sort=False)
P["ann"] = (P["ann"] * 100).round(1); print(P.round(2).to_string())
print(A.drop_duplicates("signal").set_index("signal").turnover_y.round(1).to_string())
