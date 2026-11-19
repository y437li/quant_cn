"""融资余额 drawdown episodes (month-end, since 2014) and the smoothed pace of the current one.

Episodes: in each named window, the month-end high and the lowest month-end after it (a mechanical
rule split 2015 at the +32% Oct rebound and merged 2022 with 2024, so the windows are by hand). Month-ends from 20261119_margin_share_long.csv (Tushare margin,
exchange totals). Pace on the lake's curated.margin (SSE + SZSE + BSE, full days only): speed =
10-day EMA of the daily change (亿 / day), acceleration = its 5-day change / 5. Writes
20261119_margin_drawdown.csv (the episodes) to the lake's meta/runs/research.
"""
import duckdb
import pandas as pd

R = "/Volumes/Treasury/quant_cn_lake/meta/runs/research/"
m = pd.read_csv(R + "20261119_margin_share_long.csv", dtype={"date": str})
rz = m.set_index(m.date.str[:6])["rz"]
rz = rz[rz.index >= "201401"]
WINDOWS = [("2015 股灾", "201401", "201612"), ("2018 熊市", "201712", "201906"),
           ("2022", "202109", "202212"), ("2024", "202309", "202409"), ("2026", "202601", "202612")]
out = []
for name, a, b in WINDOWS:
    w = rz[(rz.index >= a) & (rz.index <= b)]
    hi_d = w.idxmax()
    after = w[w.index >= hi_d]
    lo_d = after.idxmin()
    out.append((name, hi_d, w[hi_d], lo_d, after[lo_d]))
ep = pd.DataFrame(out, columns=["episode", "high_month", "high", "low_month", "low"])
ep["depth"] = ep.low / ep.high - 1
ep["months"] = [(int(b[:4]) - int(a[:4])) * 12 + int(b[4:]) - int(a[4:])
                for a, b in zip(ep.high_month, ep.low_month, strict=True)]
ep.to_csv(R + "20261119_margin_drawdown.csv", index=False)
print((ep.assign(high=ep.high / 1e4, low=ep.low / 1e4)).round(3).to_string())

day = duckdb.sql("""SELECT trade_date, sum(rzye) / 1e8 AS rz, count(DISTINCT exchange_id) AS n
FROM read_parquet('/Volumes/Treasury/quant_cn_lake/curated/margin/**/*.parquet')
GROUP BY 1 ORDER BY 1""").df().set_index("trade_date")
s = day.loc[day.n == day.n.max(), "rz"]
speed = s.diff().ewm(span=10).mean()
acc = speed.diff(5) / 5
pace = pd.DataFrame({"rz": s, "speed": speed, "acc": acc, "dd": s / s.cummax() - 1}).round(2)
print(pace.tail(10).to_string())
print("fastest fall since 2026-06:", speed.loc["20260601":].idxmin(), round(speed.min(), 1))
