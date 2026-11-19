"""Systematic ways to set exposure on a liquid ETF book (2026-11-14). User: 我们看有没有系统性的; ETFs only, liquid, low premium.

Groups (equal weight inside, ETFs join when listed): A股 510300 510500 512100 159915; 债券 511010 511260 511020 511090;
黄金商品 518880 (half) + 159980 159981 (quarter each); 港股 159920 513050 513130. Cash 511880.
Base mix 股25 / 债35 / 黄金商品20 / 港股20. Decisions weekly (Friday close, trade next session) unless noted;
weights held constant between decisions (daily rebalanced to target, an approximation); 15 bp per unit traded.
Rules (parameters fixed in advance from earlier research, none fitted here):
  M1 fixed 25×4 monthly; M2 fixed base mix monthly; M3 risk parity across groups (1 / 60-day vol, monthly);
  M4 M2 x min(1, 8% / 60-day vol of the M2 book) (portfolio vol target); M5 M2 with each ETF on/off by trend 21/63/252;
  M6 M2 with the A股 quarter x plan-24 position (blend 10/21/42/252 x min(1, 20% / 60-day vol)); M7 M2 with stock-bond
  tilt ±10 pt by the equity risk premium z (market earnings yield − 10-year yield, z over 3 years);
  M8 M6 + M4; M9 M6 + M7 + M4.
Freed capital goes to cash. Reports 2020-02..2026-11 and the halves 2020-22 / 2023-26.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_etf_universe"
c = duckdb.connect()
pd.set_option("display.width", 240)
GROUPS = {"A股": {"510300.SH": 1, "510500.SH": 1, "512100.SH": 1, "159915.SZ": 1},
          "债券": {"511010.SH": 1, "511260.SH": 1, "511020.SH": 1, "511090.SH": 1},
          "黄金商品": {"518880.SH": 2, "159980.SZ": 1, "159981.SZ": 1},
          "港股": {"159920.SZ": 1, "513050.SH": 1, "513130.SH": 1}}
BASE = {"A股": 0.25, "债券": 0.35, "黄金商品": 0.20, "港股": 0.20}
CASH, COST, START = "511880.SH", 0.0015, "2020-02-01"


def load() -> tuple[pd.DataFrame, pd.Series]:
    codes = [x for g in GROUPS.values() for x in g] + [CASH]
    D = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
                      where ts_code in ({','.join(repr(x) for x in codes)}) and pre_close > 0""").df()
    D["trade_date"] = pd.to_datetime(D.trade_date)
    R = D.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
    return R.drop(columns=CASH), R[CASH].fillna(0)


def erp_z(index: pd.DatetimeIndex) -> pd.Series:
    E = c.execute(f"""select trade_date, sum(total_mv) / sum(total_mv / pe_ttm) pe from read_parquet('{LAKE}/curated/daily_basic/**/*.parquet', union_by_name=true)
                      where pe_ttm > 0 and dayofweek(strptime(trade_date, '%Y%m%d')) = 5 group by 1""").df()
    Y = c.execute(f"select trade_date, avg(y_10y) y_10y from read_parquet('{LAKE}/curated/macro/cn_bond_yield.parquet') where curve_name = '中债国债收益率曲线' group by 1").df()
    E = E.merge(Y, on="trade_date"); E["trade_date"] = pd.to_datetime(E.trade_date)
    e = (1 / E.set_index("trade_date").pe - E.set_index("trade_date").y_10y / 100).sort_index()
    z = (e - e.rolling(156, min_periods=104).mean()) / e.rolling(156, min_periods=104).std()
    return z.reindex(index, method="ffill")


def group_weights(R: pd.DataFrame, mix: pd.DataFrame) -> pd.DataFrame:
    """Spread group weights (rows = dates) over the live ETFs of each group by their inner weights."""
    w = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    for g, inner in GROUPS.items():
        cols = list(inner); live = R[cols].notna().astype(float) * pd.Series(inner)
        w[cols] = live.div(live.sum(axis=1).replace(0, np.nan), axis=0).mul(mix[g], axis=0).fillna(0)
    return w


def run(R: pd.DataFrame, cash: pd.Series, w: pd.DataFrame, decide: pd.Series) -> pd.Series:
    w = w.where(decide, np.nan).ffill().fillna(0).shift(1).fillna(0)
    used = w.sum(axis=1)
    return ((w * R.fillna(0)).sum(axis=1) + (1 - used) * cash - COST * w.diff().abs().sum(axis=1)).loc[START:]


def stats(x: pd.Series, cash: pd.Series, turn: float) -> dict:
    ex = x - cash.loc[x.index]; cum = (1 + x).cumprod()
    s = lambda e: e.mean() / e.std() * 252 ** 0.5
    return {"ann": cum.iloc[-1] ** (252 / len(x)) - 1, "vol": x.std() * 252 ** 0.5, "sharpe": s(ex),
            "sharpe_20_22": s(ex[:"2022"]), "sharpe_23_26": s(ex["2023":]), "max_dd": (cum / cum.cummax() - 1).min(),
            "worst_12m": ((1 + x).rolling(252).apply(np.prod, raw=True) - 1).min(), "turnover_y": turn}


def main() -> None:
    R, cash = load()
    idx = R.index
    fri = pd.Series(idx.dayofweek == 4, index=idx)
    month = pd.Series(idx.to_period("M") != idx.to_period("M").to_series().shift(1).to_numpy(), index=idx)
    P = (1 + R.fillna(0)).cumprod().where(R.notna().cumsum() > 0)
    base = pd.DataFrame({g: v for g, v in BASE.items()}, index=idx)
    books, turns = {}, {}

    def add(name: str, w: pd.DataFrame, decide: pd.Series) -> None:
        books[name] = run(R, cash, w, decide)
        ww = w.where(decide, np.nan).ffill().fillna(0)
        turns[name] = ww.diff().abs().sum(axis=1).loc[START:].mean() * 252

    add("M1 固定 25×4 月调", group_weights(R, pd.DataFrame(0.25, index=idx, columns=list(GROUPS))), month)
    w2 = group_weights(R, base); add("M2 固定 股25/债35/金商20/港股20 月调", w2, month)
    gret = pd.DataFrame({g: (group_weights(R, pd.DataFrame({k: 1.0 if k == g else 0.0 for k in GROUPS}, index=idx)) * R.fillna(0)).sum(axis=1)
                         for g in GROUPS})
    iv = 1 / (gret.rolling(60).std() * 252 ** 0.5); rp = iv.div(iv.sum(axis=1), axis=0)
    add("M3 风险平价 月调", group_weights(R, rp), month)
    b2 = (w2.shift(1) * R.fillna(0)).sum(axis=1)
    lev = (0.08 / (b2.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
    add("M4 M2 + 组合目标波动 8%", w2.mul(lev, axis=0), fri)
    sig = sum((P > P.shift(n)).astype(float).where(P.shift(n).notna()) for n in (21, 63, 252)) / 3
    add("M5 M2 + 每只 ETF 趋势开关", w2 * sig.fillna(0), fri)
    a = list(GROUPS["A股"])
    blend = sum((P[a] > P[a].shift(n)).astype(float).where(P[a].shift(n).notna()) for n in (10, 21, 42, 252)) / 4
    size = (0.20 / (R[a].rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
    w6 = w2.copy(); w6[a] = w2[a] * (blend * size).fillna(0)
    add("M6 M2 + A股按计划24仓位", w6, fri)
    z = erp_z(idx).clip(-1, 1).fillna(0)
    mix7 = base.copy(); mix7["A股"] = 0.25 + 0.10 * z; mix7["债券"] = 0.35 - 0.10 * z
    w7 = group_weights(R, mix7); add("M7 M2 + 股债性价比倾斜", w7, fri)
    b6 = (w6.shift(1) * R.fillna(0)).sum(axis=1); lev6 = (0.08 / (b6.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
    add("M8 M6 + 目标波动", w6.mul(lev6, axis=0), fri)
    w9 = w7.copy(); w9[a] = w7[a] * (blend * size).fillna(0)
    b9 = (w9.shift(1) * R.fillna(0)).sum(axis=1); lev9 = (0.08 / (b9.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)
    add("M9 M6 + M7 + 目标波动", w9.mul(lev9, axis=0), fri)
    books["参考 持有510300"] = R["510300.SH"].fillna(0).loc[START:]; turns["参考 持有510300"] = 0.0
    T = pd.DataFrame({k: stats(v, cash, turns[k]) for k, v in books.items()}).T
    T.to_csv(OUT / "systematic.csv"); pd.DataFrame(books).to_csv(OUT / "systematic_daily.csv")
    f = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_12m"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print(f"{START}..{idx[-1].date()}, 15 bp, Sharpe over cash 511880:"); print(f.round(2).to_string())
    Y = pd.DataFrame(books).groupby(lambda d: d.year).apply(lambda g: (1 + g).prod() - 1)
    print("\nBy year:"); print((Y * 100).round(1).to_string())
    print(f"\nERP z now {erp_z(idx).iloc[-1]:+.2f}; A股 plan-24 position now:",
          (blend * size).iloc[-1].round(2).to_dict())


if __name__ == "__main__":
    main()
