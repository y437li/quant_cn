"""Market beta of the CTA futures book and the ETF books (2026-11-14).

Books: futures equal-risk book and sleeves (20261114_cta_portfolio/portfolio_daily.csv, sleeves_daily.csv);
ETF 25%-per-group books (etf_equal_capital_daily.csv, 5 bp).
Market: 沪深300 index (000300.SH). Weekly returns (Friday, so QDII / overseas lags line up).
Reports: beta and annual alpha (OLS on weekly excess-free returns), correlation, beta in up / down market weeks,
the 20 worst 沪深300 weeks (book mean vs market mean), and a 4-factor fit for the ETF trend book on the
group hold returns (A股 / 债券 / 商品 / 海外): how much is the static mix.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
RES = LAKE / "meta/runs/research"
OUT = RES / "20261114_cta_horizon_etf"
c = duckdb.connect()
pd.set_option("display.width", 240)


def weekly(x: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return (1 + x.fillna(0)).resample("W-FRI").prod() - 1


def ols(y: pd.Series, X: pd.DataFrame) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X.to_numpy()])
    return np.linalg.lstsq(A, y.to_numpy(), rcond=None)[0]


def main() -> None:
    I = c.execute(f"select trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet') where ts_code='000300.SH'").df()
    I["trade_date"] = pd.to_datetime(I.trade_date)
    mkt = I.set_index("trade_date").close.sort_index().pct_change()
    B = pd.read_csv(RES / "20261114_cta_portfolio/portfolio_daily.csv", index_col=0, parse_dates=True)
    S = pd.read_csv(RES / "20261114_cta_portfolio/sleeves_daily.csv", index_col=0, parse_dates=True)
    E = pd.read_csv(OUT / "etf_equal_capital_daily.csv", index_col=0, parse_dates=True)
    books = {"期货组合(10%波动)": B["组合: 四个等风险"], **{f"  {k}": S[k] for k in S},
             "ETF 短周期 周调": E["10/21/42/252天 周调"], "ETF 21/63/252 周调": E["21/63/252天 周调"],
             "ETF 12个月 周调": E["252天 周调"], "ETF 一直持有": E["一直持有 周调"]}
    rows = []
    m = weekly(mkt)
    worst = None
    for name, x in books.items():
        y = weekly(x.dropna()); j = pd.concat([y.rename("y"), m.rename("m")], axis=1).dropna()
        j = j[(j.y != 0) | (j.m != 0)]
        a, b = ols(j.y, j[["m"]])
        up, dn = j[j.m > 0], j[j.m < 0]
        worst = j.m.nsmallest(20).index
        rows.append({"book": name, "weeks": len(j), "beta": b, "alpha_ann": a * 52, "corr": j.y.corr(j.m),
                     "beta_up": ols(up.y, up[["m"]])[1], "beta_down": ols(dn.y, dn[["m"]])[1],
                     "worst20_book": j.loc[worst, "y"].mean(), "worst20_mkt": j.loc[worst, "m"].mean()})
    T = pd.DataFrame(rows); T.to_csv(OUT / "beta_check.csv", index=False)
    f = T.copy()
    for col in ("alpha_ann", "worst20_book", "worst20_mkt"):
        f[col] = f[col].map(lambda v: f"{v*100:+.1f}%")
    print("Beta to 沪深300, weekly returns:"); print(f.round(2).to_string(index=False))

    # ETF trend book on the four group hold returns
    codes = {"A股": ["510300.SH", "510500.SH", "512100.SH", "159915.SZ"], "债券": ["511010.SH", "511260.SH", "511020.SH", "511090.SH"],
             "商品": ["518880.SH", "161226.SZ", "159985.SZ", "159980.SZ", "159981.SZ"],
             "海外": ["513100.SH", "513500.SH", "513520.SH", "513030.SH", "159920.SZ", "513050.SH"]}
    allc = [x for v in codes.values() for x in v]
    F = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
                      where ts_code in ({','.join(repr(x) for x in allc)}) and pre_close > 0""").df()
    F["trade_date"] = pd.to_datetime(F.trade_date)
    R = F.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
    G = weekly(pd.DataFrame({g: R[v].mean(axis=1) for g, v in codes.items()}))
    print("\nETF books on the four group hold returns (weekly; loadings ≈ average capital in each group):")
    for name in ("ETF 短周期 周调", "ETF 21/63/252 周调", "ETF 一直持有"):
        y = weekly(books[name].dropna()); j = pd.concat([y.rename("y"), G], axis=1).dropna()
        coef = ols(j.y, j[list(codes)]); fit = coef[0] + j[list(codes)].to_numpy() @ coef[1:]
        r2 = 1 - ((j.y - fit) ** 2).sum() / ((j.y - j.y.mean()) ** 2).sum()
        print(f"  {name}: alpha {coef[0]*52*100:+.1f}%/y, " + ", ".join(f"{g} {b:.2f}" for g, b in zip(codes, coef[1:])) + f", R² {r2:.2f}")


if __name__ == "__main__":
    main()
