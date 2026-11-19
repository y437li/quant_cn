"""Variants of the 1-month cross-sectional reversal (截面反转) vs the existing reversal_1m.
Over the last 21 sessions: overnight-only (close->open), intraday-only (open->close), and a turnover split
(sum of returns on the 10 highest-turnover days vs the 11 lowest). Month-end signal, universe = derived/universe,
entry open(t+1), exit close(t+H). Rank IC raw and net of reversal_1m + size + turnover_60d."""
import duckdb, numpy as np, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
OUT = LAKE / "meta/runs/research/20261114_reversal_variants"; OUT.mkdir(parents=True, exist_ok=True)
r = lambda t: f"read_parquet('{LAKE}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
con = duckdb.connect(); W = 21
px = con.sql(f"""select d.ts_code, d.trade_date, d.open*a.adj_factor o, d.close*a.adj_factor c, b.turnover_rate_f tv, b.circ_mv
  from {r('curated/daily')} d join {r('curated/adj_factor')} a using (ts_code, trade_date)
  left join {r('curated/daily_basic')} b using (ts_code, trade_date) where d.trade_date >= '20181001'""").df()
P = lambda v: px.pivot(index="trade_date", columns="ts_code", values=v).sort_index()
O, C, TV, CM = P("o"), P("c"), P("tv"), P("circ_mv"); idx, cols = C.index, C.columns
on = np.log(O / C.shift(1)); intra = np.log(C / O); tot = np.log(C / C.shift(1))
rk = TV.rolling(W, min_periods=W).rank()      # rank of today's turnover within its own 21-day window
# turnover split needs per-window ranks; approximate with the rank of each day's turnover within the window ending at d,
# computed only at month-ends below
uni = con.sql(f"select trade_date, ts_code, in_universe from {r('derived/universe')} where trade_date >= '20190101'").df()
U = uni.pivot(index="trade_date", columns="ts_code", values="in_universe").reindex(index=idx, columns=cols).fillna(0).astype(bool)
ex = con.sql(f"""select trade_date, ts_code, factor, value from {r('derived/features')} where factor in ('reversal_1m','turnover_60d')""").df()
EX = {f: g.pivot(index="trade_date", columns="ts_code", values="value").reindex(index=idx, columns=cols) for f, g in ex.groupby("factor")}
EX["size"] = np.log(CM)
months = [d for d in pd.Series(idx, index=idx).groupby(idx.str[:6]).last() if "20190201" <= d <= "20260930"]
HS = (5, 20, 60)
FWD = {h: C.shift(-h) / O.shift(-1) - 1 for h in HS}
rows = []
for d in months:
    i = idx.get_loc(d); win = idx[i - W + 1: i + 1]
    t = TV.loc[win]; rr = tot.loc[win]
    hi = t.rank(axis=0, ascending=False) <= 10
    f = pd.DataFrame({
        "rev_total": -rr.sum(), "rev_overnight": -on.loc[win].sum(), "rev_intraday": -intra.loc[win].sum(),
        "rev_high_turnover_days": -rr.where(hi).sum(), "rev_low_turnover_days": -rr.where(~hi).sum(),
        **{f"y{h}": FWD[h].loc[d] for h in HS}, **{k: v.loc[d] for k, v in EX.items()}})
    f = f[U.loc[d] & f.y5.notna() & (t.notna().sum() >= 18)]
    f["d"] = d; rows.append(f)
E = pd.concat(rows)
SIG = ["rev_total", "rev_overnight", "rev_intraday", "rev_high_turnover_days", "rev_low_turnover_days", "reversal_1m"]

def ic(g, x, y, ctrl):
    g = g.dropna(subset=[x, y] + ctrl); v = g[x].rank()
    if ctrl:
        Z = g[ctrl].rank(); Z = (Z - Z.mean()) / Z.std(); Z["c"] = 1.0
        v = v - Z.values @ np.linalg.lstsq(Z.values, v.values, rcond=None)[0]
    return pd.Series(v.values).corr(g[y].rank().reset_index(drop=True))

out = []
for x in SIG:
    for ctrl_name, ctrl in (("raw", []), ("net of reversal_1m+size+turnover", ["reversal_1m", "size", "turnover_60d"])):
        if x == "reversal_1m" and ctrl: ctrl = ["size", "turnover_60d"]; ctrl_name = "net of size+turnover"
        for h in HS:
            s = E.groupby("d").apply(lambda g: ic(g, x, f"y{h}", ctrl), include_groups=False).dropna()
            n_eff = len(s) * min(1, 20 / h)
            out.append({"signal": x, "controls": ctrl_name, "H": h, "IC": s.mean(), "t": s.mean() / s.std() * np.sqrt(n_eff),
                        "2019-22": s[s.index < "20230101"].mean(), "2023-26": s[s.index >= "20230101"].mean()})
R = pd.DataFrame(out); R.to_csv(OUT / "reversal_variants_ic.csv", index=False)
pd.set_option("display.width", 220)
print(f"months {E.d.nunique()}, stocks/month {len(E)/E.d.nunique():.0f}")
print(R.pivot_table(index=["signal", "controls"], columns="H", values=["IC", "t"], sort=False).round(3).to_string())
print("\n20-day IC by sub-period"); print(R[R.H == 20].set_index(["signal", "controls"])[["2019-22", "2023-26"]].round(3).to_string())
c = E[SIG].rank(pct=True).groupby(E.d).corr().groupby(level=1).mean().loc[SIG, SIG]
print("\nmean cross-sectional rank corr"); print(c.round(2).to_string())

# --- follow-up: are intraday and high-turnover reversal the same signal? and their combination
rows = []
for d in months:
    i = idx.get_loc(d); win = idx[i - W + 1: i + 1]
    hi = TV.loc[win].rank(axis=0, ascending=False) <= 10
    rows.append(pd.Series(-intra.loc[win].where(hi).sum(), name=d))
E = E.join(pd.concat(rows, axis=1).T.stack().rename("rev_intraday_high_tv"), on=["d", E.index.name or "ts_code"]) if False else E
combo = pd.concat(rows, axis=1).T.stack().rename("rev_intraday_high_tv").reset_index()
combo.columns = ["d", "ts_code", "rev_intraday_high_tv"]
E2 = E.reset_index().rename(columns={"index": "ts_code"}).merge(combo, on=["d", "ts_code"], how="left").set_index("ts_code")
E2["rev_intra_plus_hitv"] = E2.groupby("d").rev_intraday.rank(pct=True) + E2.groupby("d").rev_high_turnover_days.rank(pct=True)
base = ["reversal_1m", "size", "turnover_60d"]
tests = [("rev_intraday", base + ["rev_high_turnover_days"]), ("rev_high_turnover_days", base + ["rev_intraday"]),
         ("rev_intraday_high_tv", []), ("rev_intraday_high_tv", base), ("rev_intra_plus_hitv", []), ("rev_intra_plus_hitv", base),
         ("rev_intra_plus_hitv", ["size", "turnover_60d"])]
out = []
for x, ctrl in tests:
    for h in (20, 60):
        s = E2.groupby("d").apply(lambda g: ic(g, x, f"y{h}", ctrl), include_groups=False).dropna()
        n_eff = len(s) * min(1, 20 / h)
        out.append({"signal": x, "controls": "+".join(ctrl) or "raw", "H": h, "IC": round(s.mean(), 4), "t": round(s.mean() / s.std() * np.sqrt(n_eff), 2)})
print("\nfollow-up"); print(pd.DataFrame(out).pivot_table(index=["signal", "controls"], columns="H", values=["IC", "t"], sort=False).to_string())
# decile spread of the combination vs reversal_1m, 20-day, before costs
for x in ("reversal_1m", "rev_intra_plus_hitv"):
    e = E2.dropna(subset=[x, "y20"]).copy(); e["dec"] = e.groupby("d")[x].transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
    m = e.groupby(["d", "dec"]).y20.mean().unstack(); sp = m[9] - m[0]
    print(f"{x}: D10-D1 20-day {sp.mean()*100:.2f}%/month t {sp.mean()/sp.std()*np.sqrt(len(sp)):.2f}, win {int((sp>0).sum())}/{len(sp)}, worst {sp.min()*100:.1f}%")
