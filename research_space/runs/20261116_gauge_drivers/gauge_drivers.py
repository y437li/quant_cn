"""Which features drive the RetailGauge v5 forecast of next-quarter holder change?
Fit the v5 LightGBM (lgbm_best.json, within-quarter rank features and target) on every labelled quarter-end row
(the live model for 2026Q4), then: mean |SHAP| (pred_contrib) on the live 2026-11-16 rows, grouped by feature family;
direction = rank corr of each feature with its own SHAP value; univariate rank IC of each feature with the realised change.
Rows come from research run 20261115_gauge_intraquarter (feature_rows.parquet)."""
import json, numpy as np, pandas as pd, lightgbm as lgb
S = "/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast"
IN = "/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261115_gauge_intraquarter"
OUT = "/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261116_gauge_drivers"
import os; os.makedirs(OUT, exist_ok=True)
F = pd.read_parquet(f"{IN}/feature_rows.parquet")
FE = [c for c in F.columns if c not in ("ts_code", "q", "asof", "off", "y", "ann_y")]
TR = F[(F.off == 999) & F.y.notna() & (F.y.abs() < 2)].copy()
TE = F[(F.off == 0) & (F["asof"] == F.loc[F.off == 0, "asof"].max())].copy()
med = TR[FE].median(); TR[FE] = TR[FE].fillna(med); TE[FE] = TE[FE].fillna(med)
for c in FE: TR[c] = TR.groupby("q")[c].rank(pct=True); TE[c] = TE[c].rank(pct=True)
TR["t"] = TR.groupby("q").y.rank(pct=True)
m = lgb.LGBMRegressor(verbose=-1, random_state=0, **json.load(open(f"{S}/lgbm_best.json"))).fit(TR[FE], TR.t)
sh = pd.DataFrame(m.predict(TE[FE], pred_contrib=True)[:, :-1], columns=FE, index=TE.index)
imp = sh.abs().mean().rename("mean_abs_shap")
dirn = pd.Series({c: TE[c].corr(sh[c], method="spearman") for c in FE}, name="dir")
ic = pd.Series({c: TR.groupby("q").apply(lambda g: g[c].corr(g.t), include_groups=False).mean() for c in FE}, name="uni_ic")
R = pd.concat([imp, dirn, ic], axis=1).sort_values("mean_abs_shap", ascending=False)
R["share"] = R.mean_abs_shap / R.mean_abs_shap.sum(); R.to_csv(f"{OUT}/gauge_drivers.csv")
def fam(c):
    if c in ("prev", "prev2") or c.endswith("_lag1") or c == "dtov_prev": return "上季及更早的户数/状态 (lags)"
    if c.startswith("tov") or c in ("dtov",): return "换手率 turnover"
    if c.startswith(("lg", "big", "elg", "sm", "out_")): return "资金流 order flow"
    if c.startswith(("rz", "m_", "mchg")): return "融资 margin"
    if c in ("win_b", "conc_b", "pc50_b", "dwin", "dconc", "dpc50", "wavg_gap"): return "筹码 chips"
    if c.startswith("vol") or c in ("n_bigup", "n_bigdn", "limitups", "reversals"): return "波动/大涨大跌 volatility"
    if c == "lmv": return "市值 size"
    if c == "qtr": return "季度 season"
    return "价格路径 price path"
R["family"] = [fam(c) for c in R.index]
pd.set_option("display.width", 200)
print("train rows", len(TR), "quarters", TR.q.nunique(), "| live rows", len(TE), TE["asof"].iloc[0])
print(R.groupby("family").share.sum().sort_values(ascending=False).round(3).to_string())
print(R.head(20).round(3).to_string())
