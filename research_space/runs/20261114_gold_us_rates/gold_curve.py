"""Gold vs the US curve: short end, long end and shape (2026-11-14). User: "长端，短端，以及结构".

US nominal curve us_tycr (m3, y2, y10, y30) and real curve us_trycr (y5, y10, y30), fetched once into the run folder.
Gold = 黄金ETF 518880 (CNY). Weekly gold return vs weekly changes in: 3m, 2y, 10y, 30y nominal; 10y real; 10y breakeven
(nominal − real); slopes 10y−2y and 30y−3m. Correlations full period, by 2-year block and 2026; multiple regression on
short (2y), long (10y) and slope; gold after steepening vs flattening weeks; curve now vs 1 year.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_gold_us_rates"
pd.set_option("display.width", 220)
FIELDS = {"us_tycr": ["date", "m3", "y2", "y5", "y10", "y30"], "us_trycr": ["date", "y5", "y10", "y30"]}


def fetch(api: str) -> pd.DataFrame:
    f = OUT / f"{api}_curve.csv"
    if f.exists():
        return pd.read_csv(f, dtype={"date": str})
    client = TushareClient(Config.load().tushare, Clock())
    D = pd.concat([client.query(api, {"start_date": f"{y}0101", "end_date": f"{y}1231"}, FIELDS[api]) for y in range(2013, 2027)])
    D = D.drop_duplicates("date"); D.to_csv(f, index=False)
    return D


def main() -> None:
    n = fetch("us_tycr").set_index("date").add_prefix("n_"); r = fetch("us_trycr").set_index("date").add_prefix("r_")
    Y = n.join(r, how="outer"); Y.index = pd.to_datetime(Y.index); Y = Y.sort_index().astype(float)
    Y["be10"] = Y.n_y10 - Y.r_y10; Y["s10_2"] = Y.n_y10 - Y.n_y2; Y["s30_3m"] = Y.n_y30 - Y.n_m3
    G = duckdb.connect().execute(f"select trade_date, close/pre_close-1 r from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet') where ts_code='518880.SH' and pre_close>0").df()
    G["trade_date"] = pd.to_datetime(G.trade_date); gp = (1 + G.set_index("trade_date").r.sort_index().clip(-0.2, 0.2)).cumprod()
    W = pd.concat([gp.resample("W-FRI").last().rename("gold"), Y.resample("W-FRI").last()], axis=1).dropna()
    cols = {"n_m3": "3月", "n_y2": "2年", "n_y10": "10年", "n_y30": "30年", "r_y10": "10年实际", "be10": "10年通胀预期", "s10_2": "10-2利差", "s30_3m": "30y-3m利差"}
    d = W[list(cols)].diff().rename(columns=cols); d["gold"] = W.gold.pct_change(); d = d.dropna()
    blocks = {"全期": d, **{f"{a}-{a+1}": d.loc[str(a):str(a + 1)] for a in range(2014, 2026, 2)}, "2026": d.loc["2026"]}
    C = pd.DataFrame({k: z.drop(columns="gold").corrwith(z.gold) for k, z in blocks.items()}).T
    print("weekly corr(gold return, Δ yield):"); print(C.round(2).to_string())
    beta = {k: (np.polyfit(z[c], z.gold, 1)[0] * 0.10 * 100) for k, z in (("全期", d), ("2026", d.loc["2026"])) for c in [None] if False}
    print("\n% gold per +10 bp (simple beta):")
    print(pd.DataFrame({k: {c: np.polyfit(z[c], z.gold, 1)[0] * 0.10 * 100 for c in cols.values()} for k, z in (("全期", d), ("2026", d.loc["2026"]))}).round(2).T.to_string())
    for k, z in (("全期", d), ("2024-25", d.loc["2024":"2025"]), ("2026", d.loc["2026"])):
        X = np.column_stack([np.ones(len(z)), z["2年"], z["10-2利差"], z["10年通胀预期"]]); b, *_ = np.linalg.lstsq(X, z.gold, rcond=None)
        pred = X @ b; r2 = 1 - ((z.gold - pred) ** 2).sum() / ((z.gold - z.gold.mean()) ** 2).sum()
        print(f"regression {k}: per +10 bp  2y {b[1]*10:+.2f}%, slope(10-2) {b[2]*10:+.2f}%, breakeven {b[3]*10:+.2f}%  R2 {r2:.2f}")
    # 4-week regimes: bear/bull steepener / flattener
    m = W.resample("4W-FRI").last(); q = pd.DataFrame({"gold": m.gold.pct_change(), "short": m.n_y2.diff(), "long": m.n_y10.diff()}).dropna()
    q["regime"] = np.select([(q.long > 0) & (q.long > q.short), (q.long > 0) & (q.long <= q.short), (q.long <= 0) & (q.long < q.short), (q.long <= 0) & (q.long >= q.short)],
                            ["熊陡(长端领涨)", "熊平(短端领涨)", "牛陡(短端领跌)" if False else "牛平(长端领跌)", "牛陡(短端领跌)"], "其他")
    print("\n4-week gold return by curve move:"); print(q.groupby("regime").gold.agg(["mean", "median", "count", lambda x: (x > 0).mean()]).rename(columns={"<lambda_0>": "上涨占比"}).round(3).to_string())
    last = W.iloc[-1]; y1 = W.loc[W.index >= W.index[-1] - pd.Timedelta(days=365)]; s = W.loc["2025-12-31":].iloc[0]
    print(f"\ncurve {W.index[-1].date()} (年初 → 现在, 1年区间):")
    for c, nm in cols.items():
        print(f"  {nm:10s} {s[c]:6.2f} → {last[c]:6.2f} ({(last[c]-s[c])*100:+4.0f} bp)  1y {y1[c].min():.2f}..{y1[c].max():.2f}")
    C.to_csv(OUT / "gold_curve_corr.csv")


if __name__ == "__main__":
    main()
