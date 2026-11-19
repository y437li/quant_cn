"""Has 中证1000 bottomed? Base rates 2010-2026 for days like 2026-11-18: drawdown from the 250-session high <= -30%
and 20-day realised vol in the top 15% of its trailing 250 sessions. Forward 20/60/120-session returns and the further
fall below the signal-day close; one episode = first signal day after 60 sessions without a signal."""
import duckdb, pandas as pd, numpy as np
P=duckdb.sql("select trade_date,close from read_parquet('/Volumes/Treasury/quant_cn_lake/curated/reference/index_daily.parquet') "
             "where ts_code='000852.SH' order by 1").df().set_index("trade_date").close
r=np.log(P).diff(); rv=r.rolling(20).std()*np.sqrt(252)
pct=rv.rolling(250).apply(lambda x:(x<=x[-1]).mean(),raw=True)
dd=P/P.rolling(250,min_periods=1).max()-1
sig=(dd<=-0.30)&(pct>=0.85)
rows=[];last=-999
for i,(d,s) in enumerate(sig.items()):
    if not s: continue
    if i-last>60:
        out={"date":d,"close":P.iloc[i],"dd":dd.iloc[i],"rv":rv.iloc[i]}
        for h in (20,60,120):
            seg=P.iloc[i:i+h+1]
            out[f"r{h}"]=seg.iloc[-1]/P.iloc[i]-1 if len(seg)>h else np.nan
            out[f"low{h}"]=seg.min()/P.iloc[i]-1
        rows.append(out)
    last=i
T=pd.DataFrame(rows); pd.set_option("display.width",200)
print(T.round(3).to_string(index=False))
print("now: dd",round(dd.iloc[-1],3),"rv pct",round(pct.iloc[-1],3),"signal",bool(sig.iloc[-1]))
