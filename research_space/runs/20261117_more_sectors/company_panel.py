"""Second-round sector leaders (express, MDI, coking coal, oil services): quarterly profit and gross margin, valuation vs history, consensus and its
3-month revision, balance sheet, and chips (RetailGauge, winner rate, holder count). As of 2026-11-16."""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

cfg = Config.load(Path(".")); LAKE = Path(cfg.lake.root)
OUT = LAKE / "meta/runs/research/20261117_more_sectors"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True); q = lambda s: c.execute(s).df()
AS_OF = "20261116"
NAMES = {"002352.SZ": "顺丰控股", "600233.SH": "圆通速递", "002468.SZ": "申通快递", "002120.SZ": "韵达股份", "600309.SH": "万华化学", "000983.SZ": "山西焦煤", "601699.SH": "潞安环能",
         "600985.SH": "淮北矿业", "601808.SH": "中海油服", "600583.SH": "海油工程", "002353.SZ": "杰瑞股份"}
IN = ",".join(repr(k) for k in NAMES)
pd.set_option("display.width", 260)
inc = q(f"""SELECT ts_code, end_date, arg_max(n_income_attr_p, ann_date) np, arg_max(revenue, ann_date) rev, arg_max(oper_cost, ann_date) AS cost
  FROM curated.income_vip WHERE report_type='1' AND ts_code IN ({IN}) AND end_date>='20240101' GROUP BY 1,2""").sort_values(["ts_code", "end_date"])
inc["y"] = inc.end_date.str[:4]
for col in ["np", "rev", "cost"]:
    inc[col + "_q"] = inc[col] - inc.groupby(["ts_code", "y"])[col].shift().fillna(0)
inc["gm_q"] = 1 - inc.cost_q / inc.rev_q
inc["name"] = inc.ts_code.map(NAMES)
npq = inc.pivot(index="name", columns="end_date", values="np_q") / 1e8
gmq = inc.pivot(index="name", columns="end_date", values="gm_q") * 100
print("单季归母净利润（亿）"); print(npq.round(1).to_string())
print("\n单季毛利率（%）"); print(gmq.round(1).to_string())
db = q(f"SELECT ts_code, trade_date, close, pe_ttm, pb, total_mv/1e4 mv, dv_ttm FROM curated.daily_basic WHERE ts_code IN ({IN}) AND trade_date>='20160101'")
now = db[db.trade_date == AS_OF].set_index("ts_code")
pbpct = {k: (g.pb < now.loc[k, "pb"]).mean() for k, g in db[db.pb > 0].groupby("ts_code")}
pa = q(f"SELECT ts_code, trade_date, close_adj FROM derived.prices_adj WHERE ts_code IN ({IN}) AND trade_date>='20210101'")
ret = {}
for k, g in pa.groupby("ts_code"):
    g = g.set_index("trade_date").close_adj.sort_index(); last = g.iloc[-1]
    ret[k] = {"ret3m": (last / g[g.index <= "20260816"].iloc[-1] - 1) * 100, "ret12m": (last / g[g.index <= "20251116"].iloc[-1] - 1) * 100,
              "from_5y_hi": (last / g.max() - 1) * 100}
rc = q(f"""SELECT ts_code, report_date, org_name, quarter, np FROM curated.report_rc WHERE ts_code IN ({IN}) AND quarter IN ('2026Q4','2027Q4') AND report_date>='20260501'""")
def cons(d0, d1, qtr):
    s = rc[(rc.report_date > d0) & (rc.report_date <= d1) & (rc.quarter == qtr)].sort_values("report_date").groupby(["ts_code", "org_name"]).np.last()
    return s.groupby("ts_code").median() / 1e4
c26, c27, c27_old = cons("20260816", AS_OF, "2026Q4"), cons("20260816", AS_OF, "2027Q4"), cons("20260501", "20260816", "2027Q4")
nb = rc[(rc.report_date > "20260816")].groupby("ts_code").org_name.nunique()
bs = q(f"""SELECT ts_code, arg_max(total_liab, ann_date)/arg_max(total_assets, ann_date) dta FROM curated.balancesheet_vip
  WHERE report_type='1' AND end_date='20260930' AND ts_code IN ({IN}) GROUP BY 1""").set_index("ts_code").dta
gauge = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet")["pct"]
hn = q(f"""SELECT ts_code, end_date, arg_max(holder_num, ann_date) n FROM curated.stk_holdernumber WHERE ts_code IN ({IN}) AND end_date>='20250930' GROUP BY 1,2""").sort_values(["ts_code", "end_date"])
hchg = hn.groupby("ts_code").n.apply(lambda s: (s.iloc[-1] / s.iloc[-2] - 1) * 100 if len(s) > 1 else None)
cl = TushareClient(cfg.tushare, Clock())
win = {}
for k in NAMES:
    d = cl.query("cyq_perf", {"ts_code": k, "trade_date": AS_OF}, [])
    win[k] = d.iloc[0][["winner_rate", "cost_15pct", "cost_50pct", "cost_85pct"]].astype(float).to_dict() if not d.empty else {}
rnd = lambda x, d=0: round(x, d) if x == x and x is not None else None
rows = []
for k, n in NAMES.items():
    r = now.loc[k]
    rows.append({"name": n, "close": r.close, "mv": round(r.mv), "pe_ttm": round(r.pe_ttm, 1) if r.pe_ttm == r.pe_ttm else None,
                 "pe27": round(r.mv / c27.get(k, float("nan")), 1), "np26e": round(c26.get(k, float("nan")), 1), "np27e": round(c27.get(k, float("nan")), 1),
                 "rev27_3m%": rnd((c27.get(k, float("nan")) / c27_old.get(k, float("nan")) - 1) * 100), "brokers": nb.get(k, 0),
                 "pb": round(r.pb, 2), "pb_pct": round(pbpct[k], 2), "dy%": round(r.dv_ttm or 0, 1), "debt/asset": round(bs.get(k), 2),
                 **{x: rnd(v) for x, v in ret[k].items()}, "gauge": round(gauge.get(k, float("nan")), 2), "holders%": round(hchg.get(k, float("nan")), 1),
                 **{x: round(v, 1) for x, v in win[k].items()}})
panel = pd.DataFrame(rows)
print("\n公司面板"); print(panel.to_string(index=False))
panel.to_csv(OUT / "company_panel.csv", index=False); npq.to_csv(OUT / "np_quarterly.csv"); gmq.to_csv(OUT / "gm_quarterly.csv")
