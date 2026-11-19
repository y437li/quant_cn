"""地量见地价? Does market-wide volume drying up mark a price low?
Turnover ratio = sum(amount) / sum(circ_mv) over all A-shares each day (daily_basic + daily; comparable across years as the market
grows). Signals: the 20-day mean ratio at its lowest in 250 sessions ('地量', new 1-year low) and in the bottom 10% of its trailing
3 years. Price: 沪深300 / 中证1000 closes (index cache 2015..2026-08, then 510300 / 512100 pct_chg). Episodes ≥ 40 sessions apart;
per episode: 20 / 60 / 120-day return and the drawdown still to come within 120 days. Unconditional means for comparison.
Also: where today's ratio sits, and turnover on past major lows."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
L = "/Volumes/Treasury/quant_cn_lake/curated"; r = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
t = duckdb.sql(f"""select d.trade_date, sum(d.amount)*1000 amt, sum(b.circ_mv)*10000 cmv from {r('daily')} d join {r('daily_basic')} b using (ts_code, trade_date)
  where d.trade_date >= '20120101' group by 1 order by 1""").df().set_index("trade_date")
tr = (t.amt / t.cmv * 100).rename("turn%"); tr20 = tr.rolling(20).mean()
SRC = Path("/Volumes/Treasury/chinese_market/src/regime/cache"); cl = {}
for code, f in (("c1000", "000852_SH_5min.csv"), ("c300", "000300_SH_5min.csv")):
    b = pd.read_csv(SRC / f, usecols=["trade_time", "close", "trade_date"]); cl[code] = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close
P = pd.DataFrame(cl).dropna(); P.index = P.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select ts_code, trade_date, pct_chg from {r('fund_daily')} where ts_code in ('512100.SH','510300.SH') and trade_date > '{P.index[-1]}'").df()
g = (1 + e.pivot(index="trade_date", columns="ts_code", values="pct_chg").sort_index() / 100).cumprod()
P = pd.concat([P, pd.DataFrame({"c1000": P.c1000.iloc[-1] * g["512100.SH"], "c300": P.c300.iloc[-1] * g["510300.SH"]})])
D = pd.DataFrame({"tr20": tr20}).join(P, how="inner").dropna()
D["low1y"] = D.tr20 <= D.tr20.rolling(250, min_periods=250).min()
D["p3y"] = D.tr20.rolling(750, min_periods=500).apply(lambda x: (x <= x[-1]).mean(), raw=True); D["bot10"] = D.p3y <= 0.10
idx = list(D.index); pd.set_option("display.width", 220)
def episodes(flag):
    st = flag.index[flag & ~flag.shift(1, fill_value=False)]; ep = []
    for s in st:
        if not ep or idx.index(s) - idx.index(ep[-1]) > 40: ep.append(s)
    return ep
print(f"data {D.index[0]}..{D.index[-1]}; today 20-day turnover {D.tr20.iloc[-1]:.2f}% of float cap (daily {tr.iloc[-1]:.2f}%), 3-year pct {D.p3y.iloc[-1]:.0%}, 1-year low {D.tr20.iloc[-250:].min():.2f}% on {D.tr20.iloc[-250:].idxmin()}")
for c in ("c300", "c1000"):
    print(c, "unconditional %:", {h: round((np.log(D[c].shift(-h) / D[c]).mean()) * 100, 2) for h in (20, 60, 120)})
for lab, flag in (("20-day turnover at a 1-year low (地量)", D.low1y), ("bottom 10% of 3 years", D.bot10)):
    rows = []
    for s in episodes(flag):
        i = idx.index(s); o = {"start": s, "tr20%": D.tr20.iloc[i]}
        for c, nm in (("c300", "300"), ("c1000", "1000")):
            for h in (20, 60, 120): o[f"{nm}_{h}"] = (D[c].iloc[i + h] / D[c].iloc[i] - 1) * 100 if i + h < len(D) else np.nan
            w = D[c].iloc[i + 1:i + 121]; o[f"{nm}_worst120"] = (w.min() / D[c].iloc[i] - 1) * 100 if len(w) else np.nan
        rows.append(o)
    X = pd.DataFrame(rows); print(f"\n[{lab}] episodes {len(X)}"); print(X.round(1).to_string(index=False))
    for col in ("300_20", "300_60", "300_120", "1000_20", "1000_60", "1000_120"):
        x = X[col].dropna(); print(f"  {col}: mean {x.mean():.1f}%, median {x.median():.1f}%, positive {int((x > 0).sum())}/{len(x)}")
lows = ["20160128", "20181018", "20190104", "20200323", "20220426", "20221031", "20240205", "20240913", "20250407"]
print("\nturnover on past lows (20-day mean, % of float cap):", {d: round(D.tr20.get(d, np.nan), 2) for d in lows})
