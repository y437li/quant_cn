"""Drawdowns of buyable ETF books (2026-11-14): user cannot trade futures.

Books 2020-02..2026-11, 15 bp per unit traded (a conservative ETF cost), cash in 511880:
  trend 21/63/252 weekly (25% capital per group, long-flat), trend 10/21/42/252 weekly,
  static 25/25/25/25 rebalanced monthly, static 股25 / 债35 / 商品20 / 海外20 rebalanced monthly, hold 510300.
Per book: annual return, max drawdown, peak / trough dates, longest time under water, worst 1 / 3 / 12 months,
yearly returns, and a 21-day block bootstrap (2000 paths) of the max drawdown.
Stress outside the ETF history: the A股 quarter alone (four indices, same rules, 2011-2019 incl. 2015 / 2018),
as drawdown of a 25% slice.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_cta_horizon_etf"
c = duckdb.connect()
pd.set_option("display.width", 240)
GROUPS = {"A股": ["510300.SH", "510500.SH", "512100.SH", "159915.SZ"],
          "债券": ["511010.SH", "511260.SH", "511020.SH", "511090.SH"],
          "商品": ["518880.SH", "161226.SZ", "159985.SZ", "159980.SZ", "159981.SZ"],
          "海外": ["513100.SH", "513500.SH", "513520.SH", "513030.SH", "159920.SZ", "513050.SH"]}
CASH, COST, START = "511880.SH", 0.0015, "2020-02-01"


def signal(P: pd.DataFrame, ns: tuple[int, ...]) -> pd.DataFrame:
    s = sum((P > P.shift(n)).astype(float).where(P.shift(n).notna()) for n in ns) / len(ns)
    return s.loc[s.index.dayofweek == 4].reindex(s.index, method="ffill")


def book(R: pd.DataFrame, w: pd.DataFrame, cash: pd.Series) -> pd.Series:
    ww = w.shift(1).fillna(0); used = ww.sum(axis=1)
    return ((ww * R[w.columns]).sum(axis=1) + (1 - used) * cash - COST * ww.diff().abs().sum(axis=1)).loc[START:]


def static(R: pd.DataFrame, mix: dict[str, float]) -> pd.Series:
    """Monthly rebalanced fixed mix; weights drift inside the month."""
    cols = [x for g in GROUPS.values() for x in g]
    target = pd.DataFrame(0.0, index=R.index, columns=cols)
    for g, v in GROUPS.items():
        live = R[v].notna()
        target[v] = live.div(live.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * mix[g]
    month = R.index.to_series().dt.to_period("M")
    reb = (month != month.shift(1)).to_numpy()
    w = target.iloc[0].copy(); out, prev = [], w.copy()
    for i, d in enumerate(R.index):
        if reb[i]:
            w = target.loc[d].copy()
        r = R.loc[d, cols].fillna(0)
        trade = (w - prev).abs().sum() if reb[i] else 0.0
        out.append((w * r).sum() + (1 - w.sum()) * 0 - COST * trade)
        prev = w * (1 + r); prev = prev / max(1e-12, (1 + (w * r).sum())); w = prev.copy()
    return pd.Series(out, index=R.index).loc[START:]


def describe(x: pd.Series) -> dict:
    cum = (1 + x).cumprod(); dd = cum / cum.cummax() - 1
    trough = dd.idxmin(); peak = cum.loc[:trough].idxmax()
    under = (dd < 0).astype(int); longest = under.groupby((under == 0).cumsum()).sum().max()
    roll = lambda n: ((1 + x).rolling(n).apply(np.prod, raw=True) - 1).min()
    rng = np.random.default_rng(0); a = x.to_numpy(); L = len(a); boot = []
    for _ in range(2000):
        idx = np.concatenate([np.arange(s, s + 21) % L for s in rng.integers(0, L, L // 21 + 1)])[:L]
        cc = np.cumprod(1 + a[idx]); boot.append((cc / np.maximum.accumulate(cc) - 1).min())
    return {"ann": cum.iloc[-1] ** (252 / len(x)) - 1, "vol": x.std() * 252 ** 0.5, "max_dd": dd.min(),
            "peak": peak.date(), "trough": trough.date(), "longest_under_days": int(longest),
            "worst_1m": roll(21), "worst_3m": roll(63), "worst_12m": roll(252),
            "boot_dd_median": np.median(boot), "boot_dd_5pct": np.quantile(boot, 0.05)}


def main() -> None:
    codes = [x for g in GROUPS.values() for x in g] + [CASH]
    E = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
                      where ts_code in ({','.join(repr(x) for x in codes)}) and pre_close > 0""").df()
    E["trade_date"] = pd.to_datetime(E.trade_date)
    R = E.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    cash = R[CASH].fillna(0)
    books = {}
    for k, ns in {"趋势 21/63/252 周调": (21, 63, 252), "趋势 10/21/42/252 周调": (10, 21, 42, 252)}.items():
        sig = signal(P, ns); w = pd.DataFrame(0.0, index=R.index, columns=[x for g in GROUPS.values() for x in g])
        for g in GROUPS.values():
            w[g] = sig[g].div(sig[g].notna().sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 0.25
        books[k] = book(R, w, cash)
    books["固定 25/25/25/25 月调"] = static(R, {"A股": 0.25, "债券": 0.25, "商品": 0.25, "海外": 0.25})
    books["固定 股25/债35/商品20/海外20 月调"] = static(R, {"A股": 0.25, "债券": 0.35, "商品": 0.20, "海外": 0.20})
    books["只持有 510300"] = R["510300.SH"].fillna(0).loc[START:]
    T = pd.DataFrame({k: describe(v) for k, v in books.items()}).T
    T.to_csv(OUT / "dd_check.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_1m", "worst_3m", "worst_12m", "boot_dd_median", "boot_dd_5pct"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print(f"ETF books {START}..{R.index[-1].date()}, {COST*1e4:.0f} bp per unit traded:"); print(f.to_string())
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).to_string())

    # stress: A股 quarter on index history
    I = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
    I["trade_date"] = pd.to_datetime(I.trade_date)
    PI = I.pivot(index="trade_date", columns="ts_code", values="close").sort_index()[["000300.SH", "000905.SH", "000852.SH", "399006.SZ"]]
    RI = PI.pct_change()
    print("\nStress, A股 quarter only (25% of capital, rest cash at 0), on index history:")
    for k, ns in {"趋势 21/63/252 周调": (21, 63, 252), "趋势 10/21/42/252 周调": (10, 21, 42, 252), "一直持有": ()}.items():
        sig = signal(PI, ns) if ns else PI.notna().astype(float)
        w = sig.div(sig.notna().sum(axis=1), axis=0) * 0.25
        x = ((w.shift(1) * RI).sum(axis=1) - COST * w.shift(1).diff().abs().sum(axis=1)).loc["2011-01-04":]
        for a, b in (("2015-06-01", "2016-02-29"), ("2018-01-01", "2018-12-31"), ("2011-01-04", "2026-11-13")):
            cum = (1 + x.loc[a:b]).cumprod()
            print(f"  {k:22s} {a[:7]}..{b[:7]}: max dd {(cum / cum.cummax() - 1).min()*100:+.1f}% of total capital")


if __name__ == "__main__":
    main()
