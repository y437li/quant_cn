"""ETF CTA book from 2014 on backfilled ETF history (D-159) — plan 27 phase 1 (2026-11-14).
User: "数据补齐后跑2013年以来的回测".

Same rules as full_scheme.py (risk budget 1:1:1:1 on 股票 / 债券 / 黄金 / 商品, monthly; weekly A股 plan-24 position; optional bond
switch, no 30-year, bond cap 65%; long only; 15 bp; cash 511880). ETFs join their group when listed.
Before the commodity ETFs list (159980 2019-12, 159981 2020-01) their returns are proxied by equal-weight main-contract futures
returns (close / pre_close of the mapped contract): 有色 = CU AL ZN PB NI SN (SHF), 能化 = TA MA FG SA (ZCE).
The 原油 LOF joins in 2017-02. Start 2014-01-02 (60-day vols and 252-session signals need 2013 history).
Reports variants ①..⑤ over the full period, sub-periods and episodes (2015 crash, 2016-17 bond bear, 2018, 2020-26),
by year, and the proxy check (proxy vs ETF correlation after listing).
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import duckdb, numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
spec = importlib.util.spec_from_file_location("fs", HERE / "full_scheme.py")
fs = importlib.util.module_from_spec(spec); spec.loader.exec_module(fs)
om, sy = fs.om, fs.sy
pd.set_option("display.width", 260)
START = "2014-01-01"
PROXY = {"159980.SZ": ["CU.SHF", "AL.SHF", "ZN.SHF", "PB.SHF", "NI.SHF", "SN.SHF"],
         "159981.SZ": ["TA.ZCE", "MA.ZCE", "FG.ZCE", "SA.ZCE"]}
PERIODS = {"2014-16": ("2014", "2016"), "2017-19": ("2017", "2019"), "2020-22": ("2020", "2022"), "2023-26": ("2023", "2026"),
           "股灾 2015-06..2016-02": ("2015-06", "2016-02"), "债熊 2016-10..2017-12": ("2016-10", "2017-12"),
           "2018": ("2018", "2018"), "2020-02..2026-11": ("2020-02", "2026")}


def futures_proxy(index: pd.DatetimeIndex) -> pd.DataFrame:
    c = duckdb.connect(); fams = sorted({f for v in PROXY.values() for f in v})
    F = c.execute(f"""select m.ts_code fam, m.trade_date, d.close/d.pre_close-1 ret
      from read_parquet('{LAKE}/curated/fut_mapping/**/*.parquet') m
      join read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') d on d.ts_code=m.mapping_ts_code and d.trade_date=m.trade_date
      where m.ts_code in ({','.join(repr(f) for f in fams)}) and d.pre_close>0 and d.close>0""").df()
    F["trade_date"] = pd.to_datetime(F.trade_date)
    X = F.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
    return pd.DataFrame({etf: X[[f for f in fams_ if f in X]].mean(axis=1) for etf, fams_ in PROXY.items()}).reindex(index)


def main() -> None:
    base = sy.GROUPS
    sy.GROUPS = {**base, "原油": {om.OIL: 1}}; R, cash = sy.load()
    R = R.loc["2012-01-01":]; cash = cash.reindex(R.index).fillna(0)
    px = futures_proxy(R.index)
    for etf in PROXY:
        live = R[etf].notna().cumsum() > 0
        j = pd.concat([R[etf], px[etf]], axis=1).dropna()
        print(f"proxy check {etf}: corr {j.iloc[:, 0].corr(j.iloc[:, 1]):.2f} over {len(j)} days after listing")
        R[etf] = R[etf].where(live, px[etf])
    sy.START = START
    cov = {c_: R[c_].first_valid_index() for c_ in R.columns}
    print("first day per ETF:", {k: (v.date() if v is not None else None) for k, v in sorted(cov.items(), key=lambda kv: str(kv[1]))})
    sy.load = lambda: (R, cash)                     # full_scheme.main calls sy.load()
    fs.main.__globals__["sy"] = sy
    idx = R.index
    # run full_scheme's variants by reusing its build logic through main() would print 2020 stats; rebuild here instead
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0); A = fs.A
    blend = sum((P[A] > P[A].shift(n)).astype(float).where(P[A].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    a_pos = (blend * (0.20 / (R[A].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).where(fri).ffill()

    def build(bonds: dict, a24: bool, switch: bool, cap: bool) -> pd.Series:
        G = fs.layout(bonds); sy.GROUPS = G
        gr = pd.DataFrame({g: (sy.group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in G}, index=idx)) * R.fillna(0)).sum(axis=1) for g in G})
        gr = gr.where(pd.DataFrame({g: R[list(G[g])].notna().any(axis=1) for g in G}))
        iv = 1 / (gr.rolling(60, min_periods=40).std() * 252 ** 0.5); m = iv.div(iv.sum(axis=1), axis=0).where(month).ffill()
        if cap:
            over = (m["债券"] - fs.CAP).clip(lower=0); rest = m.drop(columns="债券")
            m["债券"] = m["债券"] - over
            m[rest.columns] = rest.add(rest.div(rest.sum(axis=1), axis=0).mul(over, axis=0))
        if switch:
            nav = (1 + gr["债券"].fillna(0)).cumprod()
            s = (sum((nav > nav.shift(n)).astype(float).where(nav.shift(n).notna()) for n in (21, 63, 252)) / 3).where(fri).ffill()
            m["债券"] = m["债券"] * s.fillna(1.0)
        w = sy.group_weights(R, m.fillna(0))
        if a24:
            w[A] = w[A] * a_pos.fillna(0)
        return sy.run(R, cash, w, fri if (a24 or switch) else month)

    steps = [("① 风险预算", fs.BOND_ALL, False, False, False), ("② + A股择时", fs.BOND_ALL, True, False, False),
             ("③ + 债券开关", fs.BOND_ALL, True, True, False), ("④ + 去30年", fs.BOND_NO30, True, True, False),
             ("⑤ 完整方案(+债券≤65%)", fs.BOND_NO30, True, True, True)]
    books = {n: build(b, a, s, cp) for n, b, a, s, cp in steps}
    books["参考 股40/债60"] = None
    sy.GROUPS = fs.layout(fs.BOND_ALL)
    books["参考 股40/债60"] = sy.run(R, cash, sy.group_weights(R, pd.DataFrame({"股票": 0.4, "债券": 0.6}, index=idx).reindex(columns=list(sy.GROUPS)).fillna(0)), month)
    books["参考 持有510300"] = R["510300.SH"].fillna(0).loc[START:]
    sy.GROUPS = base
    rows = {}
    for k, x in books.items():
        ex = x - cash.loc[x.index]; cum = (1 + x).cumprod()
        r = {"ann": cum.iloc[-1] ** (252 / len(x)) - 1, "vol": x.std() * 252 ** 0.5, "sharpe": ex.mean() / ex.std() * 252 ** 0.5,
             "max_dd": (cum / cum.cummax() - 1).min(), "worst_12m": ((1 + x).rolling(252).apply(np.prod, raw=True) - 1).min()}
        for p, (a, b) in PERIODS.items():
            z = x.loc[a:b]; zc = (1 + z).cumprod(); ze = z - cash.loc[z.index]
            if z.empty:
                continue
            r[f"{p} 收益"] = zc.iloc[-1] - 1
            if len(z) > 120 and not p.startswith(("股灾", "债熊", "2018")):
                r[f"{p} 夏普"] = ze.mean() / ze.std() * 252 ** 0.5
            else:
                r[f"{p} 回撤"] = (zc / zc.cummax() - 1).min()
        rows[k] = r
    T = pd.DataFrame(rows).T
    T.to_csv(sy.OUT / "full_scheme_long.csv"); pd.DataFrame(books).to_csv(sy.OUT / "full_scheme_long_daily.csv")
    main_cols = ["ann", "vol", "sharpe", "max_dd", "worst_12m"]
    f = T[main_cols].copy()
    for col in ("ann", "vol", "max_dd", "worst_12m"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print(f"\n{START}..{idx[-1].date()}, 15 bp:"); print(f.round(2).to_string())
    g = T.drop(columns=main_cols).copy()
    for col in g:
        g[col] = g[col].map(lambda v: "" if pd.isna(v) else (f"{v:.2f}" if "夏普" in col else f"{v*100:+.1f}%"))
    print("\nsub-periods and episodes:"); print(g.T.to_string())
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g_: (1 + g_).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).T.to_string())


if __name__ == "__main__":
    main()
