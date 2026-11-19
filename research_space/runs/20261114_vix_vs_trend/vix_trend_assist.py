"""Does the real A-share VIX help the trend position? (2026-11-14). User: "在A股里做择时 加入vix帮助找趋势有用吗？".

Base T0 = plan-24 position: blend of 10/21/42/252-session signals x min(1, 20% / 60-day realised vol), next day, 5 bp.
VIX variants (VIX from vix_history.csv, real_vix.py; percentile over the trailing 250 sessions):
  T1 size from implied vol: blend x min(1, 20% / VIX)
  T2 blow-off cut: halve the position when VIX pct ≥ 0.9 while blend ≥ 0.75 (fear high but trend still up)
  T3 fear-spike exit: halve the position while VIX is ≥ 20% above its 20-day mean
  T4 calm confirm: blend steps up count only when VIX ≤ its 20-day mean (else keep the previous position)
  T5 T1 + T2
Per line from the first day with a VIX percentile; Sharpe, annual return, max drawdown, average position; and the average over lines.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_vix_vs_trend"
LINES = {"OP510050.SH": ("000016.SH", "上证50"), "OP000300.SH": ("000300.SH", "沪深300(指数期权)"),
         "OP510500.SH": ("000905.SH", "中证500"), "OP000852.SH": ("000852.SH", "中证1000")}
c = duckdb.connect()
pd.set_option("display.width", 220)


def main() -> None:
    V = pd.read_csv(OUT / "vix_history.csv"); V["trade_date"] = pd.to_datetime(V.trade_date.astype(str))
    I = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
    I["trade_date"] = pd.to_datetime(I.trade_date)
    rows = []
    for code, (ix, name) in LINES.items():
        p = I[I.ts_code == ix].set_index("trade_date").close.sort_index(); r = p.pct_change()
        v = V[V.line == code].set_index("trade_date").vix.reindex(p.index).ffill(limit=5) / 100
        vp = v.rolling(250, min_periods=200).apply(lambda x: np.nan if np.isnan(x[-1]) else (x[~np.isnan(x)] <= x[-1]).mean(), raw=True)
        blend = pd.concat([(p > p.shift(n)).astype(float).where(p.shift(n).notna()) for n in (10, 21, 42, 252)], axis=1).mean(axis=1, skipna=False)
        size_rv = (0.20 / (r.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
        size_iv = (0.20 / v).clip(upper=1.0)
        hot = (vp >= 0.9) & (blend >= 0.75)
        spike = v >= 1.2 * v.rolling(20).mean()
        calm = v <= v.rolling(20).mean()
        t0 = blend * size_rv
        t4 = t0.copy()
        prev = np.nan
        for i, d in enumerate(t4.index):
            x = t0.iloc[i]
            if not np.isnan(prev) and not np.isnan(x) and x > prev and not bool(calm.iloc[i]):
                x = prev
            t4.iloc[i] = x; prev = x
        rules = {"T0 计划24": t0, "T1 用VIX定仓位": blend * size_iv, "T2 恐慌高但趋势多时减半": t0.where(~hot, t0 / 2),
                 "T3 VIX急升时减半": t0.where(~spike, t0 / 2), "T4 VIX平静才加仓": t4,
                 "T5 T1 + T2": (blend * size_iv).where(~hot, blend * size_iv / 2)}
        start = vp.first_valid_index()
        for label, w in rules.items():
            ww = w.shift(1); ret = (ww * r - 0.0005 * ww.diff().abs()).loc[start:].dropna(); cum = (1 + ret).cumprod()
            rows.append({"line": name, "start": start.date(), "rule": label, "sharpe": ret.mean() / ret.std() * 252 ** 0.5,
                         "ann": cum.iloc[-1] ** (252 / len(ret)) - 1, "max_dd": (cum / cum.cummax() - 1).min(), "avg_pos": ww.loc[start:].mean()})
    T = pd.DataFrame(rows); T.to_csv(OUT / "vix_trend_assist.csv", index=False)
    f = T.copy()
    for col in ("ann", "max_dd", "avg_pos"):
        f[col] = f[col].map(lambda x: f"{x*100:+.0f}%")
    print(f.round(2).to_string(index=False))
    print("\naverage over lines:"); print(T.groupby("rule", sort=False)[["sharpe", "max_dd", "avg_pos"]].mean().round(2).to_string())


if __name__ == "__main__":
    main()
