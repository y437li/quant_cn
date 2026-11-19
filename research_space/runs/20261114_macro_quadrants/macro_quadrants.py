"""Macro quadrants of the plan 27 book (2026-11-14). User: "感觉像是个宏观策略" -> "看看".

Growth = China official manufacturing PMI, inflation = PPI y/y (CPI y/y as a check). Direction = 3-month average now vs
3 months earlier. Two labellings:
  known    -- the regime as it was knowable that day (value used from its release date; release table to 2025, then
              month end + lag 7 days PMI / 20 days CPI PPI as D-086). Shows what a trader could have seen.
  hindsight -- the regime of the calendar month the data describes. Shows the book's true macro exposure.
Per regime: annualised return of each group (股票 A股+港股 2:1, 黄金, 商品, 债券 5y+30y, all equal-member, no timing)
and of the 60/40 book (param_sensitivity.BASE), 2014-01..2026-11, futures / curve proxies before ETF listing.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import duckdb, numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ps", HERE.parent / "20261114_etf_universe/param_sensitivity.py")
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
LAKE = Path("/Volumes/Treasury/quant_cn_lake"); M = LAKE / "curated/macro"
OUT = LAKE / "meta/runs/research/20261114_macro_quadrants"; OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 240)
SERIES = {"pmi": ("cn_pmi", "pmi010000", "release_pmi", 7), "ppi": ("cn_ppi", "ppi_yoy", "release_ppi", 20),
          "cpi": ("cn_cpi", "nt_yoy", "release_cpi", 20)}
GROUPS = {"股票": {**{x: 2.0 for x in ps.A}, **{x: 4 / 3 for x in ps.HK}}, "黄金": {"518880.SH": 1.0},
          "商品": {"159980.SZ": 1.0, "159981.SZ": 1.0, ps.om.OIL: 1.0}, "债券": {c: 1.0 for c in ps.BONDS}}
NAMES = {(1, 1): "增长↑通胀↑ 过热", (1, -1): "增长↑通胀↓ 复苏", (-1, 1): "增长↓通胀↑ 滞胀", (-1, -1): "增长↓通胀↓ 衰退"}


def load_macro(key: str) -> pd.DataFrame:
    """Monthly value by data month, with the date it became known."""
    table, col, rel, lag = SERIES[key]; c = duckdb.connect()
    v = c.execute(f"select month, {col} v from '{M / table}.parquet'").df()
    v["month"] = pd.PeriodIndex(v["month"], freq="M")
    r = c.execute(f"select release_date, actual from '{M / rel}.parquet' where release_date >= '20120101'").df()
    r["known"] = pd.to_datetime(r["release_date"]); r["month"] = (r["known"] - pd.Timedelta(days=lag + 3)).dt.to_period("M")
    r = r.drop_duplicates("month", keep="last").rename(columns={"actual": "v"})[["month", "v", "known"]]
    v["known"] = v["month"].dt.to_timestamp(how="end").dt.normalize() + pd.Timedelta(days=lag)
    v = v.merge(r[["month", "known"]], on="month", how="left", suffixes=("", "_r"))
    v["known"] = v["known_r"].fillna(v["known"]); v = v.drop(columns="known_r")
    old = r[r["month"] < v["month"].min()]
    out = pd.concat([old, v]).sort_values("month").set_index("month")
    out["dir"] = np.sign(out["v"].rolling(3).mean().diff(3)).replace(0, np.nan).ffill()
    return out


def label(idx: pd.DatetimeIndex, infl: str) -> pd.DataFrame:
    g, i = load_macro("pmi"), load_macro(infl)
    known = pd.DataFrame({k: s.set_index("known")["dir"].reindex(idx, method="ffill") for k, s in (("g", g), ("i", i))})
    per = idx.to_period("M")
    hind = pd.DataFrame({"g": g["dir"].reindex(per).to_numpy(), "i": i["dir"].reindex(per).to_numpy()}, index=idx)
    to = lambda f: pd.Series([NAMES.get((a, b)) if pd.notna(a) and pd.notna(b) else None for a, b in zip(f["g"], f["i"])], index=idx)
    return pd.DataFrame({"known": to(known), "hindsight": to(hind)})


def table(rets: pd.DataFrame, reg: pd.Series) -> pd.DataFrame:
    x = rets.assign(reg=reg).dropna(subset=["reg"])
    ann = x.groupby("reg").mean() * 252
    share = x.groupby("reg").size() / len(x)
    hit = x.groupby("reg")["组合"].apply(lambda s: (s.groupby(s.index.to_period("M")).sum() > 0).mean())
    return ann.assign(占比=share, 组合月胜率=hit).reindex(list(NAMES.values()))


def main() -> None:
    R, cash = ps.load(); R = R.loc["2014-01-01":]; cash = cash.loc[R.index]
    gr = pd.DataFrame({g: R[list(m)].fillna(0).mul(pd.Series(m)).sum(axis=1)
                       / R[list(m)].notna().mul(pd.Series(m)).sum(axis=1).replace(0, np.nan) for g, m in GROUPS.items()})
    rets = gr.assign(组合=ps.book(R, cash, ps.BASE)).sub(cash, axis=0)  # excess over cash
    rows = []
    for infl in ("ppi", "cpi"):
        lab = label(R.index, infl)
        for kind in ("known", "hindsight"):
            t = table(rets, lab[kind]); t.to_csv(OUT / f"quadrants_{infl}_{kind}.csv")
            print(f"\n== 通胀={infl.upper()}  {kind}  (年化超额收益, 2014-01..2026-11)"); print(t.round(3))
            rows.append(lab[kind].rename(f"{infl}_{kind}"))
    lab = pd.concat(rows, axis=1); lab.to_csv(OUT / "regimes_daily.csv")
    print("\n最近的象限 (known, PPI):"); m = lab["ppi_known"].groupby(lab.index.to_period("M")).last()
    print(m.tail(14).to_string())
    yr = rets["组合"].groupby(rets.index.year).sum()
    dom = lab["ppi_hindsight"].groupby(lab.index.year).agg(lambda s: s.value_counts().idxmax() if s.notna().any() else None)
    print("\n每年组合超额 & 主导象限 (hindsight PPI):"); print(pd.DataFrame({"组合": yr.round(3), "象限": dom}).to_string())


if __name__ == "__main__":
    main()
