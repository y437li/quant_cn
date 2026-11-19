"""Absolute margin level: financing balance (Σ margin_detail rzye + rqye) vs float market cap and
vs turnover, with percentiles since 2019 (parquet read-only; the catalog is locked by update-all)."""
import duckdb

LAKE = "/Volumes/Treasury/quant_cn_lake/curated"
con = duckdb.connect()
df = con.sql(f"""
with m as (select trade_date d, sum(rzye)/1e8 rz, sum(rqye)/1e8 rq, sum(rzmre)/1e8 rzbuy, count(*) n
           from read_parquet('{LAKE}/margin_detail/*/*.parquet') group by 1),
b as (select trade_date d, sum(circ_mv)/1e4 circ, sum(total_mv)/1e4 tot
      from read_parquet('{LAKE}/daily_basic/*/*.parquet') group by 1),
t as (select trade_date d, sum(amount)/1e5 amt from read_parquet('{LAKE}/daily/*/*.parquet')
      where trade_date >= '20190101' group by 1)
select * from m join b using(d) join t using(d) where d >= '20190101' order by d
""").df().set_index("d")
df = df[df["n"] >= 0.9 * df["n"].rolling(20, min_periods=1).median()]
df["rz_circ"] = df["rz"] / df["circ"] * 100        # % of float market cap
df["rzbuy_amt"] = df["rzbuy"] / df["amt"] * 100     # financing buys as % of turnover
df["rz_days"] = df["rz"] / df["amt"].rolling(20).mean()  # balance in days of turnover
cols = ["rz", "rq", "circ", "amt", "rz_circ", "rzbuy_amt", "rz_days"]
now = df.iloc[-1]
print("as of", df.index[-1])
for c in cols:
    s = df[c].dropna()
    print(f"{c:10s} now {now[c]:10.2f}  pct {(s <= now[c]).mean():.2f}  min {s.min():10.2f} ({s.idxmin()})  max {s.max():10.2f} ({s.idxmax()})  median {s.median():10.2f}")
for d in ("20190104", "20210217", "20240205", "20240923", "20250102", "20250408", "20260807", "20260930"):
    r = df.loc[df.index[df.index >= d][0]]
    print(d, {c: round(r[c], 2) for c in ("rz", "rz_circ", "rzbuy_amt", "rz_days")})
