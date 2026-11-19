"""If holder count fell last quarter, what happens this quarter? Quarter-to-quarter transition of the holder-count change.
Change = log(n_q / n_{q-1}) from stk_holdernumber (latest announced value per end_date), minus the quarter's cross-sectional
median (market-relative). Buckets of last quarter's change (quintiles within quarter) -> this quarter's change: median,
share up, rank autocorrelation; also two quarters back, and the model's partial effect (SHAP of `prev` by its quintile)."""
import duckdb, numpy as np, pandas as pd, json, lightgbm as lgb
L = "/Volumes/Treasury/quant_cn_lake/curated"
s = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
h = duckdb.sql(f"select ts_code, end_date, arg_max(holder_num, ann_date) n from {s('events/stk_holdernumber')} where end_date >= '20190331' and right(end_date,4) in ('0331','0630','0930','1231') group by 1,2").df()
N = h.pivot(index="end_date", columns="ts_code", values="n").sort_index()
N = N[N.index.isin([f"{y}{m}" for y in range(2019, 2027) for m in ("0331", "0630", "0930", "1231")])]
D = np.log(N / N.shift(1)); D = D.where(D.abs() < 2)
R = D.sub(D.median(axis=1), axis=0)                     # market-relative
rows = []
for i in range(2, len(R)):
    q, p, p2 = R.index[i], R.iloc[i - 1], R.iloc[i - 2]
    d = pd.DataFrame({"now": R.iloc[i], "prev": p, "prev2": p2, "raw_now": D.iloc[i], "raw_prev": D.iloc[i - 1]}).dropna(subset=["now", "prev"]); d["q"] = q; rows.append(d)
E = pd.concat(rows); E = E[E.q >= "20200630"]
E["b"] = E.groupby("q").prev.transform(lambda x: pd.qcut(x.rank(method="first"), 5, labels=["1 大减", "2 减", "3 平", "4 增", "5 大增"]))
pd.set_option("display.width", 200)
print("quarters", E.q.nunique(), "rows", len(E))
print("rank autocorr (mean over quarters):", round(E.groupby("q").apply(lambda g: g.now.corr(g.prev, method="spearman"), include_groups=False).mean(), 3),
      "| lag2:", round(E.dropna(subset=["prev2"]).groupby("q").apply(lambda g: g.now.corr(g.prev2, method="spearman"), include_groups=False).mean(), 3))
t = E.groupby("b", observed=True).agg(prev_med=("raw_prev", "median"), now_med=("raw_now", "median"), now_rel_med=("now", "median"), up_share=("raw_now", lambda x: (x > 0).mean()), rel_up=("now", lambda x: (x > 0).mean()), n=("now", "size"))
print("\nall quarters"); print(t.round(3).to_string())
E["b2"] = E.groupby("q").prev2.transform(lambda x: pd.qcut(x.rank(method="first"), 5, labels=False) if x.notna().sum() > 50 else x * np.nan)
x = E[E.b.isin(["1 大减", "2 减"])].dropna(subset=["b2"])
print("\nlast quarter fell (bottom 40%), split by the quarter before (prev2 quintile 0=大减..4=大增): median now rel, share up rel")
print(x.groupby("b2").agg(now_rel_med=("now", "median"), rel_up=("now", lambda v: (v > 0).mean()), n=("now", "size")).round(3).to_string())
for lab, sel in (("2020-22", E.q < "20230101"), ("2023-26", E.q >= "20230101")):
    print(f"\n{lab}"); print(E[sel].groupby("b", observed=True).agg(now_rel_med=("now", "median"), rel_up=("now", lambda v: (v > 0).mean())).round(3).to_string())
# model partial effect of prev
IN = "/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter"; S = "/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
F = pd.read_parquet(f"{IN}/feature_rows.parquet"); FE = [c for c in F.columns if c not in ("ts_code", "q", "asof", "off", "y", "ann_y")]
TR = F[(F.off == 999) & F.y.notna() & (F.y.abs() < 2)].copy(); med = TR[FE].median(); TR[FE] = TR[FE].fillna(med)
raw_prev = TR.prev.copy()
for c in FE: TR[c] = TR.groupby("q")[c].rank(pct=True)
TR["t"] = TR.groupby("q").y.rank(pct=True)
m = lgb.LGBMRegressor(verbose=-1, random_state=0, **json.load(open(f"{S}/lgbm_best.json"))).fit(TR[FE], TR.t)
smp = TR.sample(30000, random_state=0); sh = m.predict(smp[FE], pred_contrib=True)[:, FE.index("prev")]
qq = pd.qcut(smp.prev.rank(method="first"), 5, labels=["1 大减", "2 减", "3 平", "4 增", "5 大增"])
print("\nmodel: SHAP of `prev` by its quintile (in gauge percentile points, other features held)"); print((pd.Series(sh, index=smp.index).groupby(qq, observed=True).mean() * 100).round(1).to_string())
