"""Stock TSMOM decomposed into market timing and cross-sectional parts, vs classic XSMOM (2026-11-14).

Per month t, stocks i with signal s_i = sign(own past return), r_m = equal-weight mean of next-month returns:
  TS book  = mean_i(s_i r_i) = n_t r_m + mean_i(s_i (r_i - r_m)),  n_t = mean_i(s_i) (net long share)
  timing   = n_t r_m           (how much of the market the TS book holds)
  relative = mean_i(s_i (r_i - r_m))   (cross-sectional part)
Classic XSMOM: top decile minus bottom decile by the past-return rank; and rank weights.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_single"
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
sigs = {"12-1m": lg.shift(1).rolling(11, min_periods=11).sum(), "1m": lg}
nxt = r.shift(-1)
keep = (r.index >= "2010-01-01") & (r.index < "2026-10-01")
sr = lambda p: p.mean() / p.std() * 12 ** 0.5
tst = lambda p: p.mean() / p.std() * len(p) ** 0.5
rows = []
for name, past in sigs.items():
    P, Y = past[keep], nxt[keep]
    ok = P.notna() & Y.notna()
    P, Y = P.where(ok), Y.where(ok)
    s = np.sign(P)
    rm = Y.mean(axis=1)
    ts = (s * Y).mean(axis=1)
    net = s.mean(axis=1)
    timing = net * rm
    rel = (s * Y.sub(rm, axis=0)).mean(axis=1)
    rk = P.rank(axis=1, pct=True)
    xs_dec = Y.where(rk > 0.9).mean(axis=1) - Y.where(rk <= 0.1).mean(axis=1)
    w = rk.sub(rk.mean(axis=1), axis=0)
    xs_rank = (w * Y).sum(axis=1) / w.abs().sum(axis=1) * 2
    for lab, p in (("TS book (own sign, each stock)", ts), ("  = timing part n_t × r_m", timing),
                   ("  + cross-sectional part", rel), ("classic XS: top − bottom decile", xs_dec),
                   ("classic XS: rank-weighted", xs_rank)):
        p = p.dropna(); late = p[p.index >= "2018-07-01"]
        rows.append({"signal": name, "book": lab, "ret_pm_%": p.mean() * 100, "sharpe": sr(p), "t": tst(p),
                     "sharpe_2018h2+": sr(late), "t_2018h2+": tst(late)})
    print(f"{name}: average net long share n_t {net.mean():+.2f} (range {net.min():+.2f}..{net.max():+.2f}); "
          f"corr(timing, rel) {timing.corr(rel):+.2f}; corr(XS rank, rel) {xs_rank.corr(rel):+.2f}")
T = pd.DataFrame(rows); T.to_csv(OUT / "decompose.csv", index=False)
print(T.round(2).to_string(index=False))
