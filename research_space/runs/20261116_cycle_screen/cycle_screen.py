"""Ad-hoc: cycle position of cyclical SW L2/L3 industries (profit vs peak, turn, PB percentile, drawdown)."""
import duckdb, pandas as pd, numpy as np
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261116_cycle_screen"; OUT.mkdir(parents=True, exist_ok=True)
CATALOG = str(LAKE / "meta/quant_cn.duckdb")

pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300)
c = duckdb.connect(CATALOG, read_only=True); q = lambda s: c.execute(s).df()
CYC = ['农林牧渔','基础化工','钢铁','有色金属','电子','汽车','建筑材料','建筑装饰','电力设备','机械设备','煤炭','石油石化','交通运输','房地产','轻工制造','家用电器','纺织服饰','公用事业']
mem = q("SELECT l1_name,l2_code,l2_name,l3_name,ts_code FROM curated.index_member_all WHERE out_date IS NULL")
mem = mem[mem.l1_name.isin(CYC)]
inc = q("""SELECT ts_code,end_date,arg_max(n_income_attr_p,ann_date) np FROM curated.income_vip WHERE report_type='1' AND end_date>='20170101' GROUP BY 1,2""")
inc = inc[inc.ts_code.isin(mem.ts_code)].copy()
inc["y"] = inc.end_date.str[:4]; inc = inc.sort_values(["ts_code","end_date"])
inc["sq"] = inc.np - inc.groupby(["ts_code","y"]).np.shift().fillna(0)
inc.loc[inc.end_date.str[4:]=="0331","sq"] = inc.np
# require full quarter set: drop firms missing quarters in a year -> approximate by keeping as is
sq = inc.pivot_table(index="ts_code", columns="end_date", values="sq")
qs = [d for d in sq.columns if d[4:] in ("0331","0630","0930","1231")]
sq = sq[qs]
mb = q("SELECT ts_code,total_mv,pb FROM curated.daily_basic WHERE trade_date='20261116'")
pbh = q("""WITH m AS (SELECT ts_code, strftime(strptime(trade_date,'%Y%m%d'),'%Y%m') ym, arg_max(total_mv,trade_date) mv, arg_max(pb,trade_date) pb FROM curated.daily_basic WHERE trade_date>='20160101' GROUP BY 1,2) SELECT * FROM m""")
pbh = pbh[pbh.pb > 0].merge(mem[["ts_code","l2_name","l3_name"]], on="ts_code"); pbh["bk"] = pbh.mv/pbh.pb
def block(level):
    rows = []
    for key, g in mem.groupby(["l1_name", level]):
        codes = g.ts_code
        s = sq.reindex(codes).sum(min_count=1)
        s = s[s.index >= "20180101"]
        ttm = s.rolling(4).sum().dropna()
        if len(ttm) < 8: continue
        last = "20260930"
        yoy = lambda d: (s[d] - s[str(int(d[:4])-1)+d[4:]]) / abs(s[str(int(d[:4])-1)+d[4:]])
        h = pbh[pbh[level] == key[1]].groupby("ym").agg(mv=("mv","sum"), bk=("bk","sum")); h["pb"] = h.mv/h.bk
        pb_now = h.pb.iloc[-1]; pct = (h.pb < pb_now).mean()
        rows.append(dict(l1=key[0], ind=key[1], n=len(codes), mv_yi=round(mb[mb.ts_code.isin(codes)].total_mv.sum()/1e4),
            ttm_yi=round(ttm[last]/1e8,1), peak_yi=round(ttm.max()/1e8,1), peak_q=ttm.idxmax()[:6], ttm_vs_peak=round(ttm[last]/ttm.max(),2),
            yoy_q1=round(yoy("20260331"),2), yoy_q2=round(yoy("20260630"),2), yoy_q3=round(yoy("20260930"),2),
            pb=round(pb_now,2), pb_pct=round(pct,2)))
    return pd.DataFrame(rows)
for level in ("l2_name", "l3_name"):
    out = block(level)
    out.to_csv(OUT / f"cycle_{level[:2]}.csv", index=False)
    print(out.sort_values(["l1", "ind"]).to_string(index=False))
