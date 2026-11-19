"""RetailGauge v5 walk-forward predictions for every quarter 2022Q1..2026Q3 (+ the 2026-11-12 nowcast), saved
for return tests. Panel assembly is copied from research_space/prototypes/holder_nowcast/holders_v5_compare.py
(same features, PIT labels and lags, lgbm_best.json); only the loop that stores predictions is new.
Run: uv run --all-extras --with lightgbm --with scikit-learn python <this file>"""
import duckdb, json, numpy as np, pandas as pd, lightgbm as lgb
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root); S = LAKE / "meta/runs/holder_nowcast"; L = LAKE / "curated"
OUT = LAKE / "meta/runs/research/20261113_retail_gauge_returns"; OUT.mkdir(parents=True, exist_ok=True)
s = lambda t: f"read_parquet('{L}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
F = (pd.read_parquet(S / "holders_v3_feats.parquet")
     .merge(pd.read_parquet(S / "holders_v4_flow.parquet"), on=["ts_code", "q"], how="left")
     .merge(pd.read_parquet(S / "holders_v5_feats.parquet"), on=["ts_code", "q"], how="left"))
cyq = pd.read_parquet(S / "cyq_qe.parquet"); cyq["conc"] = (cyq.cost_85pct - cyq.cost_15pct) / cyq.cost_50pct
cd = sorted(cyq.trade_date.unique()); Q = sorted(F.q.unique())
snap = lambda q: max(d for d in cd if d <= q)
px = duckdb.sql(f"select ts_code, trade_date, close from {s('daily')} where trade_date in {tuple(cd)}").df()
chip = []
for i, q in enumerate(Q):
    a = Q[i - 1] if i > 0 else None
    cb = cyq[cyq.trade_date == snap(q)].set_index("ts_code"); pb = px[px.trade_date == snap(q)].set_index("ts_code").close
    c = pd.DataFrame({"win_b": cb.winner_rate, "conc_b": cb.conc, "pc50_b": np.log(pb / cb.cost_50pct)})
    if a is not None:
        ca = cyq[cyq.trade_date == snap(a)].set_index("ts_code"); pa = px[px.trade_date == snap(a)].set_index("ts_code").close
        c["dwin"] = cb.winner_rate - ca.winner_rate; c["dconc"] = cb.conc - ca.conc
        c["dpc50"] = c.pc50_b - np.log(pa / ca.cost_50pct); c["wavg_gap"] = np.log(cb.weight_avg / ca.weight_avg)
    c["q"] = q; chip.append(c.reset_index())
F = F.merge(pd.concat(chip), on=["ts_code", "q"], how="left")
h = duckdb.sql(f"""select ts_code, end_date, arg_max(holder_num, ann_date) n, min(ann_date) ann
  from {s('events/stk_holdernumber')} where end_date >= '20200630' group by 1, 2""").df()
N = h.pivot(index="ts_code", columns="end_date", values="n"); A = h.set_index(["ts_code", "end_date"]).ann
allq = sorted(N.columns); pq = lambda q, k: allq[allq.index(q) - k] if q in allq and allq.index(q) - k >= 0 else None
def lab(c, q):
    p = pq(q, 1)
    return np.log(N.at[c, q] / N.at[c, p]) if (q in N.columns and p and c in N.index) else np.nan
F["y"] = [lab(c, q) if q != "20261112" else np.nan for c, q in zip(F.ts_code, F.q)]
F["ann_y"] = [A.get((c, q)) for c, q in zip(F.ts_code, F.q)]
def lagchg(c, q, k):
    qq = pq(q if q in allq else "20260930", k - 1 if q not in allq else k)
    if qq is None or c not in N.index: return np.nan
    p = pq(qq, 1); a = A.get((c, qq))
    if p is None or a is None or a > q: return np.nan
    return np.log(N.at[c, qq] / N.at[c, p])
F["prev"] = [lagchg(c, q, 1) for c, q in zip(F.ts_code, F.q)]; F["prev2"] = [lagchg(c, q, 2) for c, q in zip(F.ts_code, F.q)]
F["qtr"] = F.q.str[4:6].map({"03": 1, "06": 2, "09": 3, "12": 4, "11": 4}).astype(float)
F = F.sort_values(["ts_code", "q"])
for c in ["dtov", "tov_acc", "mchg", "ret_q", "big_cum", "dd_qhigh", "lg_cum", "tov_rel_60", "lg_60"]:
    F[c + "_lag1"] = F.groupby("ts_code")[c].shift(1)
F["dtov_prev"] = F["dtov_lag1"]
FEATS = [c for c in F.columns if c not in ("ts_code", "q", "y", "ann_y")]
best = json.load(open(S / "lgbm_best.json")); train_q = [q for q in Q if q != "20261112"]

def fit_predict(tr: pd.DataFrame, te: pd.DataFrame) -> np.ndarray:
    med = tr[FEATS].median(); tr = tr.copy(); te = te.copy(); tr[FEATS] = tr[FEATS].fillna(med); te[FEATS] = te[FEATS].fillna(med)
    for c in FEATS: tr[c] = tr.groupby("q")[c].rank(pct=True); te[c] = te[c].rank(pct=True)
    tr["t"] = tr.groupby("q").y.rank(pct=True)
    return lgb.LGBMRegressor(verbose=-1, random_state=0, **best).fit(tr[FEATS], tr.t).predict(te[FEATS])

out = []
for q in train_q[4:] + ["20261112"]:
    k = train_q.index(q) if q in train_q else len(train_q)
    tr = F[F.q.isin(train_q[:k]) & (F.ann_y <= q) & F.y.notna() & (F.y.abs() < 2)]
    te = F[F.q == q]   # every stock, labelled or not: at the prediction date nobody knows the label
    p = pd.Series(fit_predict(tr, te), index=te.index).rank(pct=True)
    out.append(pd.DataFrame({"ts_code": te.ts_code, "q": q, "gauge": p, "y": te.y, "prev": te.prev, "ann_y": te.ann_y}))
    print(q, len(te), "IC vs realised", round(p.corr(te.y.rank(pct=True), method="spearman"), 3), flush=True)
pd.concat(out).to_parquet(OUT / "gauge_walkforward.parquet", index=False)
