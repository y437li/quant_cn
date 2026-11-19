"""Does a financing balance that stops falling after a deleveraging mark a small-cap bottom?
Event: total 融资余额 at least DD below its 250-session high, and its N-day change turns >= 0
(first day; 20-session cooldown). Outcome: 中证1000 / 沪深300 forward 20 / 60 session returns."""
import duckdb
import pandas as pd

# read the curated parquet directly (read-only): the catalog is locked by a running update-all
LAKE = "/Volumes/Treasury/quant_cn_lake/curated"
con = duckdb.connect()
# market financing balance = sum of per-stock rzye (margin_detail, 2019+); drop thin days (holidays / gaps)
m = con.sql(f"""select trade_date d, sum(rzye)/1e8 rz, count(*) n
  from read_parquet('{LAKE}/margin_detail/*/*.parquet') group by 1 order by 1""").df()
m = m[m["n"] >= 0.9 * m["n"].rolling(20, min_periods=1).median()]
px = con.sql(f"""select trade_date d, ts_code, close from read_parquet('{LAKE}/reference/index_daily.parquet')
  where ts_code in ('000852.SH','000300.SH') order by 1""").df().pivot(index="d", columns="ts_code", values="close")
df = m.set_index("d")[["rz"]].join(px, how="inner").dropna()
for h in (20, 60):
    for c in ("000852.SH", "000300.SH"):
        df[f"{c[:6]}_f{h}"] = df[c].shift(-h) / df[c] - 1
df["dd"] = df["rz"] / df["rz"].rolling(250, min_periods=120).max() - 1
print("history", df.index[0], df.index[-1], len(df))
base = df[[c for c in df if "_f" in c]].mean()
print("unconditional", (base * 100).round(1).to_dict())
rows = []
for n in (5, 10, 20):
    chg = df["rz"] / df["rz"].shift(n) - 1
    for dd in (-0.05, -0.10, -0.15):
        cond = (df["dd"] <= dd) & (chg >= 0) & (chg.shift(1) < 0)
        ev, last = [], None
        for d in df.index[cond]:
            i = df.index.get_loc(d)
            if last is None or i - last >= 20:
                ev.append(d); last = i
        e = df.loc[ev]
        r = {"n": n, "dd": dd, "events": len(e)}
        for c in ("000852_f20", "000852_f60", "000300_f60"):
            v = e[c].dropna()
            r[c] = round(v.mean() * 100, 1) if len(v) else None
            r[c + "_hit"] = round((v > 0).mean(), 2) if len(v) else None
        rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))
# current state
chg10 = df["rz"].iloc[-1] / df["rz"].iloc[-11] - 1
print("now", df.index[-1], "rz", round(df["rz"].iloc[-1]), "dd", round(df["dd"].iloc[-1] * 100, 1), "chg10", round(chg10 * 100, 2))

# event list for the chosen rule (5-day change turns >= 0 with the balance >= 10% below its 250-day high)
chg5 = df["rz"] / df["rz"].shift(5) - 1
cond = (df["dd"] <= -0.10) & (chg5 >= 0) & (chg5.shift(1) < 0)
ev, last = [], None
for d in df.index[cond]:
    i = df.index.get_loc(d)
    if last is None or i - last >= 20:
        ev.append(d); last = i
print((df.loc[ev, ["rz", "dd", "000852_f20", "000852_f60"]] * [1, 100, 100, 100]).round(1).to_string())
print("max drawdown in history", round(df["dd"].min() * 100, 1), df["dd"].idxmin())
