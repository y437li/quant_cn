"""Pilot test of minute factors on CSI 300 + CSI 500 members (membership as of each date).
Signal = 20-day mean of the daily minute feature, known at close t. Forward return enters at the
open of t+1 (no overnight leg, see overnight_split.py) and exits at the close of t+H.
Reports rank IC raw and after regressing out size + existing factors (incremental IC)."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root); RUN = LAKE / "meta/runs/research/20261113_minute_factors"
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
import sys
H, W = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (20, 20)
mf = pd.read_parquet(RUN / "minute_features.parquet")
codes = mf.ts_code.unique().tolist(); cl = ",".join(f"'{c}'" for c in codes)
con = duckdb.connect()
px = con.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c, b.circ_mv,
  d.close/d.pre_close-1 ret from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date)
  left join {r('curated/daily_basic')} b using (ts_code, trade_date)
  where d.trade_date >= '20250401' and d.ts_code in ({cl})""").df()
P = lambda v: px.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
O, C = P("o"), P("c"); idx, cols = C.index, C.columns
fwd = C.shift(-H) / O.shift(-1) - 1
size = np.log(P("circ_mv")).reindex_like(C)
ex = con.sql(f"""select trade_date, ts_code, factor, value from {r('derived/features')} where trade_date >= '20250401'
  and factor in ('reversal_1m','turnover_60d','momentum_12_1','dividend_yield','ep_ttm') and ts_code in ({cl})""").df()
EX = {f: g.pivot(index="trade_date", columns="ts_code", values="value").reindex(index=idx, columns=cols) for f, g in ex.groupby("factor")}
EX["size"] = size
mem = con.sql(f"""select trade_date, con_code ts_code from {r('curated/index_weight')}
  where index_code in ('000300.SH','000905.SH') and trade_date >= '20250301'""").df()
M = mem.assign(v=1.0).pivot_table(index="trade_date", columns="ts_code", values="v").reindex(columns=cols)
M = M.reindex(M.index.union(idx)).sort_index().ffill().reindex(idx).fillna(0).astype(bool)

def ic_series(F: pd.DataFrame, resid: bool) -> pd.Series:
    out = {}
    for d in F.index[::5]:  # every 5th day: enough, and less overlap
        y = fwd.loc[d]; x = F.loc[d]; m = M.loc[d] & y.notna() & x.notna()
        X = pd.DataFrame({k: v.loc[d] for k, v in EX.items()})
        if resid:
            m &= X.notna().all(axis=1)
        if m.sum() < 200: continue
        xs = x[m].rank()
        if resid:
            Z = X[m].rank(); Z = (Z - Z.mean()) / Z.std(); Z["c"] = 1.0
            xs = xs - Z.values @ np.linalg.lstsq(Z.values, xs.values, rcond=None)[0]
        out[d] = pd.Series(xs).corr(y[m].rank())
    return pd.Series(out)

feats = [c for c in mf.columns if c not in ("ts_code", "trade_date", "n_bars")]
rows, sig = [], {}
for f in feats:
    D = mf.pivot(index="trade_date", columns="ts_code", values=f).reindex(index=idx, columns=cols)
    F = D.rolling(W, min_periods=max(3, int(W * 0.75))).mean()
    sig[f] = F
    for resid in (False, True):
        s = ic_series(F, resid)
        n_eff = len(s) * 5 / H
        rows.append({"feature": f, "resid": resid, "n": len(s), "IC": s.mean(), "ICIR": s.mean() / s.std(),
                     "t(NW~)": s.mean() / s.std() * np.sqrt(n_eff), "hit": (np.sign(s) == np.sign(s.mean())).mean()})
res = pd.DataFrame(rows)
# correlation of each signal with existing factors (mean cross-sectional rank corr)
corr = {}
for f, F in sig.items():
    corr[f] = {k: np.nanmean([F.loc[d].corr(V.loc[d], method="spearman") for d in idx[30::20]]) for k, V in EX.items()}
corr = pd.DataFrame(corr).T
res.to_csv(RUN / f"minute_ic_H{H}_W{W}.csv", index=False); corr.to_csv(RUN / f"minute_corr_W{W}.csv")
pd.set_option("display.width", 200)
t = res.pivot(index="feature", columns="resid", values=["IC", "t(NW~)"]).round(3)
t.columns = ["IC_raw", "IC_incr", "t_raw", "t_incr"]
print(f"stocks={len(cols)} window={idx[0]}..{idx[-1]} H={H} W={W}")
print(t.sort_values("t_incr", key=abs, ascending=False).to_string())
print("\nrank corr with existing factors"); print(corr.round(2).to_string())
