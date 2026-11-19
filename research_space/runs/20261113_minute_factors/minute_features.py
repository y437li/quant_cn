"""Daily stock features from 5-minute bars (one row per ts_code x trade_date).
Bar returns are within-day only: the first bar's return is close/open of that bar, so the
overnight gap is excluded. Output: <run>/minute_features.parquet"""
import glob, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
RUN = Path(Config.load().lake.root) / "meta/runs/research/20261113_minute_factors"
EDGE = 6  # 6 bars = 30 minutes

def smart_ratio(g: pd.DataFrame) -> float:
    """VWAP of the 'smart' bars (top |r|/sqrt(volume), up to 20% of day volume) over the day VWAP."""
    v = g.volume.to_numpy(); a = g.amount.to_numpy(); s = g.s.to_numpy()
    if v.sum() <= 0: return np.nan
    o = np.argsort(-s); cv = np.cumsum(v[o]); k = np.searchsorted(cv, 0.2 * v.sum()) + 1
    sel = o[:k]
    return (a[sel].sum() / v[sel].sum()) / (a.sum() / v.sum()) if v[sel].sum() > 0 else np.nan

def one(path: str) -> pd.DataFrame:
    b = pd.read_parquet(path)
    if b.empty: return pd.DataFrame()
    b = b[b.volume > 0].copy() if False else b.copy()
    b["trade_date"] = b.date.str.replace("-", "")
    b = b.sort_values(["trade_date", "time"])
    prev = b.groupby("trade_date").close.shift(1).fillna(b.open)
    b["r"] = np.log(b.close / prev)
    b["s"] = b.r.abs() / np.sqrt(b.volume.where(b.volume > 0))
    b["i"] = b.groupby("trade_date").cumcount()
    n = b.groupby("trade_date").time.transform("size")
    g = b.groupby("trade_date")
    r2, r3, r4 = b.r**2, b.r**3, b.r**4
    k = g.size()
    rv = r2.groupby(b.trade_date).sum()
    out = pd.DataFrame({
        "n_bars": k,
        "rvol": np.sqrt(rv),
        "rskew": np.sqrt(k) * r3.groupby(b.trade_date).sum() / rv**1.5,
        "rkurt": k * r4.groupby(b.trade_date).sum() / rv**2,
        "up_var_share": r2.where(b.r > 0, 0).groupby(b.trade_date).sum() / rv,
        "pv_corr": g.apply(lambda x: x.close.corr(x.volume), include_groups=False),
        "open30_vol_share": b.volume.where(b.i < EDGE, 0).groupby(b.trade_date).sum() / g.volume.sum(),
        "close30_vol_share": b.volume.where(b.i >= n - EDGE, 0).groupby(b.trade_date).sum() / g.volume.sum(),
        "close30_ret": b.r.where(b.i >= n - EDGE, 0).groupby(b.trade_date).sum(),
        "open30_ret": b.r.where(b.i < EDGE, 0).groupby(b.trade_date).sum(),
        "amihud_5m": (b.r.abs() / b.amount.where(b.amount > 0)).groupby(b.trade_date).mean() * 1e8,
        "smart_money": g.apply(smart_ratio, include_groups=False),
    })
    out.loc[out.n_bars < 40, out.columns.difference(["n_bars"])] = np.nan  # half days / suspensions
    out["ts_code"] = b.ts_code.iloc[0]
    return out.reset_index()

if __name__ == "__main__":
    import sys
    from multiprocessing import Pool
    files = sorted(glob.glob(str(RUN / "bars/*.parquet")))
    with Pool(8) as p:
        df = pd.concat(p.map(one, files), ignore_index=True)
    df.to_parquet(RUN / "minute_features.parquet", index=False)
    print(len(files), "stocks", df.shape); print(df.describe().T.round(4).to_string())
