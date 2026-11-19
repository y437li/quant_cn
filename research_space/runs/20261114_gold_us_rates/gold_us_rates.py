"""Gold vs US Treasury yields (2026-11-14). User: "黄金也在跌" / "看一下跟美债利率的相关性？".

US nominal 10y (Tushare us_tycr y10) and real 10y (us_trycr y10, TIPS) fetched once into the run folder (not a lake dataset);
gold = 黄金ETF 518880 (CNY, from curated fund_daily) and SGE Au99.99 (curated sge_daily), plus USD gold implied via USDCNH if present.
Reports: correlation of weekly gold returns with weekly yield changes (full period and by 2-year block), rolling 52-week
correlation, beta (% gold per +10 bp), levels now vs 1-year range, and this year's moves.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_gold_us_rates"; OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 220)


def fetch(api: str) -> pd.DataFrame:
    f = OUT / f"{api}.csv"
    if f.exists():
        return pd.read_csv(f, dtype={"date": str})
    client = TushareClient(Config.load().tushare, Clock())
    parts = []
    for y in range(2013, 2027):
        parts.append(client.query(api, {"start_date": f"{y}0101", "end_date": f"{y}1231"}, ["date", "y5", "y10", "y30"]))
    D = pd.concat(parts).drop_duplicates("date"); D.to_csv(f, index=False)
    return D


def main() -> None:
    nom = fetch("us_tycr").rename(columns={"y10": "nom10"})[["date", "nom10"]]
    real = fetch("us_trycr").rename(columns={"y10": "real10"})[["date", "real10"]]
    Y = nom.merge(real, on="date", how="outer"); Y["date"] = pd.to_datetime(Y.date); Y = Y.set_index("date").sort_index().astype(float)
    c = duckdb.connect()
    G = c.execute(f"select trade_date, close/pre_close-1 r from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet') where ts_code='518880.SH' and pre_close>0").df()
    G["trade_date"] = pd.to_datetime(G.trade_date); g = G.set_index("trade_date").r.sort_index().clip(-0.2, 0.2)
    gp = (1 + g).cumprod()
    W = pd.concat([gp.resample("W-FRI").last().rename("gold"), Y.resample("W-FRI").last()], axis=1).dropna()
    wk = pd.DataFrame({"gold": W.gold.pct_change(), "d_nom": W.nom10.diff(), "d_real": W.real10.diff()}).dropna()
    print(f"weekly {wk.index[0].date()}..{wk.index[-1].date()}, {len(wk)} weeks")
    def row(z):
        b_n = np.polyfit(z.d_nom, z.gold, 1)[0] * 0.10; b_r = np.polyfit(z.d_real, z.gold, 1)[0] * 0.10
        return {"corr_名义10y": z.gold.corr(z.d_nom), "corr_实际10y": z.gold.corr(z.d_real), "每+10bp名义": b_n, "每+10bp实际": b_r, "周数": len(z)}
    T = pd.DataFrame({"全期": row(wk), **{f"{a}-{a+1}": row(wk.loc[str(a):str(a + 1)]) for a in range(2014, 2027, 2) if len(wk.loc[str(a):str(a + 1)]) > 30}}).T
    print(T.round(3).to_string())
    roll = wk.gold.rolling(52).corr(wk.d_real)
    print("\nrolling 52w corr(gold, real 10y) at year ends:"); print(roll.groupby(roll.index.year).last().round(2).to_string())
    print(f"latest rolling 52w: real {roll.iloc[-1]:.2f}, nominal {wk.gold.rolling(52).corr(wk.d_nom).iloc[-1]:.2f}")
    last = W.iloc[-1]; y1 = W.loc[W.index >= W.index[-1] - pd.Timedelta(days=365)]
    print(f"\nnow {W.index[-1].date()}: nominal 10y {last.nom10:.2f}% (1y {y1.nom10.min():.2f}..{y1.nom10.max():.2f}), real 10y {last.real10:.2f}% ({y1.real10.min():.2f}..{y1.real10.max():.2f})")
    for a, b in (("2025-12-31", None), ("2026-06-30", None)):
        z = W.loc[a:]; print(f"since {a}: gold {z.gold.iloc[-1]/z.gold.iloc[0]-1:+.1%}, nominal {(z.nom10.iloc[-1]-z.nom10.iloc[0])*100:+.0f} bp, real {(z.real10.iloc[-1]-z.real10.iloc[0])*100:+.0f} bp")
    q = W.resample("QE").last(); qq = pd.DataFrame({"gold": q.gold.pct_change(), "d_real_bp": q.real10.diff() * 100, "d_nom_bp": q.nom10.diff() * 100}).loc["2024":]
    print("\nquarterly:"); print((qq.assign(gold=qq.gold * 100)).round(1).to_string())
    T.to_csv(OUT / "gold_us_rates.csv")


if __name__ == "__main__":
    main()
