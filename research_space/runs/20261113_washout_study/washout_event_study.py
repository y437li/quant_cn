"""下杀 / 筹码洗盘 indicators: event study since 2021 and current status."""
import duckdb, pandas as pd, numpy as np
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root); L = str(LAKE / "curated")
S = str(LAKE / "meta/runs/research/20261113_washout_study"); Path(S).mkdir(parents=True, exist_ok=True)
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda sql: duckdb.sql(sql).df()
px=q(f"select d.ts_code,d.trade_date,d.close*a.adj_factor c from {s('daily')} d join {s('adj_factor')} a on d.ts_code=a.ts_code and d.trade_date=a.trade_date where d.trade_date>='20200101'").pivot(index="trade_date",columns="ts_code",values="c").sort_index()
tv=q(f"select ts_code,trade_date,turnover_rate_f t, circ_mv from {s('daily_basic')} where trade_date>='20200101'")
cm=tv.pivot(index="trade_date",columns="ts_code",values="circ_mv").reindex(index=px.index,columns=px.columns)
tv=tv.pivot(index="trade_date",columns="ts_code",values="t").reindex(index=px.index,columns=px.columns)
mg=q(f"select ts_code,trade_date,rzye from {s('margin_detail')} where trade_date>='20200101'").pivot(index="trade_date",columns="ts_code",values="rzye").reindex(index=px.index,columns=px.columns)
hi=px.rolling(250,min_periods=200).max(); dd=px/hi-1
tov120=tv.rolling(120,min_periods=100).sum()                    # % of free float traded in 120d
dry=tv.rolling(5).mean()/tv.rolling(60,min_periods=50).mean()   # volume dry-up
base=(px.rolling(10).min()>px.rolling(60).min())                # 60d low set >10 sessions ago
mflush=mg/mg.rolling(250,min_periods=120).max()-1
fwd=px.shift(-60)/px-1; mkt=fwd.mean(axis=1); xf=fwd.sub(mkt,axis=0)
me=pd.Series(px.index,index=px.index).groupby(px.index.str[:6]).last().values
me=[d for d in me if "20210101"<=d<="20260815"]
big=(cm>=50e4)
rows=[]
for d in me:
    m=big.loc[d]&xf.loc[d].notna()
    f=pd.DataFrame({"dd":dd.loc[d],"tov":tov120.loc[d],"dry":dry.loc[d],"base":base.loc[d],"mf":mflush.loc[d],"x":xf.loc[d]})[m]
    f["date"]=d; rows.append(f)
E=pd.concat(rows)
def stat(name,m):
    g=E[m]; return {"组":name,"样本":len(g),"每月平均只数":round(len(g)/len(me),1),"60日超额均值%":round(g.x.mean()*100,2),"中位%":round(g.x.median()*100,2),"跑赢比例":round((g.x>0).mean(),2)}
k=E.dd<=-0.35
tq=E.tov>=E.groupby("date").tov.transform(lambda s:s.quantile(0.5))
res=[stat("全部(流通≥50亿)",E.dd.notna()),stat("下杀: 距一年高点≤-35%",k),
 stat("下杀+止跌(60日低点在10日前)",k&E.base),stat("下杀+缩量(5日/60日换手≤0.6)",k&(E.dry<=0.6)),
 stat("下杀+换手充分(120日换手≥中位)",k&tq),stat("下杀+融资出清(≤-30%)",k&(E.mf<=-0.3)),
 stat("下杀+止跌+缩量",k&E.base&(E.dry<=0.6)),stat("下杀+止跌+缩量+融资出清",k&E.base&(E.dry<=0.6)&(E.mf<=-0.3)),
 stat("下杀+止跌+缩量+融资出清+换手充分",k&E.base&(E.dry<=0.6)&(E.mf<=-0.3)&tq)]
pd.set_option("display.width",250); print(pd.DataFrame(res).to_string(index=False))
d=px.index[-1]; cur=pd.DataFrame({"dd":dd.loc[d],"tov120":tov120.loc[d],"dry":dry.loc[d],"base":base.loc[d],"mf":mflush.loc[d],"cmv":cm.loc[d]/1e4})
cur["tov_med"]=cur.loc[cur.cmv>=50,"tov120"].median()
cur.to_parquet(f"{S}/washout_now.parquet"); print("as of",d,"| 流通≥50亿中距高点≤-35%:",int(((cur.cmv>=50)&(cur.dd<=-0.35)).sum()),"/",int((cur.cmv>=50).sum()))

# ---- chip conditions: announced holder change (PIT), 20d large-order flow, quarter-end winner rate ----
hn=q(f"""select ts_code,end_date,min(ann_date) ann,arg_min(holder_num,ann_date) n from {s('events/stk_holdernumber')}
  where end_date>='20191231' and ann_date is not null group by 1,2""").sort_values(["ts_code","end_date"])
hn["chg"]=hn.groupby("ts_code").n.pct_change()
hn=hn.dropna(subset=["chg"]); hn["di"]=hn.ann.astype(int); hn=hn.sort_values("di")
ev=E.reset_index().rename(columns={"index":"ts_code","ts_code":"ts_code"})
ev=ev.rename(columns={ev.columns[0]:"ts_code"}); ev["di"]=ev.date.astype(int); ev=ev.sort_values("di")
ev=pd.merge_asof(ev,hn[["ts_code","di","end_date","chg"]],on="di",by="ts_code",direction="backward")
ev=ev[pd.to_datetime(ev.date)-pd.to_datetime(ev.end_date)<=pd.Timedelta(days=200)]
lg=q(f"select ts_code,trade_date,(buy_lg_amount-sell_lg_amount) f from {s('moneyflow')} where trade_date>='20200101'").pivot(index="trade_date",columns="ts_code",values="f").reindex(index=px.index,columns=px.columns)
lg20=(lg.rolling(20,min_periods=15).sum()/cm).stack().rename("lg20")   # 万/万 = share of float cap
ev=ev.join(lg20,on=["date","ts_code"])
E2=ev; k=E2.dd<=-0.35
def st(name,m):
    g=E2[m]; return {"组":name,"样本":len(g),"每月只数":round(len(g)/len(me),1),"60日超额均值%":round(g.x.mean()*100,2),"中位%":round(g.x.median()*100,2),"跑赢比例":round((g.x>0).mean(),2)}
r=[st("全部(有户数数据)",E2.dd.notna()),st("下杀",k),st("下杀+户数降≥5%",k&(E2.chg<=-0.05)),st("下杀+户数降≥10%",k&(E2.chg<=-0.10)),
   st("下杀+户数升≥10%(散户抄底)",k&(E2.chg>=0.10)),st("下杀+大单20日净流入",k&(E2.lg20>0)),
   st("下杀+户数降≥5%+大单净流入",k&(E2.chg<=-0.05)&(E2.lg20>0)),st("下杀+户数降≥5%+大单净流入+止跌",k&(E2.chg<=-0.05)&(E2.lg20>0)&E2.base),
   st("不下杀+户数降≥5%+大单净流入",(E2.dd>-0.35)&(E2.chg<=-0.05)&(E2.lg20>0))]
print(pd.DataFrame(r).to_string(index=False))
# quarter-end winner rate (cyq_qe) after a 下杀
cy=pd.read_parquet(str(LAKE / "meta/runs/holder_nowcast/cyq_qe.parquet"))
print("cyq_qe cols",list(cy.columns)[:12])

# ---- quarter-end chip distribution after a 下杀 ----
cy["d"]=cy.trade_date.astype(str); rows=[]
for d,g in cy.groupby("d"):
    if d not in px.index or d>"20260815": continue
    g=g.set_index("ts_code"); f=pd.DataFrame({"dd":dd.loc[d],"x":xf.loc[d],"big":big.loc[d],"p":px.loc[d]}).join(g[["winner_rate","cost_15pct","cost_50pct","cost_85pct","cost_95pct"]],how="inner")
    raw=q(f"select ts_code, close from {s('daily')} where trade_date='{d}'").set_index("ts_code").close
    f=f.join(raw.rename("close")); f["date"]=d; rows.append(f[f.big&f.x.notna()])
C=pd.concat(rows); C["band"]=(C.cost_85pct-C.cost_15pct)/C.cost_50pct; C["trap"]=C.cost_95pct/C.close-1
k=C.dd<=-0.35; nq=C.date.nunique()
def st(name,m):
    g=C[m]; return {"组":name,"样本":len(g),"每季只数":round(len(g)/nq,1),"60日超额均值%":round(g.x.mean()*100,2),"中位%":round(g.x.median()*100,2),"跑赢比例":round((g.x>0).mean(),2)}
r=[st("季末全部",C.dd.notna()),st("下杀",k),st("下杀+获利盘≤10%",k&(C.winner_rate<=10)),st("下杀+获利盘10-30%",k&C.winner_rate.between(10,30)),st("下杀+获利盘>30%",k&(C.winner_rate>30)),
   st("下杀+筹码集中(70%区间≤中位)",k&(C.band<=C.groupby("date").band.transform("median"))),st("下杀+上方套牢≤30%(cost95/价)",k&(C.trap<=0.3)),st("下杀+上方套牢>60%",k&(C.trap>0.6))]
print(f"\nquarter ends: {nq}"); print(pd.DataFrame(r).to_string(index=False))

# ---- combine winner rate with announced holder change and large orders (quarter ends) ----
C=C.reset_index().rename(columns={"index":"ts_code"}); C["di"]=C.date.astype(int); C=C.sort_values("di")
C=pd.merge_asof(C,hn[["ts_code","di","chg"]],on="di",by="ts_code",direction="backward").join(lg20,on=["date","ts_code"])
k=C.dd<=-0.35; w=C.winner_rate<=10
r=[st("下杀+获利盘≤10%",k&w),st("  +户数降≥5%",k&w&(C.chg<=-0.05)),st("  +户数升≥5%",k&w&(C.chg>=0.05)),st("  +大单20日净流入",k&w&(C.lg20>0)),st("  +大单20日净流出",k&w&(C.lg20<=0))]
print(pd.DataFrame(r).to_string(index=False))
import os, requests
tok=os.environ["TUSHARE_TOKEN"]; out=[]; off=0
while True:
    j=requests.post("http://api.tushare.pro",json={"api_name":"cyq_perf","token":tok,"params":{"trade_date":"20261112","offset":off,"limit":5000},"fields":"ts_code,winner_rate,cost_15pct,cost_50pct,cost_85pct,cost_95pct"},timeout=60).json()
    it=j["data"]["items"]; out+=it
    if len(it)<5000: break
    off+=5000
cn=pd.DataFrame(out,columns=j["data"]["fields"]).set_index("ts_code"); cn.to_parquet(f"{S}/cyq_20261112.parquet")
now=pd.read_parquet(f"{S}/washout_now.parquet").join(cn); now=now[now.cmv>=50]
k=now.dd<=-0.35
print("\n11-12 流通≥50亿:",len(now),"| 下杀(≤-35%):",int(k.sum()),"| 下杀+获利盘≤10%:",int((k&(now.winner_rate<=10)).sum()),"| 下杀+获利盘>30%(还没杀透):",int((k&(now.winner_rate>30)).sum()))
now.to_parquet(f"{S}/washout_now.parquet")
