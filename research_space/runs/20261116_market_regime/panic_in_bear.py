"""Panic-day buys inside the 2021-12..2024-02 bear market and the 2025-04 tariff crash: peak within 250 sessions, 250-day return,
and whether the entry was undercut after the peak. 中证1000 from the index cache extended with 512100. Calendar-year returns too."""
import pandas as pd, duckdb
b = pd.read_csv("/Volumes/Treasury/chinese_market/src/regime/cache/000852_SH_5min.csv", usecols=["trade_time", "close", "trade_date"])
c = b[b.trade_time.str[11:16] == "15:00"].set_index("trade_date").close; c.index = c.index.astype(str).str.replace("-", "")
e = duckdb.sql(f"select trade_date, pct_chg from read_parquet('/Volumes/Treasury/quant_cn_lake/curated/fund_daily/**/*.parquet', hive_partitioning=true) where ts_code='512100.SH' and trade_date>'{c.index[-1]}'").df().set_index("trade_date").pct_chg.sort_index() / 100
p = pd.concat([c, c.iloc[-1] * (1 + e).cumprod()])
y = p.groupby(p.index.str[:4]).agg(["first", "last"]); print("calendar-year %:", ((y["last"] / y["first"] - 1) * 100).round(1).to_dict())
s = p[(p.index >= "20210101") & (p.index <= "20221231")]; lo = p[(p.index >= "20240101") & (p.index <= "20241231")]
print("2021-22 high", s.idxmax(), round(s.max()), "| 2024 low", lo.idxmin(), round(lo.min()), "| drop %.1f%%" % ((lo.min() / s.max() - 1) * 100))
for d in ["20220425", "20240205", "20240416", "20250407"]:
    i = p.index.get_loc(d); w = p.iloc[i:i + 251]; pk = w.idxmax()
    print(d, round(p[d]), "peak +%.1f%% on %s" % ((w.max() / w.iloc[0] - 1) * 100, pk), "| 250d %+.1f%%" % ((w.iloc[-1] / w.iloc[0] - 1) * 100) if len(w) == 251 else "",
          "| lowest after peak %+.1f%% vs entry" % ((w.loc[pk:].min() / w.iloc[0] - 1) * 100), "| first close below entry later:", next((k for k, v in p.iloc[i + 1:].items() if v < p[d]), None))
t = p[(p.index >= "20250320") & (p.index <= "20250630")]; print("2025 tariff path:", {k: round(v) for k, v in t.iloc[::5].items()})
i = p.index.get_loc("20250407"); print("04-07 close", round(p.iloc[i]), "prev", round(p.iloc[i - 1]), "| back above the 04-02 close on", next((k for k, v in p.iloc[i:].items() if v >= p.loc["20250402"]), None))
