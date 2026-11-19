"""Compare the gap IC with forward EP, trailing EP, PEG and the controls (fwd20); gap of the 2026 tech leaders on 2026-06-30. Reads the panel written by pricing_gap_factor.py."""
import pandas as pd, numpy as np
p=pd.read_parquet("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261118_linear_pricing_gap/panel_0.7_15.parquet")
p["peg"]=-p["fep"]/p["grow"].where(p["grow"]>0)  # PE/growth-ish (higher = dearer)
for c in ["gap","fep","tep","peg","rev20","mom","turn","size"]:
    s=p.dropna(subset=["fwd20",c]).groupby("date").apply(lambda f:f[c].rank().corr(f["fwd20"].rank()))
    print(c, round(s.mean(),4), "t", round(s.mean()/s.std()*np.sqrt(len(s)),2))
# top decile by gap: share of tech? and gap among 2026-06 leaders
x=p[p.date=="20260630"].set_index("ts_code")
print(x.loc[[c for c in ["300308.SZ","300502.SZ","601138.SH","603986.SH","688256.SH","688041.SH","688981.SH","002371.SZ"] if c in x.index],["gap"]].round(2).assign(pct=lambda f: x["gap"].rank(pct=True).reindex(f.index).round(2)))
