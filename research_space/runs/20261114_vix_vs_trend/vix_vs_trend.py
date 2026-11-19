"""Do "buy when A-share VIX is high" and the short-trend blend overlap or conflict? (2026-11-14)

A-share VIX history in the lake starts 2025-11 (volatility_monitor.json, ~1 year), so 2011-2026 uses
20-day realised volatility as the fear proxy; the 2025-26 overlap checks how well it tracks the VIX.
Indices: 沪深300 (VIX: 300ETF), 中证500 (500ETF), 中证1000 (中证1000 options), 创业板指 (no options).
Fear high: proxy at or above its trailing-250-session 90th percentile (the monitor's alert_pct 0.9).
Trend blend: share of {10, 21, 42, 252}-session signals that are up (0, .25, .5, .75, 1).
Outputs: overlap counts; next 20 / 60-session index return by fear state × trend bucket (2011-2026);
backtests 2011-2026 of blend + vol sizing, fear-buy alone (hold 60 sessions after a fear-high day)
and the two combined (position = max of the two).
"""
from __future__ import annotations
import json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
REPO = Path(__file__).resolve().parents[3]
OUT = LAKE / "meta/runs/research/20261114_vix_vs_trend"
D = duckdb.connect().execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
D["trade_date"] = pd.to_datetime(D.trade_date)
names = {"000300.SH": ("沪深300", "cn_300"), "000905.SH": ("中证500", "cn_500"), "000852.SH": ("中证1000", "cn_1000"), "399006.SZ": ("创业板指", None)}
vm = {x["key"]: pd.Series({pd.Timestamp(h["date"]): h["value"] for h in x["history"]})
      for x in json.load(open(REPO / "research_space/prototypes/chain_view/volatility_monitor.json"))["lines"]}
pct = lambda s: s.rolling(250, min_periods=120).apply(lambda x: (x <= x[-1]).mean(), raw=True)
rows, bt, chk = [], [], []
for code, (nm, vkey) in names.items():
    p = D[D.ts_code == code].set_index("trade_date").close.sort_index(); r = p.pct_change()
    rv = r.rolling(20).std() * 252 ** 0.5
    fear = pct(rv) >= 0.9
    blend = pd.concat([(p > p.shift(n)).astype(float).where(p.shift(n).notna()) for n in (10, 21, 42, 252)], axis=1).mean(axis=1, skipna=False)
    f20, f60 = p.shift(-20) / p - 1, p.shift(-60) / p - 1
    dd1y = p / p.rolling(250).max() - 1
    df = pd.DataFrame({"fear": fear, "blend": blend, "f20": f20, "f60": f60, "dd1y": dd1y}).loc["2011-06-01":].dropna(subset=["blend"])
    df["index"] = nm; rows.append(df)
    if vkey and vkey in vm:
        v = vm[vkey]; j = pd.concat([v, rv.reindex(v.index), pct(rv).reindex(v.index), blend.reindex(v.index)], axis=1, keys=["vix", "rv", "rv_pct", "blend"]).dropna()
        vp = j.vix.rank(pct=True)
        chk.append({"index": nm, "days": len(j), "corr_vix_rv": j.vix.corr(j.rv),
                    "vix_top10_days": int((vp >= 0.9).sum()), "of_which_rv_pct>=0.9": int(((vp >= 0.9) & (j.rv_pct >= 0.9)).sum()),
                    "blend_on_vix_top10": j.blend[vp >= 0.9].mean()})
    # backtests
    size = (0.20 / rv.shift(0)).clip(upper=1.0)
    hold60 = fear.astype(float).rolling(60, min_periods=1).max()       # in for 60 sessions after a fear-high day
    hold60_dd = (fear & (dd1y <= -0.15)).astype(float).rolling(60, min_periods=1).max()
    for label, w in {"一直持有": pd.Series(1.0, index=p.index), "趋势混合 + vol": blend * size,
                     "恐慌高就买(持有60天)": hold60, "恐慌高且已跌15%才买(持有60天)": hold60_dd,
                     "趋势混合 + vol, 再加恐慌买入(取大)": np.maximum(blend * size, hold60_dd)}.items():
        ww = w.shift(1); ret = (ww * r - 0.0005 * ww.diff().abs()).loc["2011-06-01":].dropna(); cum = (1 + ret).cumprod()
        bt.append({"index": nm, "rule": label, "sharpe": ret.mean() / ret.std() * 252 ** 0.5,
                   "ann": cum.iloc[-1] ** (252 / len(ret)) - 1, "max_dd": (cum / cum.cummax() - 1).min(), "in": ww.loc["2011-06-01":].mean()})
A = pd.concat(rows); A.to_csv(OUT / "panel.csv")
pd.set_option("display.width", 220)
print("1) Proxy vs real VIX (2025-11..2026-11):"); print(pd.DataFrame(chk).round(2).to_string(index=False))
print(f"\n2) Overlap 2011-2026, 4 indices: fear-high days {int(A.fear.sum())} of {len(A)} ({A.fear.mean():.0%});")
print("   trend blend on fear-high days:", A[A.fear].blend.value_counts(normalize=True).sort_index().map(lambda x: f"{x:.0%}").to_dict())
print("   trend blend on other days:   ", A[~A.fear].blend.value_counts(normalize=True).sort_index().map(lambda x: f"{x:.0%}").to_dict())
A["trend"] = pd.cut(A.blend, [-0.01, 0.25, 0.5, 1.0], labels=["空(0-25%)", "中(50%)", "多(75-100%)"])
g = A.groupby(["fear", "trend"], observed=True).agg(days=("f20", "size"), next20=("f20", "mean"), next60=("f60", "mean"), up60=("f60", lambda x: (x > 0).mean()))
g["next20"] = g.next20.map(lambda x: f"{x*100:+.1f}%"); g["next60"] = g.next60.map(lambda x: f"{x*100:+.1f}%"); g["up60"] = g.up60.map(lambda x: f"{x:.0%}")
print("\n3) Next-period index return by fear state × trend (all days 2011-2026, overlapping, 4 indices):"); print(g.to_string())
uc = A.f60.mean(); print(f"   unconditional next60 {uc*100:+.1f}%, up {(A.f60 > 0).mean():.0%}")
B = pd.DataFrame(bt); B.to_csv(OUT / "backtest.csv", index=False)
b = B.groupby("rule", sort=False)[["sharpe", "ann", "max_dd", "in"]].mean()
print("\n4) Backtests 2011-06..2026-11 (average of 4 indices, 5 bp):")
print(b.assign(ann=b.ann.map(lambda x: f"{x*100:.0f}%"), max_dd=b.max_dd.map(lambda x: f"{x*100:.0f}%"), **{"in": b["in"].map(lambda x: f"{x*100:.0f}%")}).round(2).to_string())
