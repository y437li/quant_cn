"""Is A-share earnings news priced in before disclosure? Event study 2019-2026.

Event = first disclosure of a quarter (min ann_date of forecast_vip, express_vip, income_vip).
Surprise = SUE: single-quarter net profit yoy change / std of the prior 8 yoy changes (>= 4).
Excess = log return minus the equal-weight market (all A shares), windows in trading days:
pre [-60,-1], reaction [0,+1], post [+2,+60]. Deciles by SUE within each end_date.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
START = "20180601"
WINDOWS = {"pre60": (-60, -1), "pre20": (-20, -1), "react": (0, 1), "post20": (2, 21), "post60": (2, 61)}


def load(q: LakeQuery) -> tuple[pd.DataFrame, pd.DataFrame]:
    px = q.sql("SELECT trade_date, ts_code, close_adj FROM derived.prices_adj "
               "WHERE trade_date >= ? AND ts_code NOT LIKE '%.BJ'", [START])
    inc = q.sql("""SELECT ts_code, end_date, arg_min(n_income_attr_p, ann_date) AS cum, min(ann_date) AS ann
                   FROM curated.income_vip WHERE report_type = '1' AND n_income_attr_p IS NOT NULL
                   GROUP BY 1, 2""")
    first = q.sql("""SELECT ts_code, end_date, min(ann_date) AS first_ann FROM (
                       SELECT ts_code, end_date, ann_date FROM curated.forecast_vip
                       UNION ALL SELECT ts_code, end_date, ann_date FROM curated.express_vip
                       UNION ALL SELECT ts_code, end_date, ann_date FROM curated.income_vip WHERE report_type='1')
                     GROUP BY 1, 2""")
    return px, inc.merge(first, on=["ts_code", "end_date"])


def build_events(inc: pd.DataFrame) -> pd.DataFrame:
    inc = inc.sort_values(["ts_code", "end_date"]).copy()
    inc["year"], inc["q"] = inc["end_date"].str[:4], inc["end_date"].str[4:6].astype(int) // 3
    prev = inc.groupby(["ts_code", "year"])["cum"].shift()
    prev_q = inc.groupby(["ts_code", "year"])["q"].shift()
    inc["sq"] = np.where(inc["q"] == 1, inc["cum"], np.where(prev_q == inc["q"] - 1, inc["cum"] - prev, np.nan))
    inc["key"] = inc["year"].astype(int) * 4 + inc["q"]
    lag = inc[["ts_code", "key", "sq"]].assign(key=lambda f: f["key"] + 4).rename(columns={"sq": "sq_ly"})
    inc = inc.merge(lag, on=["ts_code", "key"], how="left")
    inc["d"] = inc["sq"] - inc["sq_ly"]
    sd = inc.groupby("ts_code")["d"].transform(lambda s: s.shift().rolling(8, min_periods=4).std())
    inc["sue"] = inc["d"] / sd.where(sd > 0)
    ev = inc.dropna(subset=["sue"])
    ev = ev[ev["first_ann"] >= "20190101"].copy()
    ev["dec"] = ev.groupby("end_date")["sue"].transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
    return ev


def attach_car(ev: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    close = px.pivot(index="trade_date", columns="ts_code", values="close_adj").sort_index()
    lr = np.log(close).diff()
    lr = lr.where(lr.abs() < 0.25)  # drop glitches / relisting gaps
    ar = lr.sub(lr.mean(axis=1), axis=0)
    cum = ar.fillna(0).cumsum()
    live = close.notna()
    dates = close.index.to_numpy()
    cols = {c: i for i, c in enumerate(close.columns)}
    ev = ev[ev["ts_code"].isin(cols)].copy()
    d0 = np.searchsorted(dates, ev["first_ann"].to_numpy())
    ci = ev["ts_code"].map(cols).to_numpy()
    cm, lv, n = cum.to_numpy(), live.to_numpy(), len(dates)
    ok_pre = (d0 - 61 >= 0) & (d0 < n)
    ok_pre[ok_pre] = lv[d0[ok_pre] - 61, ci[ok_pre]]
    for name, (a, b) in WINDOWS.items():
        lo, hi = d0 + a - 1, d0 + b
        ok = ok_pre & (hi < n) & (lo >= 0)
        out = np.full(len(ev), np.nan)
        out[ok] = (cm[hi[ok], ci[ok]] - cm[lo[ok], ci[ok]]) * 100
        ev[name] = out
    ev["first_day"] = np.where(d0 < n, dates[np.minimum(d0, n - 1)], None)
    return ev[ok_pre]


def summarise(ev: pd.DataFrame) -> None:
    cols = list(WINDOWS)
    print("events", len(ev), "quarters", ev["end_date"].nunique())
    t = ev.groupby("dec")[cols].mean().round(2)
    t["n"] = ev.groupby("dec").size()
    print("\n## mean excess % by SUE decile (0 = worst)\n", t.to_string())
    spread = ev[ev.dec == 9][cols].mean() - ev[ev.dec == 0][cols].mean()
    print("\n## top-bottom spread\n", spread.round(2).to_string())
    print("\n## share of the spread (pre60 + react + post60):",
          (spread[["pre60", "react", "post60"]] / spread[["pre60", "react", "post60"]].sum()).round(2).to_dict())
    # per quarter spread t-stat
    g = ev.groupby(["end_date", "dec"])[cols].mean().unstack("dec")
    for c in cols:
        s = g[c][9] - g[c][0]
        print(f"{c}: spread mean {s.mean():.2f}, t {s.mean() / s.std() * np.sqrt(s.count()):.2f}, quarters {s.count()}")
    # rank IC of SUE vs each window
    ic = {c: ev.groupby("end_date").apply(lambda f: f["sue"].rank().corr(f[c].rank())).mean() for c in cols}
    print("\n## mean rank IC (SUE vs window)", {k: round(v, 3) for k, v in ic.items()})
    # 利好出尽: surprise quintile x pre-run quintile -> post60
    ev = ev.copy()
    ev["sq5"] = ev.dec // 2
    ev["pre5"] = ev.groupby("end_date")["pre60"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    print("\n## post60 by SUE quintile (rows) x pre60 quintile (cols)\n",
          ev.pivot_table(index="sq5", columns="pre5", values="post60", aggfunc="mean").round(2).to_string())
    print("\n## react by SUE quintile x pre60 quintile\n",
          ev.pivot_table(index="sq5", columns="pre5", values="react", aggfunc="mean").round(2).to_string())
    print("\n## by year: top-bottom spread")
    ev["yr"] = ev["first_ann"].str[:4]
    y = ev.groupby(["yr", "dec"])[cols].mean().unstack("dec")
    print(pd.DataFrame({c: y[c][9] - y[c][0] for c in cols}).round(2).to_string())


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    px, inc = load(LakeQuery(cat))
    cat.close()
    ev = attach_car(build_events(inc), px)
    pd.set_option("display.width", 200)
    summarise(ev)
    out = Path(cfg.lake.root) / "meta/runs/research/20261118_priced_in"
    out.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(out / "events.parquet")


if __name__ == "__main__":
    main()
