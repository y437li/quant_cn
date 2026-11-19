"""Trend or mean reversion in China commodity futures (ad hoc, 2026-11-14).

1. Variance ratios VR(k) = Var(k-day return) / (k Var(1-day)) for k = 5, 21, 63, 126, 252 on main-contract
   roll-free daily returns, 2020-01 onward, with the Lo-MacKinlay heteroskedasticity-robust z.
2. Spread half-lives: futures_monitor.yaml spreads plus PP − 3×MA (MTO), legs on the mapped (main)
   contract settle; AR(1) on daily levels (log for ratios) -> half-life = -ln2 / ln(1+b); ADF p-value;
   current z vs the full sample and vs one year.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd, yaml
from statsmodels.tsa.stattools import adfuller

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_mean_reversion"
REPO = Path(__file__).resolve().parents[3]
cfg = yaml.safe_load(open(REPO / "config/futures_monitor.yaml"))
fams = {f["family"]: f for f in cfg["families"]}
spreads = cfg["spreads"] + [{"key": "mto", "name": "PP − 3×甲醇（MTO）", "legs": [
    {"family": "PP.DCE", "coef": 1.0}, {"family": "MA.ZCE", "coef": -3.0}]}]
c = duckdb.connect()
inl = ",".join(f"'{f}'" for f in fams)
d = c.execute(f"""
select m.ts_code fam, m.trade_date, d.close/d.pre_close-1 ret, d.settle
from read_parquet('{LAKE}/curated/fut_mapping/**/*.parquet') m
join read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') d on d.ts_code=m.mapping_ts_code and d.trade_date=m.trade_date
where m.ts_code in ({inl}) and d.pre_close>0 and d.close>0""").df()
d["trade_date"] = pd.to_datetime(d["trade_date"])
R = d.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
S = d.pivot_table(index="trade_date", columns="fam", values="settle").sort_index()
R = R[R.index >= "2020-01-01"]


def variance_ratio(x: np.ndarray, k: int) -> tuple[float, float]:
    """Lo-MacKinlay VR(k) on overlapping k-sums and the heteroskedasticity-robust z."""
    x = x[~np.isnan(x)]; n = len(x)
    mu = x.mean(); e = x - mu
    s1 = (e ** 2).sum() / (n - 1)
    sk = pd.Series(x).rolling(k).sum().dropna().to_numpy() - k * mu
    m = k * (n - k + 1) * (1 - k / n)
    vr = (sk ** 2).sum() / m / s1
    e2 = e ** 2; den = e2.sum() ** 2
    theta = sum((2 * (k - j) / k) ** 2 * (e2[j:] * e2[:-j]).sum() / den for j in range(1, k))
    return vr, (vr - 1) / np.sqrt(theta)


rows = []
for f in R.columns:
    x = R[f].to_numpy()
    if np.isfinite(x).sum() < 500:  # >= 2 years
        continue
    row = {"family": f, "name": fams[f]["name"], "group": fams[f]["group"], "n": int(np.isfinite(x).sum())}
    for k in (5, 21, 63, 126, 252):
        vr, z = variance_ratio(x, k); row[f"vr{k}"] = vr; row[f"z{k}"] = z
    rows.append(row)
V = pd.DataFrame(rows).set_index("family")
V.to_csv(OUT / "variance_ratios.csv")
ks = (5, 21, 63, 126, 252)
print(f"families: {len(V)}; median VR by group (k = 1w, 1m, 3m, 6m, 12m)")
gm = V.groupby("group")[[f"vr{k}" for k in ks]].median().round(2)
gm["n"] = V.groupby("group").size()
print(gm.to_string())
print("\nall:", V[[f"vr{k}" for k in ks]].median().round(2).to_dict())
for k in ks:
    print(f"k={k:>3}: VR>1 sig (z>1.96) {int((V[f'z{k}'] > 1.96).sum())}, VR<1 sig {int((V[f'z{k}'] < -1.96).sum())} of {len(V)}")
print("\nstrongest trend at 3m:", ", ".join(f"{r['name']} {r.vr63:.2f}" for _, r in V.nlargest(6, "vr63").iterrows()))
print("strongest reversion at 3m:", ", ".join(f"{r['name']} {r.vr63:.2f}" for _, r in V.nsmallest(6, "vr63").iterrows()))

out = []
for sp in spreads:
    legs = sp["legs"]; cols = [l["family"] for l in legs]
    if any(cn not in S.columns for cn in cols):
        continue
    L = S[cols].dropna()
    if sp.get("kind") == "ratio":
        s = np.log(legs[0]["coef"] * L[cols[0]] / (legs[1]["coef"] * L[cols[1]])); unit = "log"
    else:
        s = sum(l["coef"] * L[l["family"]] for l in legs); unit = "元"
    s = s[s.index >= "2019-01-01"]
    if len(s) < 250:
        continue
    y = s.diff().dropna(); xlag = s.shift(1).loc[y.index]
    b = np.polyfit(xlag, y, 1)[0]
    hl = -np.log(2) / np.log(1 + b) if b < 0 else np.inf
    p = adfuller(s, maxlag=10, autolag="AIC")[1]
    last = s.iloc[-1]; s1 = s[s.index >= s.index[-1] - pd.Timedelta(days=365)]
    cur = (np.exp(last) if unit == "log" else last)
    out.append({"key": sp["key"], "name": sp["name"], "start": s.index[0].date(), "n": len(s),
                "half_life_days": hl, "adf_p": p, "current": cur,
                "z_all": (last - s.mean()) / s.std(), "z_1y": (last - s1.mean()) / s1.std()})
H = pd.DataFrame(out).sort_values("half_life_days")
H.to_csv(OUT / "spread_half_life.csv", index=False)
print(f"\nspreads (as of {S.index[-1].date()}):")
for _, h in H.iterrows():
    print(f"{h['name']:18s} from {h.start} half-life {h.half_life_days:6.0f} d  ADF p {h.adf_p:.2f}  now {h.current:,.1f}  z(all) {h.z_all:+.1f}  z(1y) {h.z_1y:+.1f}")
