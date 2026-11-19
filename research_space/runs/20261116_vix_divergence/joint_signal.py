"""Buy points where two conditions hold together for 中证1000:
 A = own 20-day realized vol ≥ 90th pct of trailing 3 years, B = realized gap (1000 − 300) ≥ 90th pct, C = option VIX ≥ 90th pct of its
history (since 2022-07). Joint signals A&B (2016..) and A&C (2022-07..). Episodes start ≥ 20 sessions apart. Per episode: 20 / 60 /
120-day return, worst within 60, and the 'pct < 70% of gap or 60 days' exit result from exit_rules.py. Data as in high_vol_entry.py."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache"); OUT = Config.load().lake.root / "meta/runs/research/20261116_vix_divergence"
cl = {}
for code, f in (("c1000", "000852_SH_5min.csv"), ("c300", "000300_SH_5min.csv")):
    b = pd.read_csv(SRC / f, usecols=["trade_time", "close", "trade_date"]); cl[code] = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
P = pd.DataFrame(cl).dropna(); P.index = P.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select ts_code, trade_date, pct_chg from read_parquet('/Volumes/Treasury/quant_cn_lake/curated/fund_daily/**/*.parquet', hive_partitioning=true) where ts_code in ('512100.SH','510300.SH') and trade_date > '{P.index[-1]}'").df()
g = (1 + e.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index() / 100).cumprod()
P = pd.concat([P, pd.DataFrame({"c1000": P.c1000.iloc[-1] * g["512100.SH"], "c300": P.c300.iloc[-1] * g["510300.SH"]})])
R = np.log(P / P.shift(1)); rv = R.rolling(20).std() * np.sqrt(252) * 100
pc = lambda s: s.rolling(750, min_periods=250).apply(lambda x: (x <= x[-1]).mean(), raw=True)
A = pc(rv.c1000.dropna()); gap = (rv.c1000 - rv.c300).dropna(); B = pc(gap)
iv = pd.read_csv(OUT / "vix_lines.csv", index_col=0); iv.index = iv.index.astype(str); v = iv.cn_1000.dropna()
Cp = v.expanding(min_periods=120).apply(lambda x: (x <= x[-1]).mean(), raw=True)
F = pd.DataFrame({"A": A, "B": B, "C": Cp}).reindex(P.index)
idx = list(P.index)
def episodes(flag):
    flag = flag.fillna(False); st = flag.index[flag & ~flag.shift(1, fill_value=False)]; ep = []
    for s in st:
        if not ep or idx.index(s) - idx.index(ep[-1]) > 20: ep.append(s)
    return ep
def exit_rule(i0):
    for k in range(1, 61):
        if i0 + k >= len(idx): return np.nan, k
        if F.B.iloc[i0 + k] < 0.7: break
    return (P.c1000.iloc[i0 + k] / P.c1000.iloc[i0] - 1) * 100, k
pd.set_option("display.width", 220)
for lab, flag in (("A & B (own vol + gap)", (F.A >= 0.9) & (F.B >= 0.9)), ("A & C (own vol + option VIX)", (F.A >= 0.9) & (F.C >= 0.9)),
                  ("A alone", F.A >= 0.9), ("B alone", F.B >= 0.9)):
    rows = []
    for s in episodes(flag):
        i = idx.index(s); o = {"start": s}
        for h in (20, 60, 120): o[f"r{h}%"] = (P.c1000.iloc[i + h] / P.c1000.iloc[i] - 1) * 100 if i + h < len(P) else np.nan
        w = P.c1000.iloc[i + 1:i + 61]; o["worst60%"] = (w.min() / P.c1000.iloc[i] - 1) * 100 if len(w) else np.nan
        o["exit_rule%"], o["exit_days"] = exit_rule(i); rows.append(o)
    D = pd.DataFrame(rows)
    print(f"\n[{lab}] episodes {len(D)}"); 
    if lab.startswith("A &"): print(D.round(1).to_string(index=False))
    for col in ("r20%", "r60%", "r120%", "exit_rule%"):
        x = D[col].dropna(); print(f"  {col}: n {len(x)}, mean {x.mean():.1f}, median {x.median():.1f}, positive {int((x > 0).sum())}/{len(x)}, worst {x.min():.1f}")
print("\nnow:", F.iloc[-1].round(2).to_dict(), "on", F.index[-1])
