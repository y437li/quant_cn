"""Loop over every Shenwan L3 industry (current members): cycle position (TTM attributable profit vs its
2018+ peak, single-quarter y/y for 2026 Q1-Q3), aggregate PB and its percentile since 2016, cap-weighted
3m / 12m return, median RetailGauge. Bucket each industry, then loop over the leaders (top 3 by cap) of the
candidate buckets: 2027E PE and 3m revision, PB percentile, gauge (veto >= 0.9), winner rate and price vs
chip cost, and daily partial betas on INE crude and the US 10y yield (1y, CSI 300 controlled).
Writes industries.csv and leaders.csv to the lake run folder."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

cfg = Config.load(Path(".")); LAKE = Path(cfg.lake.root)
OUT = LAKE / "meta/runs/research/20261117_all_industries"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True); q = lambda s: c.execute(s).df()
AS_OF, LAST = "20261116", "20260930"
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 400)

# ---- industry level -------------------------------------------------------------------------------
mem = q("SELECT l1_name, l3_name, ts_code, name FROM curated.index_member_all WHERE out_date IS NULL").drop_duplicates("ts_code")
inc = q("""SELECT ts_code, end_date, arg_max(n_income_attr_p, ann_date) np FROM curated.income_vip
  WHERE report_type='1' AND end_date>='20170101' GROUP BY 1,2""")
inc = inc[inc.ts_code.isin(mem.ts_code) & inc.end_date.str[4:].isin(["0331", "0630", "0930", "1231"])].sort_values(["ts_code", "end_date"])
inc["y"] = inc.end_date.str[:4]
inc["sq"] = inc.np - inc.groupby(["ts_code", "y"]).np.shift().fillna(0)
sq = inc.pivot_table(index="ts_code", columns="end_date", values="sq")
db = q(f"SELECT ts_code, total_mv/1e4 mv, pb FROM curated.daily_basic WHERE trade_date='{AS_OF}'").set_index("ts_code")
pbh = q("""SELECT ts_code, strftime(strptime(trade_date,'%Y%m%d'),'%Y%m') ym, arg_max(total_mv,trade_date) mv, arg_max(pb,trade_date) pb
  FROM curated.daily_basic WHERE trade_date>='20160101' GROUP BY 1,2""")
pbh = pbh[pbh.pb > 0].merge(mem[["ts_code", "l3_name"]], on="ts_code"); pbh["bk"] = pbh.mv / pbh.pb
pa = q(f"""SELECT ts_code, trade_date, close_adj FROM derived.prices_adj WHERE trade_date IN
  ((SELECT max(trade_date) FROM derived.prices_adj WHERE trade_date<='20260816'), (SELECT max(trade_date) FROM derived.prices_adj WHERE trade_date<='20251116'), '{AS_OF}')""")
pw = pa.pivot(index="ts_code", columns="trade_date", values="close_adj"); d3, d12 = sorted(pw.columns)[1], sorted(pw.columns)[0]
ret = pd.DataFrame({"r3m": pw[AS_OF] / pw[d3] - 1, "r12m": pw[AS_OF] / pw[d12] - 1})
gauge = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet")["pct"]

def yoy(s, d):
    prev = s.get(str(int(d[:4]) - 1) + d[4:])
    return (s[d] - prev) / abs(prev) if prev and prev == prev and prev != 0 else np.nan

rows = []
for (l1, l3), g in mem.groupby(["l1_name", "l3_name"]):
    codes = g.ts_code
    s = sq.reindex(codes).sum(min_count=1); s = s[s.index >= "20180101"]
    ttm = s.rolling(4).sum().dropna()
    if len(ttm) < 8 or LAST not in ttm.index:
        continue
    h = pbh[pbh.l3_name == l3].groupby("ym").agg(mv=("mv", "sum"), bk=("bk", "sum")); h["pb"] = h.mv / h.bk
    mv = db.reindex(codes).mv
    w = mv / mv.sum()
    rows.append(dict(l1=l1, l3=l3, n=len(codes), mv_yi=round(mv.sum()), ttm_yi=round(ttm[LAST] / 1e8, 1),
                     peak_yi=round(ttm.max() / 1e8, 1), ttm_vs_peak=round(ttm[LAST] / ttm.max(), 2) if ttm.max() > 0 else np.nan,
                     yoy_q1=round(yoy(s, "20260331"), 2), yoy_q2=round(yoy(s, "20260630"), 2), yoy_q3=round(yoy(s, "20260930"), 2),
                     pb=round(h.pb.iloc[-1], 2), pb_pct=round((h.pb < h.pb.iloc[-1]).mean(), 2),
                     r3m=round((ret.reindex(codes).r3m * w).sum() * 100), r12m=round((ret.reindex(codes).r12m * w).sum() * 100),
                     gauge_med=round(gauge.reindex(codes).median(), 2)))
ind = pd.DataFrame(rows)

def bucket(r):
    if r.ttm_yi <= 0:
        return "D 亏损/底部未拐" if not (r.yoy_q2 > 0.15 and r.yoy_q3 > 0.15) else "B 拐头(仍亏)"
    if r.pb_pct <= 0.15 and r.ttm_vs_peak >= 0.7:
        return "A 便宜+利润近峰"
    if r.pb_pct <= 0.35 and r.yoy_q2 > 0.15 and r.yoy_q3 > 0.15:
        return "B 拐头+偏便宜"
    if r.pb_pct >= 0.8:
        return "E 估值高位"
    if r.yoy_q3 < -0.15 and r.yoy_q2 < -0.15:
        return "C 利润下行"
    return "N 中性"

ind["bucket"] = ind.apply(bucket, axis=1)
ind.to_csv(OUT / "industries.csv", index=False)
print(ind.groupby("bucket").agg(n=("l3", "size"), mv=("mv_yi", "sum")).to_string())

# ---- leader level (loop over candidate industries) -------------------------------------------------
cand = ind[ind.bucket.str[0].isin(["A", "B"]) & (ind.mv_yi >= 300)]
lead = (mem[mem.l3_name.isin(cand.l3)].assign(mv=lambda x: db.reindex(x.ts_code).mv.values)
        .sort_values("mv", ascending=False).groupby("l3_name").head(3).dropna(subset=["mv"]))
codes = lead.ts_code.tolist(); IN = ",".join(repr(x) for x in codes)
rc = q(f"SELECT ts_code, report_date, org_name, quarter, np FROM curated.report_rc WHERE ts_code IN ({IN}) AND quarter='2027Q4' AND report_date>='20260501'")
cons = lambda d0, d1: rc[(rc.report_date > d0) & (rc.report_date <= d1)].sort_values("report_date").groupby(["ts_code", "org_name"]).np.last().groupby("ts_code").median() / 1e4
c27, c27o = cons("20260816", AS_OF), cons("20260501", "20260816")
pbs = {k: (g.pb < db.pb.get(k, np.nan)).mean() for k, g in pbh[pbh.ts_code.isin(codes)].groupby("ts_code")}
r = q(f"SELECT trade_date, ts_code, pct_chg FROM curated.daily WHERE ts_code IN ({IN}) AND trade_date>'20251116'").pivot(index="trade_date", columns="ts_code", values="pct_chg")
m = q("SELECT trade_date, pct_chg m FROM curated.index_daily WHERE ts_code='000300.SH' AND trade_date>'20251116'").set_index("trade_date").m
sc = q("SELECT trade_date, settle FROM curated.fut_daily WHERE ts_code='SC.INE' AND trade_date>'20251110' ORDER BY 1").set_index("trade_date").settle.pct_change() * 100
cl = TushareClient(cfg.tushare, Clock())
y = cl.query("us_tycr", {"start_date": "20251101", "end_date": AS_OF}, ["date", "y10"]).dropna().sort_values("date")
y["dy"] = y.y10.astype(float).diff() * 100; y["d"] = pd.to_datetime(y.date)
cal = pd.DataFrame({"d": pd.to_datetime(m.index)}).sort_values("d")
dy = pd.merge_asof(cal, y[["d", "dy"]].rename(columns={"d": "ud"}), left_on="d", right_on="ud", allow_exact_matches=False)
dy = pd.Series(dy.dy.values, index=m.index, name="dy")

def beta(code, f):
    d = pd.concat([r.get(code), m, f], axis=1).dropna()
    if len(d) < 120:
        return np.nan, np.nan
    X = np.column_stack([np.ones(len(d)), d.m, d.iloc[:, 2]]); b, *_ = np.linalg.lstsq(X, d.iloc[:, 0], rcond=None)
    e = d.iloc[:, 0] - X @ b; se = np.sqrt(e @ e / (len(d) - 3) * np.linalg.inv(X.T @ X)[2, 2])
    return round(b[2], 2), round(b[2] / se, 1)

out = []
for _, x in lead.iterrows():
    k = x.ts_code
    d = cl.query("cyq_perf", {"ts_code": k, "trade_date": AS_OF}, [])
    cy = d.iloc[0] if not d.empty else {}
    close = q(f"SELECT close FROM curated.daily WHERE ts_code='{k}' AND trade_date='{AS_OF}'").close
    ob, ot = beta(k, sc.rename("sc")); rb, rt = beta(k, dy * 0.1)  # per 10bp
    out.append(dict(l3=x.l3_name, name=x["name"], code=k, mv=round(x.mv), close=close.iloc[0] if len(close) else np.nan,
                    pe27=round(x.mv / c27[k], 1) if k in c27 and c27[k] > 0 else np.nan,
                    rev27_3m=round((c27[k] / c27o[k] - 1) * 100) if k in c27 and k in c27o and c27o[k] > 0 else np.nan,
                    pb_pct=round(pbs.get(k, np.nan), 2), gauge=round(gauge.get(k, np.nan), 2),
                    winner=round(float(cy["winner_rate"]), 1) if len(cy) else np.nan,
                    cost15=round(float(cy["cost_15pct"]), 2) if len(cy) else np.nan, cost50=round(float(cy["cost_50pct"]), 2) if len(cy) else np.nan,
                    oil_b=ob, oil_t=ot, us10y_b=rb, us10y_t=rt))
L = pd.DataFrame(out).merge(cand[["l3", "bucket", "yoy_q3", "ttm_vs_peak", "pb_pct"]].rename(columns={"pb_pct": "ind_pb_pct"}), on="l3")
L["veto"] = L.gauge >= 0.9
L["below_cost50"] = L.close <= L.cost50
L.to_csv(OUT / "leaders.csv", index=False)
print(cand.sort_values(["bucket", "pb_pct"]).to_string(index=False))
print(L.to_string(index=False))
