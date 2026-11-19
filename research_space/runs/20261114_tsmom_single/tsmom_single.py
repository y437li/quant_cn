"""Time-series momentum asset by asset: each futures family and each A-share stock (2026-11-14).

Futures: per family, monthly position sign(past L-month return) x 40% / ex-ante vol, L = 1, 3, 12;
Sharpe and t per family; stability of the 12m per-family Sharpe between 2020-22 and 2023-26.
Stocks: month-end adjusted closes 2010-01..2026-10 (SH/SZ, months with >= 15 sessions):
  1. per stock, long-short and long-flat TSMOM on own past 12-1 and 1-month returns vs buy-and-hold;
     count of stocks with t > 1.96 / < -1.96; stability between halves;
  2. pooled each month: next-month return of stocks whose own past return is positive minus negative
     (t across months), and the same within the month (market removed);
  3. market timing: equal-weight A-share index, sign of its own past 12m / 1m.
"""
from __future__ import annotations
import contextlib, importlib.util, io, warnings
from pathlib import Path
import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_single"
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mr", HERE.parent / "20261114_mean_reversion/mean_reversion.py")
with contextlib.redirect_stdout(io.StringIO()):
    mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
sr = lambda p: p.mean() / p.std() * 12 ** 0.5
tstat = lambda p: p.mean() / p.std() * len(p) ** 0.5

# ---------------- futures, family by family
Rall = mr.d.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
M = (1 + Rall.fillna(0)).resample("ME").prod() - 1
M = M.where(Rall.resample("ME").count() > 10)
M = M[M.index < "2026-11-01"]
V = ((Rall.pow(2).ewm(com=60, min_periods=60).mean() * 252) ** 0.5).resample("ME").last().reindex(M.index)
rows = []
for L in (1, 3, 12):
    past = ((1 + M.fillna(0)).rolling(L).apply(np.prod, raw=True) - 1).where(M.notna().rolling(L).sum() == L)
    pnl = ((np.sign(past) * (0.40 / V)).clip(-3, 3).shift(1) * M)[M.index >= "2020-01-01"]
    for f in pnl.columns:
        p = pnl[f].dropna()
        if len(p) < 36:
            continue
        a, b = p[p.index < "2023-01-01"], p[p.index >= "2023-01-01"]
        rows.append({"family": f, "name": mr.fams[f]["name"], "group": mr.fams[f]["group"], "L": L,
                     "months": len(p), "sharpe": sr(p), "t": tstat(p),
                     "sharpe_2020_22": sr(a) if len(a) > 12 else np.nan,
                     "sharpe_2023_26": sr(b) if len(b) > 12 else np.nan})
F = pd.DataFrame(rows)
F.to_csv(OUT / "futures_by_family.csv", index=False)
print("FUTURES, each family on its own (2020-01..2026-10, before costs)")
for L in (1, 3, 12):
    x = F[F.L == L]
    print(f"  L={L:>2}m: {len(x)} families, median Sharpe {x.sharpe.median():+.2f}, t>1.96: {(x.t > 1.96).sum()}, "
          f"t<-1.96: {(x.t < -1.96).sum()}, rank corr 2020-22 vs 2023-26 {x.sharpe_2020_22.corr(x.sharpe_2023_26, method='spearman'):+.2f}")
x = F[F.L == 12].sort_values("t", ascending=False)
print("  12m best:", ", ".join(f"{r['name']} {r.sharpe:.2f} (t {r.t:.1f})" for _, r in x.head(6).iterrows()))
print("  12m worst:", ", ".join(f"{r['name']} {r.sharpe:.2f} (t {r.t:.1f})" for _, r in x.tail(4).iterrows()))
x1 = F[F.L == 1].sort_values("t", ascending=False)
print("  1m best:", ", ".join(f"{r['name']} {r.sharpe:.2f} (t {r.t:.1f})" for _, r in x1.head(6).iterrows()))

# ---------------- stocks
c = duckdb.connect()
m = c.execute(f"""
with p as (select d.ts_code, d.trade_date, d.close*a.adj_factor px
  from read_parquet('{LAKE}/curated/daily/year=*/*.parquet') d
  join read_parquet('{LAKE}/curated/adj_factor/year=*/*.parquet') a using (ts_code, trade_date)
  where d.trade_date >= '20090101' and d.trade_date < '20261101' and not d.ts_code like '%.BJ')
select ts_code, substr(trade_date,1,6) ym, arg_max(px, trade_date) px, count(*) n from p group by 1, 2""").df()
px = m.pivot(index="ym", columns="ts_code", values="px").sort_index()
n = m.pivot(index="ym", columns="ts_code", values="n").sort_index()
r = px.pct_change(fill_method=None).where(n >= 15).clip(-0.9, 3)
r.index = pd.to_datetime(r.index + "01") + pd.offsets.MonthEnd(0)
lg = np.log1p(r)
past12 = lg.shift(1).rolling(11, min_periods=11).sum()   # months t-12..t-2 (skip the last month)
past1 = lg
nxt = r.shift(-1)
keep = r.index >= "2010-01-01"
print("\nSTOCKS (SH/SZ, 2010-01..2026-10, monthly, before costs)")
res = {}
for name, sig in (("12-1m", past12), ("1m", past1)):
    s = np.sign(sig)[keep]; y = nxt[keep]
    ls = (s * y)                      # long-short per stock
    lf = (s.clip(lower=0) * y)        # long-flat per stock
    stats = []
    for code in y.columns:
        a = pd.concat([ls[code], lf[code], y[code]], axis=1, keys=["ls", "lf", "bh"]).dropna()
        if len(a) < 60:
            continue
        h1, h2 = a[a.index < "2018-07-01"], a[a.index >= "2018-07-01"]
        stats.append({"code": code, "months": len(a), "sr_ls": sr(a.ls), "t_ls": tstat(a.ls),
                      "sr_lf": sr(a.lf), "sr_bh": sr(a.bh),
                      "sr_ls_h1": sr(h1.ls) if len(h1) > 24 else np.nan,
                      "sr_ls_h2": sr(h2.ls) if len(h2) > 24 else np.nan})
    S = pd.DataFrame(stats); S.to_csv(OUT / f"stocks_{name}.csv", index=False)
    ok = S.dropna(subset=["sr_ls_h1", "sr_ls_h2"])
    print(f"  own {name}: {len(S)} stocks; median Sharpe long-short {S.sr_ls.median():+.2f}, long-flat {S.sr_lf.median():+.2f} vs buy-hold {S.sr_bh.median():+.2f}; "
          f"t>1.96 {(S.t_ls > 1.96).mean():.1%}, t<-1.96 {(S.t_ls < -1.96).mean():.1%} (2.5% each by chance); "
          f"halves rank corr {ok.sr_ls_h1.corr(ok.sr_ls_h2, method='spearman'):+.2f}")
    # pooled: positive minus negative own past, raw and with month mean removed
    pos = y.where(s > 0).mean(axis=1); neg = y.where(s < 0).mean(axis=1)
    spread = (pos - neg).dropna()
    frac = (s > 0).sum(axis=1) / s.notna().sum(axis=1)
    print(f"    pooled next-month: own-up minus own-down {spread.mean()*100:+.2f}%/month (t {tstat(spread):+.2f}); "
          f"since 2018-07 {spread[spread.index>='2018-07-01'].mean()*100:+.2f}% (t {tstat(spread[spread.index>='2018-07-01']):+.2f})")
    res[name] = spread
ew = r[keep].mean(axis=1)
ewl = np.log1p(ew)
for name, sig in (("12-1m", ewl.shift(1).rolling(11).sum()), ("1m", ewl)):
    p = (np.sign(sig) * ew.shift(-1)).dropna(); lf = (np.sign(sig).clip(lower=0) * ew.shift(-1)).dropna()
    print(f"  market timing, equal-weight index on own {name}: long-short Sharpe {sr(p):+.2f} (t {tstat(p):+.2f}), "
          f"long-flat {sr(lf):+.2f} vs buy-hold {sr(ew.shift(-1).dropna()):+.2f}")
