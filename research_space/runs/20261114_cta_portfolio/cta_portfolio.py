"""CTA-style portfolio from the 2026-11-14 research sleeves (2026-11-14).

Sleeves (daily P&L, net of costs, each tested alone earlier the same day):
  商品趋势  73 commodity families, MOP 12-month sign x 40% / EWMA vol (com 60), cap 3, set at month end,
            held through the next month; 5 bp on turnover + 10 bp roll a month on the held book.
  价差回归  PTA 加工费, PP − 3×甲醇, 螺纹 / 热卷利润 (the spreads flagged `reversion: true` in
            config/futures_monitor.yaml): position −clip(z_250, ±2) per unit of spread risk, 5 bp per leg notional.
  股指趋势  沪深300 / 中证500 / 中证1000 / 创业板指: long-flat blend of 10/21/42/252-session signals x
            min(1, 20% / 60-day vol), next-day, 5 bp (plan 24 rule).
  国债趋势  T / TF / TS / TL main contracts, MOP 12-month sign, 1 bp + 2 bp roll a quarter.
Portfolio: each sleeve scaled to 10% vol with its trailing 120-day vol (lagged one day, leverage cap 4);
  equal risk across sleeves; variants without one sleeve; plus the A-share index sleeve alone and buy-and-hold.
Common period: first day all sleeves are live (2021) to the last futures day.
Writes sleeves_daily.csv, portfolio_daily.csv, portfolio_stats.csv, portfolio_by_year.csv.
"""
from __future__ import annotations
import contextlib, importlib.util, io, warnings
from pathlib import Path
import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_cta_portfolio"
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mr", HERE.parent / "20261114_mean_reversion/mean_reversion.py")
with contextlib.redirect_stdout(io.StringIO()):
    mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
c = duckdb.connect()
TARGET, VOLWIN, LEV = 0.10, 120, 4.0
REV_KEYS = ("pta_margin", "mto_margin", "rebar_margin", "hrc_margin")


def monthly_tsmom_daily(R: pd.DataFrame, cost: float, roll_month: float) -> pd.Series:
    """MOP 12-month sign x 40%/vol weights set at month end, applied to next month's daily returns."""
    M = (1 + R.fillna(0)).resample("ME").prod() - 1
    M = M.where(R.resample("ME").count() > 10)
    V = ((R.pow(2).ewm(com=60, min_periods=60).mean() * 252) ** 0.5).resample("ME").last()
    past = ((1 + M.fillna(0)).rolling(12).apply(np.prod, raw=True) - 1).where(M.notna().rolling(12).sum() == 12)
    W = (np.sign(past) * (0.40 / V)).clip(-3, 3)                      # decided at month end
    Wd = W.shift(1, freq="D").reindex(R.index, method="ffill")         # live from the next session
    live = Wd.notna() & R.notna()
    n = live.sum(axis=1).replace(0, np.nan)
    gross = (Wd * R).where(live).sum(axis=1) / n
    first = Wd.index.to_series().dt.to_period("M") != Wd.index.to_series().shift(1).dt.to_period("M")
    turn = Wd.fillna(0).diff().abs().where(live).sum(axis=1) / n
    hold = Wd.abs().where(live).sum(axis=1) / n
    return (gross - cost * turn.where(first, 0) - roll_month / 21 * hold).dropna()


def spread_reversion_daily() -> pd.Series:
    spreads = [sp for sp in mr.cfg["spreads"] if sp.get("key") in REV_KEYS and sp.get("kind") != "ratio"]
    out = {}
    for sp in spreads:
        cols = [l["family"] for l in sp["legs"]]
        L = mr.S[cols].dropna()
        s = sum(l["coef"] * L[l["family"]] for l in sp["legs"])
        notional = sum(abs(l["coef"]) * L[l["family"]] for l in sp["legs"])
        ds = s.diff()
        z = (s - s.rolling(250).mean()) / s.rolling(250).std()
        pos = (-z.clip(-2, 2) / ds.rolling(250).std().shift(1)).shift(1)
        out[sp["key"]] = (pos * ds - pos.diff().abs() * notional * 0.0005).dropna()
    print("  spreads in sleeve:", ", ".join(out))
    return pd.DataFrame(out).mean(axis=1).dropna()


def index_trend_daily() -> tuple[pd.Series, pd.Series]:
    I = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
    I["trade_date"] = pd.to_datetime(I.trade_date)
    P = I.pivot(index="trade_date", columns="ts_code", values="close").sort_index()[
        ["000300.SH", "000905.SH", "000852.SH", "399006.SZ"]]
    rets, hold = [], []
    for code in P:
        p = P[code].dropna(); r = p.pct_change()
        blend = pd.concat([(p > p.shift(n)).astype(float).where(p.shift(n).notna()) for n in (10, 21, 42, 252)],
                          axis=1).mean(axis=1, skipna=False)
        w = (blend * (0.20 / (r.rolling(60).std() * 252 ** 0.5)).clip(upper=1.0)).shift(1)
        rets.append((w * r - 0.0005 * w.diff().abs()).rename(code)); hold.append(r.rename(code))
    return pd.concat(rets, axis=1).mean(axis=1).dropna(), pd.concat(hold, axis=1).mean(axis=1).dropna()


def to_target(x: pd.Series) -> pd.Series:
    lev = (TARGET / (x.rolling(VOLWIN, min_periods=60).std() * 252 ** 0.5)).clip(upper=LEV).shift(1)
    return (lev * x).dropna()


def stats(x: pd.Series) -> dict:
    cum = (1 + x).cumprod()
    late = x[x.index >= "2023-01-01"]
    return {"ann": cum.iloc[-1] ** (252 / len(x)) - 1, "vol": x.std() * 252 ** 0.5,
            "sharpe": x.mean() / x.std() * 252 ** 0.5, "t": x.mean() / x.std() * len(x) ** 0.5,
            "max_dd": (cum / cum.cummax() - 1).min(), "sharpe_2023+": late.mean() / late.std() * 252 ** 0.5,
            "worst_month": x.resample("ME").sum().min()}


def main() -> None:
    commod = mr.d.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
    F = c.execute(f"""select m.ts_code fam, m.trade_date, d.close/d.pre_close-1 ret
     from read_parquet('{LAKE}/curated/fut_mapping/**/*.parquet') m
     join read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') d on d.ts_code=m.mapping_ts_code and d.trade_date=m.trade_date
     where m.ts_code in ('T.CFX','TF.CFX','TS.CFX','TL.CFX') and d.pre_close>0""").df()
    F["trade_date"] = pd.to_datetime(F.trade_date)
    bonds = F.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
    idx, idx_hold = index_trend_daily()
    raw = {"商品趋势": monthly_tsmom_daily(commod, 0.0005, 0.0010), "价差回归": spread_reversion_daily(),
           "股指趋势": idx, "国债趋势": monthly_tsmom_daily(bonds, 0.0001, 0.0002 / 3)}
    S = pd.DataFrame({k: to_target(v) for k, v in raw.items()})
    end = min(v.index.max() for v in raw.values())
    S = S.loc[:end].dropna(); start = S.index[0]
    S.to_csv(OUT / "sleeves_daily.csv")
    print(f"common period {start.date()}..{S.index[-1].date()} ({len(S)} sessions)")
    print("\nCorrelation of sleeves (daily):"); print(S.corr().round(2).to_string())
    books = {k: S[k] for k in S}
    books["组合: 四个等风险"] = to_target(S.mean(axis=1))
    for drop in S:
        books[f"组合: 去掉{drop}"] = to_target(S.drop(columns=drop).mean(axis=1))
    books["组合: 只商品(趋势+价差)"] = to_target(S[["商品趋势", "价差回归"]].mean(axis=1))
    books["参考: 4指数等权持有"] = idx_hold.loc[start:end]
    books["参考: 股指趋势(未放大)"] = raw["股指趋势"].loc[start:end]
    B = pd.DataFrame(books).loc[start:end]
    B.to_csv(OUT / "portfolio_daily.csv")
    T = pd.DataFrame({k: stats(v.dropna()) for k, v in B.items()}).T
    T.to_csv(OUT / "portfolio_stats.csv")
    fmt = T.copy()
    for col in ("ann", "vol", "max_dd", "worst_month"):
        fmt[col] = fmt[col].map(lambda v: f"{v*100:+.1f}%")
    pd.set_option("display.width", 240)
    print("\nBooks (net of costs, sleeves at 10% vol):"); print(fmt.round(2).to_string())
    Y = B.groupby(B.index.year).apply(lambda g: (1 + g).prod() - 1)
    Y.to_csv(OUT / "portfolio_by_year.csv")
    print("\nBy year:"); print((Y * 100).round(1).to_string())


if __name__ == "__main__":
    main()
