"""What if bond prices fall? (2026-11-14). User: "如果债券价格开始下降呢？".

Bond group proxy from the 中债国债 curve (cn_bond_yield, 2010-): daily return ≈ y/252 − D·Δy + ½·C·Δy² for the four ETFs
(5y D 4.5; 10y D 8.5; 5-10y D 6.5 from y_7y; 30y D 19 C 450), equal weight = the book's 债券 group.
Checks: the proxy against the real ETF group 2020-2026; bond bear episodes (2013, 2016-17, 2020); bond group hold vs
trend switch (21/63/252) and vol response (60-day vol → risk-budget weight share if other groups keep their 2020-26 vol);
book loss if a 2016-17 move came now at today's 80% bond weight.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import duckdb, numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
spec = importlib.util.spec_from_file_location("sy", HERE / "systematic.py")
sy = importlib.util.module_from_spec(spec); spec.loader.exec_module(sy)
c = duckdb.connect()
Y = c.execute(f"select trade_date, avg(y_5y) y5, avg(y_7y) y7, avg(y_10y) y10, avg(y_30y) y30 from read_parquet('{LAKE}/curated/macro/cn_bond_yield.parquet') "
              "where curve_name = '中债国债收益率曲线' group by 1 order by 1").df()
Y["trade_date"] = pd.to_datetime(Y.trade_date); Y = Y.set_index("trade_date") / 100
leg = lambda y, D, C=0.0: y.shift(1) / 252 - D * y.diff() + 0.5 * C * y.diff() ** 2
B = pd.concat([leg(Y.y5, 4.5, 25), leg(Y.y10, 8.5, 90), leg(Y.y7, 6.5, 50), leg(Y.y30, 19, 450)], axis=1).mean(axis=1).dropna()
R, cash = sy.load()
real = R[list(sy.GROUPS["债券"])].mean(axis=1).loc["2020-02":]
j = pd.concat([B.rename("proxy"), real.rename("real")], axis=1).dropna()
print(f"proxy vs real ETF group 2020-02..: corr {j.proxy.corr(j.real):.2f}, ann {((1+j.proxy).prod())**(252/len(j))-1:+.1%} vs {((1+j.real).prod())**(252/len(j))-1:+.1%}, "
      f"vol {j.proxy.std()*252**.5:.1%} vs {j.real.std()*252**.5:.1%}")
cum = (1 + B).cumprod(); dd = cum / cum.cummax() - 1
print("\nbond bear episodes (proxy, peak → trough):")
for a, b in (("2013-01-01", "2014-03-31"), ("2016-08-01", "2017-12-31"), ("2020-04-01", "2020-12-31"), ("2022-10-01", "2023-01-31"), ("2025-01-01", "2026-11-13")):
    x = cum.loc[a:b]; t = (x / x.cummax() - 1).idxmin(); p = x.loc[:t].idxmax()
    print(f"  {a[:7]}..{b[:7]}: {x.loc[t]/x.loc[p]-1:+.1%} ({p.date()} → {t.date()}), 10y {Y.y10.loc[p]*100:.2f}% → {Y.y10.loc[t]*100:.2f}%, "
          f"60d vol at trough {B.loc[:t].iloc[-60:].std()*252**.5:.1%}")
nav = cum; sig = (sum((nav > nav.shift(n)).astype(float) for n in (21, 63, 252)) / 3)
fri = sig.index.dayofweek == 4; sig = sig.where(fri).ffill().shift(1).fillna(0)
cash_y = (Y.y5 * 0 + 0.02 / 252)  # 2% cash proxy before 2019
tsw = sig * B + (1 - sig) * cash_y.reindex(B.index).ffill() - 0.0015 * sig.diff().abs().fillna(0)
for nm, x in (("hold", B), ("trend switch", tsw)):
    for a, b in (("2011", "2026"), ("2013", "2014-03"), ("2016-08", "2017-12"), ("2020-04", "2020-12")):
        z = x.loc[a:b]; cz = (1 + z).cumprod()
        print(f"  {nm:12s} {a}..{b}: total {cz.iloc[-1]-1:+.1%}, max dd {(cz/cz.cummax()-1).min():+.1%}")
# weight response: other groups' vol at their 2020-26 averages (股票 22%, 黄金 18%, 商品 19%)
v = B.rolling(60).std() * 252 ** 0.5
inv_other = 1 / 0.22 + 1 / 0.18 + 1 / 0.19
wb = (1 / v) / ((1 / v) + inv_other)
for d in ("2016-10-31", "2016-12-30", "2017-03-31", "2017-06-30", "2020-05-29", "2020-08-31", "2026-11-13"):
    print(f"  {d}: bond 60d vol {v.loc[:d].iloc[-1]:.1%} → risk-budget bond weight {wb.loc[:d].iloc[-1]:.0%}")
# replay 2016-08..2017-12 bond path on today's book: bond weight from vol each month, others flat at their weights scaled
x = B.loc["2016-08-01":"2017-12-31"]; w0 = 0.80
print(f"\nreplay of 2016-17 bond losses on today's book: fixed 80% bonds → book {(w0*((1+x).prod()-1)):+.1%} from bonds over the period; "
      f"worst bond dd {((1+x).cumprod()/(1+x).cumprod().cummax()-1).min():+.1%} → book ≈ {w0*((1+x).cumprod()/(1+x).cumprod().cummax()-1).min():+.1%}")
