"""筹码干净 screen as of the latest lake date: retail leaving (announced + RetailGauge), concentrated cost band, large-order inflow.
Two shapes: A 集中控盘 (narrow band, price at/above most cost) and B 下杀洗透 (≥35% off 1y high, winner rate ≤10%)."""
import duckdb, pandas as pd, numpy as np, yaml
L="/Volumes/Treasury/quant_cn_lake/curated"; OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_clean_chips"
s=lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q=lambda x: duckdb.sql(x).df()
d=q(f"select max(trade_date) d from {s('cyq_perf')}").d[0]
td=q(f"select distinct trade_date from {s('daily')} where trade_date<='{d}' order by 1 desc limit 260").trade_date.tolist()
d60=td[60]; d20=td[19]
cy=q(f"select ts_code,trade_date,cost_5pct,cost_15pct,cost_50pct,cost_85pct,cost_95pct,winner_rate,weight_avg from {s('cyq_perf')} where trade_date in ('{d}','{d60}')")
c=cy[cy.trade_date==d].set_index("ts_code"); c0=cy[cy.trade_date==d60].set_index("ts_code")
c["band"]=(c.cost_85pct-c.cost_15pct)/c.cost_50pct; c["band60"]=(c0.cost_85pct-c0.cost_15pct)/c0.cost_50pct
db=q(f"select ts_code,close,circ_mv/1e4 cmv from {s('daily_basic')} where trade_date='{d}'").set_index("ts_code")
px=q(f"select d.ts_code,max(d.close*a.adj_factor) hi, arg_max(d.close*a.adj_factor,d.trade_date) lastpx from {s('daily')} d join {s('adj_factor')} a using(ts_code,trade_date) where d.trade_date>='{td[-1]}' and d.trade_date<='{d}' group by 1").set_index("ts_code")
lg=q(f"select m.ts_code,sum(buy_lg_amount+buy_elg_amount-sell_lg_amount-sell_elg_amount) f from {s('moneyflow')} m where trade_date>='{d20}' and trade_date<='{d}' group by 1").set_index("ts_code")
hn=q(f"""with h as (select ts_code,end_date,arg_max(holder_num,ann_date) n from {s('events/stk_holdernumber')} where end_date in ('20260630','20260930') group by 1,2)
  select ts_code, max(n) filter (where end_date='20260930') n3, max(n) filter (where end_date='20260630') n2 from h group by 1""").set_index("ts_code")
rg=pd.read_csv("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_retail_gauge_q4_table/retail_gauge_q4_20261231.csv",dtype={"代码":str}).set_index("代码")
sb=pd.read_parquet(f"{L}/reference/stock_basic.parquet").set_index("ts_code")[["name","industry"]]
t=db.join(c).join(px).join(lg).join(hn).join(rg[["十分组","中位变化%"]]).join(sb)
t["dd"]=t["lastpx"]/t.hi-1; t["trap"]=t.cost_95pct/t.close-1; t["px_cost"]=t.close/t.weight_avg-1
t["lg20"]=t.f/(t.cmv*1e4)*100      # % of float cap
t["hq3"]=t.n3/t.n2-1; t["dband"]=t.band-t.band60
t=t[(t.cmv>=50)&~t.name.str.contains("ST",na=False)]
bq=t.band.rank(pct=True)
retail_out=(t.hq3<=-0.05)&(t["十分组"]<=3)
A=t[retail_out&(bq<=0.30)&(t.dband<0)&(t.trap<=0.15)&(t.lg20>0)]
B=t[retail_out&(t.dd<=-0.35)&(t.winner_rate<=10)&(t.lg20>0)]
cols={"name":"名称","industry":"行业","cmv":"流通市值亿","hq3":"Q3户数变化","十分组":"Q4温度计组","中位变化%":"Q4预测变化%","band":"70%筹码带宽","dband":"带宽60日变化","winner_rate":"获利盘%","px_cost":"价/均成本-1","trap":"上方套牢(cost95/价-1)","dd":"距1年高点","lg20":"20日大单净流入%流通"}
fmt=lambda x: x[list(cols)].rename(columns=cols).round({"流通市值亿":0,"Q3户数变化":3,"70%筹码带宽":3,"带宽60日变化":3,"获利盘%":1,"价/均成本-1":3,"上方套牢(cost95/价-1)":3,"距1年高点":3,"20日大单净流入%流通":2})
pos=[p["code"] for p in yaml.safe_load(open("config/local.positions.yaml"))["positions"]]
pd.set_option("display.width",300); pd.set_option("display.max_columns",30); pd.set_option("display.max_rows",200)
print("as of",d,"| universe 流通≥50亿 non-ST:",len(t),"| retail leaving:",int(retail_out.sum()),"| band 30th pct:",round(t.band.quantile(.3),3))
print(f"\n== A 集中控盘: {len(A)} =="); print(fmt(A.sort_values("band")).to_string())
print(f"\n== B 下杀洗透: {len(B)} =="); print(fmt(B.sort_values("lg20",ascending=False)).to_string())
print("\n== 持仓 =="); print(fmt(t.reindex(pos)).to_string())
fmt(A).to_csv(f"{OUT}/A_concentrated_{d}.csv",encoding="utf-8-sig"); fmt(B).to_csv(f"{OUT}/B_washed_{d}.csv",encoding="utf-8-sig")
fmt(t).to_csv(f"{OUT}/all_chip_metrics_{d}.csv",encoding="utf-8-sig")
# ---- scored version: 6 conditions, keep ≥5 ----
cond=pd.DataFrame({"户数降":t.hq3<=-0.05,"温度计≤3":t["十分组"]<=3,"带宽窄":bq<=0.30,"带宽收窄":t.dband<0,"大单流入":t.lg20>0,"套牢少":t.trap<=0.20})
t["score"]=cond.sum(axis=1); t["缺"]=cond.apply(lambda r: ",".join(k for k,v in r.items() if not v),axis=1)
S5=t[t.score>=5].sort_values(["score","band"],ascending=[False,True])
print(f"\n== 评分 6 项满足≥5: {len(S5)} (6/6: {int((t.score==6).sum())}) ==")
print(pd.concat([fmt(S5),S5[["score","缺"]]],axis=1).to_string())
pd.concat([fmt(S5),S5[["score","缺"]]],axis=1).to_csv(f"{OUT}/scored_ge5_{d}.csv",encoding="utf-8-sig")
