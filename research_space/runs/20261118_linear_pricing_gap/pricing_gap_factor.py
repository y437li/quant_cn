"""Linear-pricing gap as a factor: log(market cap / value from consensus with fading growth).

Month ends 2019-01 .. 2026-11. Consensus (report_rc, report_date in the trailing 90 days, latest
per broker and fiscal year, median np): FY1 = the as-of year from May, else the year before;
FY2, FY3 follow (FY3 missing -> FY2 x (1 + FY1->FY2 growth)). FY1 and FY2 must be > 0.
Value at d: FY1..FY3 profit discounted at 9% from each fiscal year end, then growth starting at
FY2->FY3 growth (clipped to [-0.3, 1.0]) fading x0.7 a year for 7 years, exit PE 15. Gap =
log(total_mv / value). Fixed in advance; one sensitivity run (fade 0.5, exit 20).
Tests: monthly rank IC with forward 20 / 60-session returns; decile spread; Fama-MacBeth on
ranks with controls (forward EP FY1/mv, trailing EP 1/pe_ttm, FY1->FY2 growth, log size,
reversal 20d, momentum 250-20d, turnover 20d); Newey-West t (lag 1 for 20d, 3 for 60d).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
R, YEARS = 0.09, 7
FADE, EXIT = (0.5, 20.0) if "--alt" in sys.argv else (0.7, 15.0)
CONTROLS = ["fep", "tep", "grow", "size", "rev20", "mom", "turn"]
_CONS = """
WITH w AS (
  SELECT ts_code, org_name, quarter, np, report_date FROM curated.report_rc
  WHERE report_date > ? AND report_date <= ? AND np IS NOT NULL AND quarter LIKE '%Q4'),
l AS (SELECT ts_code, quarter, arg_max(np, report_date) AS np FROM w GROUP BY ts_code, org_name, quarter)
SELECT ts_code, substr(quarter, 1, 4)::INT AS fy, median(np) AS np, count(*) AS n FROM l GROUP BY 1, 2
"""


def get_month_ends(q: LakeQuery) -> list[str]:
    cal = q.sql("SELECT DISTINCT trade_date FROM derived.prices_adj WHERE trade_date >= '20181201'")
    s = cal["trade_date"].astype(str).sort_values()
    return s.groupby(s.str[:6]).max().tolist()


def compute_value(f1: np.ndarray, f2: np.ndarray, f3: np.ndarray, t1: np.ndarray) -> np.ndarray:
    """t1 = years from d to the FY1 end (may be <= 0 when FY1 just ended: floored at 0.1)."""
    t1 = np.maximum(t1, 0.1)
    v = f1 / (1 + R) ** t1 + f2 / (1 + R) ** (t1 + 1) + f3 / (1 + R) ** (t1 + 2)
    g = np.clip(f3 / f2 - 1, -0.3, 1.0)
    x = f3.copy()
    for k in range(1, YEARS + 1):
        g = g * FADE
        x = x * (1 + g)
        v = v + x / (1 + R) ** (t1 + 2 + k)
    return v + EXIT * x / (1 + R) ** (t1 + 2 + YEARS)


def build_panel(q: LakeQuery) -> pd.DataFrame:
    ends = get_month_ends(q)
    px = q.sql("SELECT trade_date, ts_code, close_adj, amount FROM derived.prices_adj "
               "WHERE trade_date >= '20171201' AND ts_code NOT LIKE '%.BJ'")
    close = px.pivot(index="trade_date", columns="ts_code", values="close_adj").sort_index()
    close.index = close.index.astype(str)
    dates = close.index.tolist()
    pos = {d: i for i, d in enumerate(dates)}
    lr = np.log(close).diff()
    lr = lr.where(lr.abs() < 0.25)
    cum = lr.fillna(0).cumsum()
    out = []
    for d in ends:
        if d not in pos or pos[d] < 250:
            continue
        i = pos[d]
        y, m = int(d[:4]), int(d[4:6])
        fy1 = y if m >= 5 else y - 1
        start = (pd.Timestamp(d) - pd.Timedelta(days=90)).strftime("%Y%m%d")
        cons = q.sql(_CONS, [start, d])
        wide = cons.pivot(index="ts_code", columns="fy", values="np")
        if fy1 not in wide or fy1 + 1 not in wide:
            continue
        f1, f2 = wide[fy1], wide[fy1 + 1]
        f3 = wide[fy1 + 2] if fy1 + 2 in wide else pd.Series(np.nan, index=wide.index)
        f3 = f3.fillna(f2 * (f2 / f1))
        ok = (f1 > 0) & (f2 > 0) & (f3 > 0)
        f1, f2, f3 = f1[ok], f2[ok], f3[ok]
        t1 = (pd.Timestamp(f"{fy1}1231") - pd.Timestamp(d)).days / 365.25
        val = compute_value(f1.to_numpy(), f2.to_numpy(), f3.to_numpy(), np.full(len(f1), t1))
        db = q.sql("SELECT ts_code, total_mv, pe_ttm, turnover_rate FROM curated.daily_basic WHERE trade_date = ?", [d]).set_index("ts_code")
        frame = pd.DataFrame({"f1": f1, "f2": f2, "value": val}).join(db, how="inner")
        frame = frame[frame.index.isin(close.columns)]
        codes = frame.index
        mv = frame["total_mv"]  # 万元, report_rc np in 万元
        frame["gap"] = np.log(mv / frame["value"])
        frame["fep"] = frame["f1"] / mv
        frame["tep"] = 1 / frame["pe_ttm"].where(frame["pe_ttm"] > 0)
        frame["grow"] = frame["f2"] / frame["f1"] - 1
        frame["size"] = np.log(mv)
        c = cum[codes]
        frame["rev20"] = c.iloc[i] - c.iloc[i - 20]
        frame["mom"] = c.iloc[i - 20] - c.iloc[i - 250]
        frame["turn"] = q.sql("SELECT ts_code, avg(turnover_rate) t FROM curated.daily_basic WHERE trade_date > ? AND trade_date <= ? GROUP BY 1",
                              [dates[i - 20], d]).set_index("ts_code")["t"].reindex(codes)
        for h in (20, 60):
            frame[f"fwd{h}"] = (c.iloc[i + h] - c.iloc[i]) if i + h < len(dates) else np.nan
        live = close[codes].iloc[i].notna()
        frame = frame[live.to_numpy()]
        frame["date"] = d
        out.append(frame.reset_index(names="ts_code"))
    return pd.concat(out, ignore_index=True)


def newey_west_t(x: pd.Series, lag: int) -> float:
    x = x.dropna().to_numpy()
    n, e = len(x), x - x.mean()
    s = (e @ e) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return x.mean() / np.sqrt(s / n)


def rank(f: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return f[cols].rank(pct=True) - 0.5


def summarise(p: pd.DataFrame) -> None:
    pd.set_option("display.width", 200)
    print("months", p["date"].nunique(), "stock-months", len(p), "median stocks/month", p.groupby("date").size().median())
    print("gap quantiles", p["gap"].quantile([0.1, 0.5, 0.9]).round(2).to_dict())
    corr = p.groupby("date")[["gap", *CONTROLS]].apply(lambda f: f.rank().corr()["gap"]).mean().round(2)
    print("mean rank corr of gap with controls", corr.drop("gap").to_dict())
    for h, lag in ((20, 1), (60, 3)):
        y = f"fwd{h}"
        sub = p.dropna(subset=[y])
        ic = sub.groupby("date").apply(lambda f: f["gap"].rank().corr(f[y].rank()))
        dec = sub.groupby("date").apply(lambda f: f.assign(d=pd.qcut(f["gap"].rank(method="first"), 10, labels=False)).groupby("d")[y].mean())
        spread = (dec[9] - dec[0]) * 100
        fm, resid = [], []
        for _, f in sub.groupby("date"):
            f = f.dropna(subset=["gap", *CONTROLS])
            if len(f) < 100:
                continue
            X = np.column_stack([np.ones(len(f)), rank(f, ["gap", *CONTROLS]).to_numpy()])
            yy = (f[y].rank(pct=True) - 0.5).to_numpy()
            fm.append(np.linalg.lstsq(X, yy, rcond=None)[0][1])
            Xc = np.column_stack([np.ones(len(f)), rank(f, CONTROLS).to_numpy()])
            g = (f["gap"].rank(pct=True) - 0.5).to_numpy()
            e = g - Xc @ np.linalg.lstsq(Xc, g, rcond=None)[0]
            resid.append(np.corrcoef(e, yy)[0, 1])
        fm, resid = pd.Series(fm), pd.Series(resid)
        print(f"\n## fwd{h}: rank IC {ic.mean():.4f} (NW t {newey_west_t(ic, lag):.2f}, IC<0 share {(ic < 0).mean():.0%}); "
              f"decile 10-1 {spread.mean():.2f}% (NW t {newey_west_t(spread, lag):.2f})")
        print(f"   net of controls: FM slope {fm.mean():.4f} (NW t {newey_west_t(fm, lag):.2f}); residual IC {resid.mean():.4f} (NW t {newey_west_t(resid, lag):.2f})")
        print("   decile means %:", (dec.mean() * 100).round(2).tolist())
        yr = ic.groupby(ic.index.str[:4]).mean().round(3)
        print("   IC by year:", yr.to_dict())


def main() -> None:
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    panel = build_panel(LakeQuery(cat))
    cat.close()
    print(f"fade {FADE}, exit PE {EXIT}")
    summarise(panel)
    out = Path(cfg.lake.root) / "meta/runs/research/20261118_linear_pricing_gap"
    out.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out / f"panel_{FADE}_{EXIT:.0f}.parquet")


if __name__ == "__main__":
    main()
