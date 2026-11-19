"""Out-of-sample check of "classify first, then choose trend or reversion" (2026-11-14).

A. Families: variance ratio VR(k) on 2020-01..2022-12 (formation) vs 2023-01..2026-10 (test):
   rank correlation across families (is the trait stable?), and monthly 12m TSMOM in the test period
   split by the formation class; a regime-aware book (trend class follows, reversion class fades).
B. Spreads: rolling one-year z-score, position = -clip(z, -2, 2) held next day; daily P&L scaled
   by the rolling std of spread changes; Sharpe per spread, before costs.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mr", HERE / "mean_reversion.py")
import contextlib, io, warnings
warnings.filterwarnings("ignore")
with contextlib.redirect_stdout(io.StringIO()):
    mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
R, S, fams, spreads, OUT = mr.R, mr.S, mr.fams, mr.spreads, mr.OUT
form, test = R[R.index < "2023-01-01"], R[R.index >= "2023-01-01"]

print("A. Is the trend / reversion trait stable?")
for k in (21, 63, 126):
    rows = []
    for f in R.columns:
        a, b = form[f].dropna().to_numpy(), test[f].dropna().to_numpy()
        if len(a) >= 500 and len(b) >= 500:
            rows.append((f, mr.variance_ratio(a, k)[0], mr.variance_ratio(b, k)[0]))
    T = pd.DataFrame(rows, columns=["f", "vr_form", "vr_test"]).set_index("f")
    same = ((T.vr_form > 1) == (T.vr_test > 1)).mean()
    print(f"  k={k:>3}: {len(T)} families, rank corr {T.vr_form.corr(T.vr_test, method='spearman'):+.2f}, "
          f"same side of 1: {same:.0%}")
    if k == 126:
        cls = np.sign(T.vr_form - 1)

vol = (R.pow(2).ewm(com=60, min_periods=60).mean() * 252) ** 0.5
Rall = mr.d.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
M = (1 + Rall.fillna(0)).resample("ME").prod() - 1
M = M.where(Rall.resample("ME").count() > 10)
V = ((Rall.pow(2).ewm(com=60, min_periods=60).mean() * 252) ** 0.5).resample("ME").last()
past = ((1 + M.fillna(0)).rolling(12).apply(np.prod, raw=True) - 1).where(M.notna().rolling(12).sum() == 12)
pos = (np.sign(past) * (0.40 / V)).clip(-3, 3).shift(1)
pnl = (pos * M)[(M.index >= "2023-01-01") & (M.index < "2026-11-01")]
sr = lambda p: p.mean() / p.std() * 12 ** 0.5
tr, rv = cls[cls > 0].index, cls[cls < 0].index
book = {"TSMOM, all families": pnl[cls.index].mean(axis=1),
        f"TSMOM, trend class ({len(tr)})": pnl[tr].mean(axis=1),
        f"TSMOM, reversion class ({len(rv)})": pnl[rv].mean(axis=1),
        "regime-aware (follow trend, fade reversion)": pd.concat([pnl[tr], -pnl[rv]], axis=1).mean(axis=1)}
print("\n  test 2023-01..2026-10, monthly 12m signal, before costs:")
for k, p in book.items():
    p = p.dropna(); print(f"    {k:45s} ann {p.mean()*12:+.1%}  Sharpe {sr(p):+.2f}  t {p.mean()/p.std()*len(p)**.5:+.2f}  ({len(p)} m)")

print("\nB. Spread mean reversion, rolling 1-year z, before costs:")
rows = []
for sp in spreads:
    cols = [l["family"] for l in sp["legs"]]
    if any(c not in S.columns for c in cols):
        continue
    L = S[cols].dropna()
    s = (np.log(sp["legs"][0]["coef"] * L[cols[0]] / (sp["legs"][1]["coef"] * L[cols[1]]))
         if sp.get("kind") == "ratio" else sum(l["coef"] * L[l["family"]] for l in sp["legs"]))
    z = (s - s.rolling(250).mean()) / s.rolling(250).std()
    ds = s.diff(); scale = ds.rolling(250).std()
    p = (-z.clip(-2, 2).shift(1) * ds / scale.shift(1)).dropna()
    for name, part in (("all", p), ("2023+", p[p.index >= "2023-01-01"])):
        if len(part) > 250:
            rows.append({"spread": sp["name"], "period": name, "start": part.index[0].date(), "days": len(part),
                         "sharpe": part.mean() / part.std() * 252 ** 0.5,
                         "t": part.mean() / part.std() * len(part) ** 0.5})
B = pd.DataFrame(rows)
B.to_csv(OUT / "spread_zscore_backtest.csv", index=False)
print(B.pivot_table(index="spread", columns="period", values=["sharpe", "t"]).round(2).sort_values(("sharpe", "all"), ascending=False).to_string())
