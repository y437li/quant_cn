"""Horizon choice per sleeve / per product, and an ETF-only version of the CTA book (2026-11-14).

A. Horizons on the futures sleeves (commodity 73 families, bond T/TF/TS/TL; monthly MOP sizing 40%/vol,
   cap 3, costs as in cta_portfolio.py): lookback 1 / 3 / 6 / 12 months and the blend mean(sign 1, 3, 12),
   Sharpe 2020-22 and 2023-26. Walk-forward: each product picks its best lookback on 2020-22 (own Sharpe),
   used unchanged in 2023-26, against the fixed 12 m and the blend.
   Index sleeve (daily, long-flat, x min(1, 20%/60d vol)): windows 10 / 21 / 42 / 63 / 126 / 252 sessions
   alone and blends, 2011-18 / 2019-26.
B. ETF-only book (long-flat, no shorting, no futures): groups A股 / 债券 / 商品 / 海外.
   Per ETF: signal = share of windows up (sets below), unit-risk weight signal x 10% / 60-day vol, equal
   within group, equal across groups; gross capped at 100% (no leverage) or 200% (hypothetical margin),
   rest in the money-market ETF 511880; daily, 5 bp on turnover. Benchmarks: equal-weight hold of the
   same ETFs; hold 510300.
Writes horizon_*.csv and etf_*.csv to the lake research folder.
"""
from __future__ import annotations
import contextlib, importlib.util, io, warnings
from pathlib import Path
import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_cta_horizon_etf"
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cp", HERE.parent / "20261114_cta_portfolio/cta_portfolio.py")
with contextlib.redirect_stdout(io.StringIO()):
    cp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp)
mr, c = cp.mr, duckdb.connect()
pd.set_option("display.width", 240)
SPLIT = "2023-01-01"
GROUPS = {"A股": ["510300.SH", "510500.SH", "512100.SH", "159915.SZ"],
          "债券": ["511010.SH", "511260.SH", "511020.SH", "511090.SH"],
          "商品": ["518880.SH", "161226.SZ", "159985.SZ", "159980.SZ", "159981.SZ"],
          "海外": ["513100.SH", "513500.SH", "513520.SH", "513030.SH", "159920.SZ", "513050.SH"]}
CASH = "511880.SH"
sr = lambda x: x.mean() / x.std() * 252 ** 0.5 if len(x) > 60 and x.std() > 0 else np.nan


def monthly_parts(R: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    M = (1 + R.fillna(0)).resample("ME").prod() - 1
    M = M.where(R.resample("ME").count() > 10)
    V = ((R.pow(2).ewm(com=60, min_periods=60).mean() * 252) ** 0.5).resample("ME").last()
    return M, V


def past(M: pd.DataFrame, L: int) -> pd.DataFrame:
    return ((1 + M.fillna(0)).rolling(L).apply(np.prod, raw=True) - 1).where(M.notna().rolling(L).sum() == L)


def product_pnl(R: pd.DataFrame, sig: pd.DataFrame, cost: float, roll_month: float) -> pd.DataFrame:
    """Daily net P&L per product from month-end signals (sizing 40%/vol, cap 3)."""
    _, V = monthly_parts(R)
    W = (sig * (0.40 / V)).clip(-3, 3).shift(1, freq="D").reindex(R.index, method="ffill")
    first = W.index.to_series().dt.to_period("M") != W.index.to_series().shift(1).dt.to_period("M")
    turn = W.fillna(0).diff().abs().mul(first, axis=0)
    return (W * R - cost * turn - roll_month / 21 * W.abs()).where(W.notna() & R.notna())


def signals(R: pd.DataFrame) -> dict[str, pd.DataFrame]:
    M, _ = monthly_parts(R)
    out = {f"{L}m": np.sign(past(M, L)) for L in (1, 3, 6, 12)}
    out["混合1/3/12m"] = pd.concat([out["1m"], out["3m"], out["12m"]]).groupby(level=0).mean().where(out["12m"].notna())
    return out


def part_a() -> None:
    commod = mr.d.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
    F = c.execute(f"""select m.ts_code fam, m.trade_date, d.close/d.pre_close-1 ret
     from read_parquet('{LAKE}/curated/fut_mapping/**/*.parquet') m
     join read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') d on d.ts_code=m.mapping_ts_code and d.trade_date=m.trade_date
     where m.ts_code in ('T.CFX','TF.CFX','TS.CFX','TL.CFX') and d.pre_close>0""").df()
    F["trade_date"] = pd.to_datetime(F.trade_date)
    bonds = F.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
    rows, wf = [], []
    for sleeve, R, cost, roll in (("商品趋势", commod, 0.0005, 0.0010), ("国债趋势", bonds, 0.0001, 0.0002 / 3)):
        sig = signals(R)
        P = {k: product_pnl(R, s, cost, roll).loc["2020-04-17":] for k, s in sig.items()}
        for k, p in P.items():
            book = p.mean(axis=1).dropna()
            rows.append({"sleeve": sleeve, "horizon": k, "sharpe": sr(book), "sharpe_2020_22": sr(book[:SPLIT]),
                         "sharpe_2023_26": sr(book[SPLIT:])})
        # walk-forward: each product's best lookback on 2020-22
        horizons = ["1m", "3m", "6m", "12m"]
        IS = pd.DataFrame({k: P[k][:SPLIT].apply(sr) for k in horizons}).dropna(how="all")
        best = IS.idxmax(axis=1)
        picked = pd.concat([P[best[f]][f][SPLIT:] for f in best.index], axis=1).mean(axis=1).dropna()
        same = pd.DataFrame({k: P[k][best.index][SPLIT:].mean(axis=1) for k in ("12m", "混合1/3/12m")}).dropna()
        # did the in-sample best stay best? rank of the picked horizon in 2023-26 per product
        late = pd.DataFrame({k: P[k][best.index][SPLIT:].apply(sr) for k in horizons}).dropna(how="all")
        stay = (late.idxmax(axis=1) == best.reindex(late.index)).mean()
        wf.append({"sleeve": sleeve, "products": len(best), "picked_mix": best.value_counts().to_dict(),
                   "sharpe_2023_26_picked": sr(picked), "sharpe_2023_26_12m": sr(same["12m"]),
                   "sharpe_2023_26_blend": sr(same["混合1/3/12m"]), "best_stays_best": stay})
    # index sleeve, daily windows
    I = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
    I["trade_date"] = pd.to_datetime(I.trade_date)
    P = I.pivot(index="trade_date", columns="ts_code", values="close").sort_index()[
        ["000300.SH", "000905.SH", "000852.SH", "399006.SZ"]]
    sets = {f"{n}天": (n,) for n in (10, 21, 42, 63, 126, 252)}
    sets |= {"混合10/21/42/252(计划24)": (10, 21, 42, 252), "混合21/63/252": (21, 63, 252), "混合10/21/42": (10, 21, 42)}
    for k, ns in sets.items():
        book = []
        for code in P:
            p = P[code].dropna(); r = p.pct_change()
            b = pd.concat([(p > p.shift(n)).astype(float).where(p.shift(n).notna()) for n in ns], axis=1).mean(axis=1, skipna=False)
            w = (b * (0.20 / (r.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).shift(1)
            book.append(w * r - 0.0005 * w.diff().abs())
        x = pd.concat(book, axis=1).mean(axis=1).loc["2011-01-04":].dropna()
        rows.append({"sleeve": "股指趋势", "horizon": k, "sharpe": sr(x), "sharpe_2020_22": sr(x["2011":"2018"]),
                     "sharpe_2023_26": sr(x["2019":])})
    H = pd.DataFrame(rows); H.to_csv(OUT / "horizon_sleeves.csv", index=False)
    W = pd.DataFrame(wf); W.to_csv(OUT / "horizon_walkforward.csv", index=False)
    print("A1. Sharpe by horizon (net; 股指趋势 columns are 2011-18 / 2019-26 instead of 2020-22 / 2023-26):")
    print(H.round(2).to_string(index=False))
    print("\nA2. Walk-forward: each product's best lookback on 2020-22, used in 2023-26:")
    print(W.round(2).to_string(index=False))


def part_b() -> None:
    codes = [x for g in GROUPS.values() for x in g] + [CASH]
    E = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
                      where ts_code in ({','.join(repr(x) for x in codes)}) and pre_close > 0""").df()
    E["trade_date"] = pd.to_datetime(E.trade_date)
    R = E.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    cash = R[CASH].fillna(0)
    vol = R.rolling(60, min_periods=40).std() * 252 ** 0.5
    sets = {"10/21/42/252天(计划24)": (10, 21, 42, 252), "21/63/252天": (21, 63, 252), "252天(12个月)": (252,),
            "21天": (21,), "一直持有(按风险)": ()}
    res, curves = [], {}
    for k, ns in sets.items():
        if ns:
            sig = sum((P > P.shift(n)).astype(float).where(P.shift(n).notna()) for n in ns) / len(ns)
        else:
            sig = P.notna().astype(float).where(P.shift(252).notna())
        unit = sig * (0.10 / vol)
        w = pd.DataFrame(0.0, index=R.index, columns=R.columns)
        live_groups = pd.concat([unit[g].notna().any(axis=1) for g in GROUPS.values()], axis=1).sum(axis=1).replace(0, np.nan)
        for g in GROUPS.values():
            n = unit[g].notna().sum(axis=1).replace(0, np.nan)
            w[g] = unit[g].div(n, axis=0).div(live_groups, axis=0).fillna(0)
        for cap in (1.0, 2.0):
            gross = w.drop(columns=CASH).sum(axis=1)
            ww = w.drop(columns=CASH).mul((cap / gross).clip(upper=1.0).fillna(0), axis=0).shift(1)
            g_used = ww.sum(axis=1)
            ret = (ww * R.drop(columns=CASH)).sum(axis=1) + (1 - g_used).clip(lower=0) * cash \
                - (g_used - 1).clip(lower=0) * cash * 1.5 - 0.0005 * ww.diff().abs().sum(axis=1)
            ret = ret.loc["2020-02-01":].dropna()
            cum = (1 + ret).cumprod()
            exp = ww.loc["2020-02-01":]
            res.append({"signal": k, "gross_cap": f"{cap:.0%}", "ann": cum.iloc[-1] ** (252 / len(ret)) - 1,
                        "vol": ret.std() * 252 ** 0.5, "sharpe": sr(ret - cash.loc[ret.index]),
                        "max_dd": (cum / cum.cummax() - 1).min(), "sharpe_2023+": sr((ret - cash)[SPLIT:].dropna()),
                        "avg_gross": g_used.loc["2020-02-01":].mean(),
                        **{f"w_{gname}": exp[gl].sum(axis=1).mean() for gname, gl in GROUPS.items()},
                        "turnover_y": ww.diff().abs().sum(axis=1).loc["2020-02-01":].mean() * 252})
            curves[f"{k} | {cap:.0%}"] = ret
    hold_all = R.drop(columns=CASH)[[x for g in GROUPS.values() for x in g]].mean(axis=1).loc["2020-02-01":]
    for name, x in (("等权持有全部ETF", hold_all), ("持有510300", R["510300.SH"].loc["2020-02-01":].fillna(0))):
        cum = (1 + x).cumprod()
        res.append({"signal": name, "gross_cap": "100%", "ann": cum.iloc[-1] ** (252 / len(x)) - 1, "vol": x.std() * 252 ** 0.5,
                    "sharpe": sr(x - cash.loc[x.index]), "max_dd": (cum / cum.cummax() - 1).min(),
                    "sharpe_2023+": sr((x - cash)[SPLIT:].dropna()), "avg_gross": 1.0})
        curves[name] = x
    T = pd.DataFrame(res); T.to_csv(OUT / "etf_books.csv", index=False)
    pd.DataFrame(curves).to_csv(OUT / "etf_daily.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "avg_gross", "w_A股", "w_债券", "w_商品", "w_海外"):
        f[col] = f[col].map(lambda v: "" if pd.isna(v) else f"{v*100:.0f}%")
    print("\nB. ETF-only book 2020-02..2026-11 (net 5 bp; Sharpe over the money-market ETF; cash in 511880; "
          "200% = hypothetical margin at 1.5x the cash yield):")
    print(f.round(2).to_string(index=False))
    print("\n   ETFs used:", {g: [x for x in l if x in R.columns] for g, l in GROUPS.items()})



def part_c(cost: float = 0.0005) -> pd.DataFrame:
    """ETF book with equal capital (not risk) per group: 25% each, equal capital inside, on/off by signal."""
    codes = [x for g in GROUPS.values() for x in g] + [CASH]
    E = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
                      where ts_code in ({','.join(repr(x) for x in codes)}) and pre_close > 0""").df()
    E["trade_date"] = pd.to_datetime(E.trade_date)
    R = E.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    cash = R[CASH].fillna(0)
    rows, curves = [], {}
    for k, ns in {"10/21/42/252天": (10, 21, 42, 252), "21/63/252天": (21, 63, 252), "252天": (252,), "一直持有": ()}.items():
        for weekly in (False, True):
            if ns:
                sig = sum((P > P.shift(n)).astype(float).where(P.shift(n).notna()) for n in ns) / len(ns)
            else:
                sig = P.notna().astype(float).where(P.shift(252).notna())
            if weekly:
                sig = sig.loc[sig.index.dayofweek == 4].reindex(sig.index, method="ffill")
            w = pd.DataFrame(0.0, index=R.index, columns=R.columns)
            for g in GROUPS.values():
                n = sig[g].notna().sum(axis=1).replace(0, np.nan)
                w[g] = sig[g].div(n, axis=0).fillna(0) * 0.25
            ww = w.drop(columns=CASH).shift(1); used = ww.sum(axis=1)
            ret = ((ww * R.drop(columns=CASH)).sum(axis=1) + (1 - used) * cash - cost * ww.diff().abs().sum(axis=1)).loc["2020-02-01":]
            cum = (1 + ret).cumprod(); ex = (ret - cash.loc[ret.index])
            label = f"{k}{' 周调' if weekly else ' 日调'}"
            rows.append({"signal": label, "ann": cum.iloc[-1] ** (252 / len(ret)) - 1, "vol": ret.std() * 252 ** 0.5,
                         "sharpe": sr(ex), "max_dd": (cum / cum.cummax() - 1).min(), "sharpe_2023+": sr(ex[SPLIT:]),
                         "avg_invested": used.loc["2020-02-01":].mean(),
                         **{f"{gn}": (ww[gl].sum(axis=1) * 0 + (R[gl].loc[ret.index].mul(ww[gl].loc[ret.index]).sum(axis=1))).sum() for gn, gl in GROUPS.items()},
                         "turnover_y": ww.diff().abs().sum(axis=1).loc["2020-02-01":].mean() * 252})
            curves[label] = ret
    T = pd.DataFrame(rows); T.to_csv(OUT / "etf_equal_capital.csv", index=False)
    pd.DataFrame(curves).to_csv(OUT / "etf_equal_capital_daily.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "avg_invested", "A股", "债券", "商品", "海外"):
        f[col] = f[col].map(lambda v: f"{v*100:+.0f}%" if col in GROUPS else f"{v*100:.0f}%")
    print("\nC. ETF book, 25% capital per group (A股 / 债券 / 商品 / 海外), long-flat, cash 511880, 5 bp; group columns = summed P&L contribution:")
    print(f.round(2).to_string(index=False))
    return T


if __name__ == "__main__":
    import sys
    if "c" in sys.argv[1:]:
        part_c()
    else:
        part_a(); part_b(); part_c()
