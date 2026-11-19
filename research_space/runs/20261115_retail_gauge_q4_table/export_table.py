"""Per-company 2026-12-31 shareholder-count forecast table from RetailGauge v5 (as-of 2026-11-12 nowcast)."""
import pandas as pd, numpy as np, yaml
S="/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
OUT="/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_retail_gauge_q4_table"
f=pd.read_parquet(f"{S}/holders_forecast_q4.parquet")
sb=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/curated/reference/stock_basic.parquet")[["ts_code","name","industry"]].set_index("ts_code")
pos={p["code"] for p in yaml.safe_load(open("config/local.positions.yaml"))["positions"]}
t=f.join(sb,how="left")
lab={0:"明显减少",1:"减少",2:"小幅减少",3:"小幅减少",4:"持平",5:"持平",6:"小幅增加",7:"增加",8:"明显增加",9:"大幅增加(散户过热)"}
t["方向"]=t.dec.map(lab)
t["中位变化%"]=(np.exp(t["50%"]+t.mk_q4)-1)*100; t["区间低%"]=(np.exp(t["25%"]+t.mk_q4)-1)*100; t["区间高%"]=(np.exp(t["75%"]+t.mk_q4)-1)*100
t["持仓"]=t.index.isin(pos)
o=t.reset_index().rename(columns={"ts_code":"代码","name":"名称","industry":"行业","pct":"预测分位","dec":"十分组","h_q3":"Q3户数","h_exp":"Q4预测户数","h_lo":"Q4预测低","h_hi":"Q4预测高"})
o=o[["代码","名称","行业","持仓","十分组","预测分位","方向","Q3户数","Q4预测户数","Q4预测低","Q4预测高","中位变化%","区间低%","区间高%"]].sort_values("预测分位",ascending=False)
for c in ["Q3户数","Q4预测户数","Q4预测低","Q4预测高"]: o[c]=o[c].round(-1).astype("Int64")
for c in ["预测分位","中位变化%","区间低%","区间高%"]: o[c]=o[c].round(3 if c=="预测分位" else 1)
o.to_csv(f"{OUT}/retail_gauge_q4_20261231.csv",index=False,encoding="utf-8-sig")
pd.set_option("display.width",250); pd.set_option("display.max_columns",20)
print(o.shape, "missing Q3 count:", o["Q3户数"].isna().sum())
print(o.groupby("十分组").size().to_dict())
print("== 持仓 =="); print(o[o.持仓].drop(columns=["持仓","行业"]).to_string(index=False))
print("== 预测增加最多 top15 (有Q3户数) =="); print(o[o["Q3户数"].notna()].head(15).drop(columns=["持仓"]).to_string(index=False))
print("== 预测减少最多 bottom10 =="); print(o[o["Q3户数"].notna()].tail(10).drop(columns=["持仓"]).to_string(index=False))
