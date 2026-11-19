"""Backtest of the watchlist buy conditions: RetailGauge <= 0.3 and large-order (20-100万) weeks positive in the last 4 ISO weeks,
at quarter ends 2022Q1-2026Q3 (gauge = point-in-time walk-forward v5), float cap >= 50亿. Forward 20/60/120-session excess return
vs the universe mean. Also inside a 'buy zone' proxy (winner rate <= 50% or >= 20% off the 1y high)."""
import duckdb, pandas as pd, numpy as np
L="/Volumes/Treasury/quant_cn_lake/curated"; M="/Volumes/Treasury/quant_cn_lake/meta/runs"
OUT=f"{M}/research/20261115_watch_conditions_bt"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
g=pd.read_parquet(f"{M}/research/20261113_retail_gauge_returns/gauge_walkforward.parquet"); g=g[g.q!="20261112"]
cal=q(f"select distinct trade_date from {s('daily')} where trade_date>='20211001' order by 1").trade_date.tolist()
sig={qq:max(d for d in cal if d<=qq) for qq in sorted(g.q.unique())}           # last session on/before quarter end
px=q(f"select d.ts_code,d.trade_date,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='20210901'").pivot(index="trade_date",columns="ts_code",values="c").sort_index()
cmv=q(f"select ts_code,trade_date,circ_mv/1e4 cmv from {s('daily_basic')} where trade_date in {tuple(sig.values())}").pivot(index="trade_date",columns="ts_code",values="cmv")
mf=q(f"select ts_code,trade_date,(buy_lg_amount-sell_lg_amount)/1e4 lg, (buy_lg_amount+buy_elg_amount-sell_lg_amount-sell_elg_amount)/1e4 lgx from {s('moneyflow')} where trade_date>='20211101'")
mf["dt"]=pd.to_datetime(mf.trade_date,format="%Y%m%d"); mf["wk"]=mf.dt.dt.strftime("%G-%V")
cy=pd.read_parquet(f"{M}/holder_nowcast/cyq_qe.parquet")
hi=px.rolling(250,min_periods=200).max()
rows=[]
for qq,d in sig.items():
    i=px.index.get_loc(d)
    f=pd.DataFrame({"cmv":cmv.loc[d] if d in cmv.index else np.nan,"dd":px.loc[d]/hi.loc[d]-1})
    for h in (20,60,120):
        if i+h<len(px): f[f"r{h}"]=px.iloc[i+h]/px.loc[d]-1
    start=(pd.Timestamp(d)-pd.Timedelta(days=40)).strftime("%Y%m%d")
    w=mf[(mf.trade_date>start)&(mf.trade_date<=d)].groupby(["ts_code","wk"])[["lg","lgx"]].sum().groupby(level=0).tail(4)
    f["lgw"]=w.groupby(level=0).lg.apply(lambda x:(x>0).sum()); f["lg4"]=w.groupby(level=0).lg.sum(); f["lgx4"]=w.groupby(level=0).lgx.sum()
    gg=g[g.q==qq].set_index("ts_code"); f["gauge"]=gg.gauge
    c=cy[cy.trade_date==max(t for t in cy.trade_date.unique() if t<=d)].set_index("ts_code"); f["win"]=c.winner_rate
    f=f[(f.cmv>=50)&f.gauge.notna()&f.lgw.notna()]; f["q"]=qq
    for h in (20,60,120):
        if f"r{h}" in f: f[f"x{h}"]=f[f"r{h}"]-f[f"r{h}"].mean()
    rows.append(f)
E=pd.concat(rows); E.to_parquet(f"{OUT}/panel.parquet")
print("obs",len(E),"quarters",E.q.nunique(),"| with 60d:",E.x60.notna().sum(),"quarters",E[E.x60.notna()].q.nunique())
def st(name,m,base=None):
    out={"组":name,"样本":int(m.sum()),"占比%":round(m.mean()*100,1)}
    for h in (20,60,120):
        x=E.loc[m,f"x{h}"].dropna(); out[f"x{h}%"]=round(x.mean()*100,2)
        if h==60: out["x60中位%"]=round(x.median()*100,2); out["x60胜率"]=round((x>0).mean(),2)
    # per-quarter difference in 60d vs complement within base
    b=base if base is not None else pd.Series(True,index=E.index)
    pq=E[b&E.x60.notna()].assign(m=m[b&E.x60.notna()]).groupby("q").apply(lambda z: z[z.m].x60.mean()-z[~z.m].x60.mean() if z.m.sum()>=5 and (~z.m).sum()>=5 else np.nan).dropna()
    out["vs其余 60d差%"]=round(pq.mean()*100,2); out["t"]=round(pq.mean()/pq.std()*np.sqrt(len(pq)),2) if len(pq)>2 else np.nan; out["正季数"]=f"{(pq>0).sum()}/{len(pq)}"
    return out
G=E.gauge<=0.3; W2=E.lgw>=2; W3=E.lgw>=3; S=E.lg4>0; SX=E.lgx4>0; HOT=E.gauge>=0.9
allm=pd.Series(True,index=E.index)
res=[st("全部",allm),st("温度计≤0.3",G),st("温度计≥0.9（回避组）",HOT),st("大单≥2周流入",W2),st("大单≥3周流入",W3),st("大单4周合计>0",S),st("大+特大单4周合计>0",SX),
     st("温度计≤0.3 且 大单≥2周（现规则）",G&W2),st("温度计≤0.3 且 大单≥3周",G&W3),st("温度计≤0.3 且 4周合计>0",G&S),st("温度计≤0.3 且 大单<2周",G&~W2)]
pd.set_option("display.width",300); pd.set_option("display.max_columns",20)
print("\n== 全样本（流通≥50亿，季末信号）=="); print(pd.DataFrame(res).to_string(index=False))
# conditional effect of flow within gauge<=0.3
print("\n== 在温度计≤0.3 内部：大单条件的增量 ==")
print(pd.DataFrame([st("≥2周 vs <2周",W2,G),st("≥3周 vs <3周",W3,G),st("4周合计>0 vs ≤0",S,G)]).to_string(index=False))
Z=(E.win<=50)|(E.dd<=-0.2)
print("\n== 买入区代理（获利盘≤50% 或 距1年高点≤-20%）内部 ==")
print(pd.DataFrame([st("区内全部",Z,Z),st("区内+温度计≤0.3",Z&G,Z),st("区内+大单≥2周",Z&W2,Z),st("区内+两条都满足（现规则）",Z&G&W2,Z),st("区内+温度计≤0.3+4周合计>0",Z&G&S,Z),st("区内+温度计≥0.9",Z&HOT,Z)]).to_string(index=False))
