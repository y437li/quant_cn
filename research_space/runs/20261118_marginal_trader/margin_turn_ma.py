"""Follow-up to margin_turn_bt.py: mean vs median of the 5-day rule, and a moving-average version
(balance crosses above its N-day average after a >= 10% drawdown from its 250-day high)."""
import duckdb
import pandas as pd

LAKE = "/Volumes/Treasury/quant_cn_lake/curated"  # parquet read-only; the catalog is locked by update-all
con = duckdb.connect()
m = con.sql(f"""select trade_date d, sum(rzye)/1e8 rz, count(*) n
  from read_parquet('{LAKE}/margin_detail/*/*.parquet') group by 1 order by 1""").df()
m = m[m["n"] >= 0.9 * m["n"].rolling(20, min_periods=1).median()]
px = con.sql(f"""select trade_date d, close from read_parquet('{LAKE}/reference/index_daily.parquet')
  where ts_code = '000852.SH' order by 1""").df().set_index("d")
df = m.set_index("d")[["rz"]].join(px, how="inner").dropna()
for h in (20, 60):
    df[f"f{h}"] = df["close"].shift(-h) / df["close"] - 1
df["dd"] = df["rz"] / df["rz"].rolling(250, min_periods=120).max() - 1


def pick(cond: pd.Series) -> list[str]:
    ev, last = [], None
    for d in df.index[cond]:
        i = df.index.get_loc(d)
        if last is None or i - last >= 20:
            ev.append(d)
            last = i
    return ev


def stats(name: str, ev: list[str]) -> dict:
    e = df.loc[ev]
    r = {"rule": name, "events": len(e)}
    for h in ("f20", "f60"):
        v = e[h].dropna()
        r[f"{h}_mean"] = round(v.mean() * 100, 1)
        r[f"{h}_median"] = round(v.median() * 100, 1)
        r[f"{h}_hit"] = round((v > 0).mean(), 2)
    r["2026"] = ",".join(d for d in ev if d >= "20260101")
    return r


deep = df["dd"] <= -0.10
chg5 = df["rz"] / df["rz"].shift(5) - 1
rows = [stats("5d change turns >= 0", pick(deep & (chg5 >= 0) & (chg5.shift(1) < 0)))]
for n in (10, 20, 60):
    ma = df["rz"].rolling(n).mean()
    above = df["rz"] > ma
    rows.append(stats(f"crosses above MA{n}", pick(deep & above & ~above.shift(1, fill_value=True))))
base = {"rule": "any day", "events": len(df)}
for h in ("f20", "f60"):
    v = df[h].dropna()
    base.update({f"{h}_mean": round(v.mean() * 100, 1), f"{h}_median": round(v.median() * 100, 1), f"{h}_hit": round((v > 0).mean(), 2)})
rows.append(base)
pd.set_option("display.width", 220)
print(pd.DataFrame(rows).to_string(index=False))
last = df.iloc[-1]
print("now", df.index[-1], {f"MA{n}": round(df["rz"].rolling(n).mean().iloc[-1]) for n in (10, 20, 60)}, "rz", round(last["rz"]))
