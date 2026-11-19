"""Ad-hoc: partial beta of China daily returns on the US 10y yield change (bp), CSI300 controlled."""
import duckdb, numpy as np, pandas as pd
from quant_cn.core.positions_book import PositionsBook
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261116_cycle_screen"; OUT.mkdir(parents=True, exist_ok=True)
CATALOG = str(LAKE / "meta/quant_cn.duckdb")

from quant_cn.core.config import Config
from quant_cn.core.clock import Clock
from quant_cn.data_loading.tushare_client import TushareClient

cfg = Config.load(Path("."))
cl = TushareClient(cfg.tushare, Clock())
y = cl.query("us_tycr", {"start_date": "20220101", "end_date": "20261116"}, ["date", "y2", "y10"])
y = y.dropna(subset=["y10"]).sort_values("date")
y["dy10"] = y["y10"].astype(float).diff() * 100
y["date"] = pd.to_datetime(y["date"])
print("us_tycr last:", y.tail(3)[["date", "y10", "dy10"]].to_string(index=False))
print("y10 1m/3m/ytd change bp:", {k: round((y.y10.iloc[-1] - y[y.date <= d].y10.iloc[-1]) * 100) for k, d in [("1m", "2026-10-16"), ("3m", "2026-08-16"), ("ytd", "2025-12-31")]})

book = PositionsBook.load(Path("."))
pos = {"positions": [{"code": p.code, "shares": p.shares} for p in book.positions], "cash": book.cash}
codes = [p["code"] for p in pos["positions"]] + ["000657.SZ"]
con = duckdb.connect(CATALOG, read_only=True)
q = lambda s: con.execute(s).df()
st = q(f"SELECT trade_date, ts_code, pct_chg, close FROM curated.daily WHERE trade_date>='20220101' AND ts_code IN ({','.join(repr(c) for c in codes)})")
fd = q("SELECT trade_date, ts_code, pct_chg, close FROM curated.fund_daily WHERE trade_date>='20220101' AND ts_code IN ('159201.SZ','510300.SH','512100.SH')")
ix = q("SELECT trade_date, ts_code, pct_chg FROM curated.index_daily WHERE trade_date>='20220101' AND ts_code IN ('000300.SH','000852.SH')")
nm = q(f"SELECT ts_code, name FROM curated.stock_basic").set_index("ts_code").name.to_dict()
allr = pd.concat([st, fd, ix])
allr["d"] = pd.to_datetime(allr.trade_date)
mkt = allr[allr.ts_code == "000300.SH"][["d", "pct_chg"]].rename(columns={"pct_chg": "m"}).sort_values("d")
mkt = pd.merge_asof(mkt, y[["date", "dy10"]].rename(columns={"date": "ud"}), left_on="d", right_on="ud", allow_exact_matches=False)
out = []
for c, g in allr.groupby("ts_code"):
    if c == "000300.SH":
        continue
    g = g.merge(mkt, on="d").dropna(subset=["pct_chg", "m", "dy10"])
    row = {"code": c, "name": nm.get(c, c)}
    for lab, start in [("2y", "2024-11-16"), ("1y", "2025-11-16")]:
        h = g[g.d > start]
        if len(h) < 120:
            continue
        X = np.column_stack([np.ones(len(h)), h.m, h.dy10]); b, *_ = np.linalg.lstsq(X, h.pct_chg, rcond=None)
        e = h.pct_chg - X @ b; se = np.sqrt((e @ e) / (len(h) - 3) * np.linalg.inv(X.T @ X)[2, 2])
        row[f"b10_{lab}"] = round(b[2] * 10, 2); row[f"t_{lab}"] = round(b[2] / se, 1)
    out.append(row)
res = pd.DataFrame(out)
last = st[st.trade_date == st.trade_date.max()].set_index("ts_code").close
w = {p["code"]: p["shares"] * last.get(p["code"], np.nan) for p in pos["positions"]}
tot = sum(v for v in w.values() if v == v) + pos["cash"]
res["weight"] = res.code.map(lambda c: round(w.get(c, np.nan) / tot, 3))
res.to_csv(OUT / "us10y_beta.csv", index=False)
print(res.to_string(index=False))
for lab in ["2y", "1y"]:
    r = res.dropna(subset=["weight"])
    print(lab, "book beta per +10bp (pct, incl. cash):", round((r.weight * r[f"b10_{lab}"]).sum(), 3), " total value:", round(tot))
