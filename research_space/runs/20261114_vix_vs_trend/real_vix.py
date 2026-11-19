"""Real A-share VIX history from the backfilled options and the "buy when VIX is high" test (2026-11-14).

VIX: the volatility monitor's own building blocks (VixCalculator, trading clock D-052, TermSelector 7 days,
price_or_volume strip, dividend-adjusted contracts excluded as in the monitor) over the full option
history, read straight from the lake parquet files (no catalog write).
Lines -> index (curated reference/index_daily):
  OP510050.SH 50ETF (2015-02) -> 上证50; OP000300.SH 沪深300 index options (2019-12) -> 沪深300;
  OP510300.SH 300ETF (2019-12) -> 沪深300; OP510500.SH 500ETF (2022-09) -> 中证500;
  OP000852.SH 中证1000 index options (2022-07) -> 中证1000.
Tests (per line, after 250 sessions of VIX history):
  1. VIX vs 20-day realised vol (correlation, top-decile overlap);
  2. next 20 / 60-session index return by VIX state (pct of trailing 250 ≥ 0.9, ≥ 0.8, normal) × trend blend;
  3. rules: buy on VIX high (hold 60), buy when VIX high and already off its 5-day peak by 10% (fear
     receding), trend blend + vol, and trend blend + vol with the receding-fear buy (max), 5 bp.
Writes vix_history.csv and real_vix_results.csv.
"""
from __future__ import annotations
import os
from pathlib import Path
import duckdb, numpy as np, pandas as pd

from quant_cn.calculation.expiry_clock import ExpiryClock
from quant_cn.calculation.forward_price_estimator import ForwardPriceEstimator
from quant_cn.calculation.option_chain_builder import OptionChainBuilder
from quant_cn.calculation.risk_free_curve import RiskFreeCurve
from quant_cn.calculation.term_interpolator import TermInterpolator
from quant_cn.calculation.term_selector import TermSelector
from quant_cn.calculation.variance_strip_calculator import VarianceStripCalculator
from quant_cn.calculation.vix_calculator import VixCalculator

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_vix_vs_trend"
LINES = {"OP510050.SH": ("50ETF", "000016.SH", "上证50"), "OP000300.SH": ("沪深300指数期权", "000300.SH", "沪深300"),
         "OP510300.SH": ("300ETF", "000300.SH", "沪深300"), "OP510500.SH": ("500ETF", "000905.SH", "中证500"),
         "OP000852.SH": ("中证1000指数期权", "000852.SH", "中证1000")}
c = duckdb.connect()
# REAL_VIX_SRC=raw reads raw/opt_daily (before compaction); REAL_VIX_TAG suffixes the output files
SRC = (f"{LAKE}/raw/opt_daily/*.parquet" if os.environ.get("REAL_VIX_SRC") == "raw"
       else f"{LAKE}/curated/opt_daily/**/*.parquet")
TAG = os.environ.get("REAL_VIX_TAG", "")


def compute_vix() -> pd.DataFrame:
    basic = c.execute(f"select * from read_parquet('{LAKE}/curated/reference/opt_basic.parquet') "
                      f"where opt_code in ({','.join(repr(k) for k in LINES)})").df()
    sessions = c.execute(f"select cal_date from read_parquet('{LAKE}/curated/reference/trade_cal.parquet') "
                         "where is_open = 1 order by cal_date").df().cal_date.astype(str).tolist()
    shibor = c.execute(f"select * from read_parquet('{LAKE}/curated/reference/shibor.parquet') order by date").df()
    out = []
    for code in LINES:
        ids = basic[basic.opt_code == code].ts_code.astype(str).tolist()
        daily = c.execute(f"select * from read_parquet('{SRC}', union_by_name=true) "
                          "where list_contains(?, ts_code)", [ids]).df()
        chains = OptionChainBuilder(exclude_adjusted=True)
        chain = chains.build_chain(basic, daily, code)
        start = str(chain.trade_date.min())
        calc = VixCalculator(RiskFreeCurve(shibor), chains, TermSelector(7), ForwardPriceEstimator(),
                             VarianceStripCalculator("price_or_volume"), TermInterpolator(),
                             ExpiryClock("trading", [d for d in sessions if d > start]))
        panel = calc.compute(chain, code)
        out.append(panel[["trade_date", "vix", "quality_flag"]].assign(line=code))
        print(f"{code}: {panel.vix.notna().sum()} VIX days {panel.trade_date.min()}..{panel.trade_date.max()}", flush=True)
    V = pd.concat(out)
    V.to_csv(OUT / f"vix_history{TAG}.csv", index=False)
    return V


def main() -> None:
    V = compute_vix()
    V["trade_date"] = pd.to_datetime(V.trade_date.astype(str))
    I = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
    I["trade_date"] = pd.to_datetime(I.trade_date)
    pctf = lambda s: s.rolling(250, min_periods=200).apply(
        lambda x: np.nan if np.isnan(x[-1]) else (x[~np.isnan(x)] <= x[-1]).mean(), raw=True)  # NaN-free rank
    res, panels = [], []
    for code, (vname, ix, iname) in LINES.items():
        p = I[I.ts_code == ix].set_index("trade_date").close.sort_index(); r = p.pct_change()
        v = V[V.line == code].set_index("trade_date").vix.reindex(p.index).ffill(limit=5)
        vp = pctf(v)
        rv = r.rolling(20).std() * 252 ** 0.5
        blend = pd.concat([(p > p.shift(n)).astype(float).where(p.shift(n).notna()) for n in (10, 21, 42, 252)], axis=1).mean(axis=1, skipna=False)
        size = (0.20 / (r.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
        hi = vp >= 0.9
        receding = hi.rolling(10, min_periods=1).max().astype(bool) & (v <= v.rolling(5).max() * 0.9)
        df = pd.DataFrame({"vix": v, "vix_pct": vp, "rv": rv, "blend": blend, "f20": p.shift(-20) / p - 1,
                           "f60": p.shift(-60) / p - 1}).dropna(subset=["vix_pct", "blend"])
        df["line"] = vname; panels.append(df)
        start = df.index[0]
        rules = {"一直持有": pd.Series(1.0, index=p.index), "VIX高就买(持有60天)": hi.astype(float).rolling(60, min_periods=1).max(),
                 "VIX高后回落10%才买(持有60天)": receding.astype(float).rolling(60, min_periods=1).max(),
                 "趋势混合 + vol": blend * size,
                 "趋势混合 + vol + VIX回落买入(取大)": np.maximum(blend * size, receding.astype(float).rolling(60, min_periods=1).max())}
        for label, w in rules.items():
            ww = w.shift(1); ret = (ww * r - 0.0005 * ww.diff().abs()).loc[start:].dropna(); cum = (1 + ret).cumprod()
            res.append({"line": vname, "index": iname, "start": start.date(), "rule": label,
                        "sharpe": ret.mean() / ret.std() * 252 ** 0.5, "ann": cum.iloc[-1] ** (252 / len(ret)) - 1,
                        "max_dd": (cum / cum.cummax() - 1).min(), "in": ww.loc[start:].mean(),
                        "signals": int((sig.loc[start:].astype(float).diff() > 0).sum()) if (sig := {"VIX高就买(持有60天)": hi, "VIX高后回落10%才买(持有60天)": receding}.get(label, receding if "VIX" in label else None)) is not None else None})
    A = pd.concat(panels); R = pd.DataFrame(res)
    A.to_csv(OUT / f"real_vix_panel{TAG}.csv"); R.to_csv(OUT / f"real_vix_results{TAG}.csv", index=False)
    pd.set_option("display.width", 240)
    print("\n1) VIX vs 20-day realised vol:")
    for ln, g in A.groupby("line", sort=False):
        top = g.vix_pct >= 0.9
        print(f"  {ln}: {len(g)} days from {g.index[0].date()}, corr {g.vix.corr(g.rv):.2f}, VIX-high days {int(top.sum())}, "
              f"trend blend ≤ 25% on {((g.blend <= 0.25) & top).sum() / max(top.sum(), 1):.0%} of them")
    A["vix_state"] = pd.cut(A.vix_pct, [-0.01, 0.8, 0.9, 1.0], labels=["正常", "偏高(80-90%)", "很高(≥90%)"])
    A["trend"] = pd.cut(A.blend, [-0.01, 0.25, 0.5, 1.0], labels=["空", "中", "多"])
    g = A.groupby(["vix_state", "trend"], observed=True).agg(days=("f20", "size"), next20=("f20", "mean"), next60=("f60", "mean"),
                                                             up60=("f60", lambda x: (x > 0).mean()))
    for col in ("next20", "next60"):
        g[col] = g[col].map(lambda x: f"{x*100:+.1f}%")
    g["up60"] = g.up60.map(lambda x: f"{x:.0%}")
    print("\n2) Next-period index return by VIX state × trend (all lines pooled, overlapping days):"); print(g.to_string())
    print(f"   all days: next60 {A.f60.mean()*100:+.1f}%, up {(A.f60 > 0).mean():.0%}")
    print("\n3) Rules (5 bp, from each line's first VIX-percentile day):")
    t = R.copy()
    for col in ("ann", "max_dd", "in"):
        t[col] = t[col].map(lambda x: f"{x*100:.0f}%")
    print(t.round(2).to_string(index=False))
    m = R.groupby("rule", sort=False)[["sharpe", "max_dd"]].mean()
    print("\n   average over lines:"); print(m.round(2).to_string())


if __name__ == "__main__":
    main()
