"""Parameter sensitivity and costs for the 2026-11-14 TSMOM / spread results, plus TSMOM on
indices, index and bond futures, SW industries and ETFs (2026-11-14).

Costs (assumptions, one side, on notional traded): commodity and financial futures 5 bp incl.
slippage, plus one roll a month on the held position (2 x 5 bp x |w|, an upper bound); ETFs 5 bp;
spread legs 5 bp each. No stamp duty on futures or ETFs.
"""
from __future__ import annotations
import contextlib, importlib.util, io, itertools, warnings
from pathlib import Path
import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_tsmom_robust"
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mr", HERE.parent / "20261114_mean_reversion/mean_reversion.py")
with contextlib.redirect_stdout(io.StringIO()):
    mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
COST, ROLL = 0.0005, 0.0010
sr = lambda p: p.mean() / p.std() * 12 ** 0.5 if len(p) > 12 and p.std() > 0 else np.nan
tst = lambda p: p.mean() / p.std() * len(p) ** 0.5 if len(p) > 12 and p.std() > 0 else np.nan
c = duckdb.connect()


def monthly(R: pd.DataFrame, end: str = "2026-11-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    M = (1 + R.fillna(0)).resample("ME").prod() - 1
    M = M.where(R.resample("ME").count() > 10)
    return M[M.index < end], R


def tsmom(R: pd.DataFrame, L: int, com: int = 60, cap: float | None = 3.0, long_flat: bool = False,
          roll: bool = True, cost: float = COST, start: str = "2020-01-01", always: bool = False,
          roll_cost: float = ROLL) -> dict[str, pd.Series]:
    """Equal-weight book of vol-scaled sign(past L months) positions; gross, net and turnover."""
    M, _ = monthly(R)
    V = ((R.pow(2).ewm(com=com, min_periods=60).mean() * 252) ** 0.5).resample("ME").last().reindex(M.index)
    past = ((1 + M.fillna(0)).rolling(L).apply(np.prod, raw=True) - 1).where(M.notna().rolling(L).sum() == L)
    sig = np.sign(past).clip(lower=0) if long_flat else np.sign(past)
    if always:  # benchmark: always long, same vol scaling
        sig = past.notna().astype(float).where(past.notna())
    w = sig * (0.40 / V)
    if cap is not None:
        w = w.clip(-cap, cap)
    w = w.shift(1)
    live = w.notna() & M.notna()
    n = live.sum(axis=1).replace(0, np.nan)
    gross = (w * M).where(live).sum(axis=1) / n
    turn = (w.fillna(0).diff().abs()).where(live).sum(axis=1) / n
    hold = w.abs().where(live).sum(axis=1) / n
    net = gross - cost * turn - (roll_cost * hold if roll else 0)
    keep = gross.index >= start
    return {"gross": gross[keep].dropna(), "net": net[keep].dropna(), "turn": turn[keep]}


def row(label: str, b: dict[str, pd.Series]) -> dict:
    g, n = b["gross"], b["net"]
    late = g.index >= "2023-01-01"
    return {"case": label, "sharpe": sr(g), "t": tst(g), "sharpe_net": sr(n), "t_net": tst(n),
            "sharpe_2023": sr(g[late]), "sharpe_net_2023": sr(n[late]), "turnover": b["turn"].mean()}


def show(title: str, rows: list[dict], file: str) -> pd.DataFrame:
    T = pd.DataFrame(rows).set_index("case"); T.to_csv(OUT / file)
    print(f"\n{title}"); print(T.round(2).to_string()); return T


# ---------- A1 commodity TSMOM grid
R = mr.d.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
rows = [row(f"L{L} com{com} cap{cap}", tsmom(R, L, com, cap))
        for L, com, cap in itertools.product((1, 3, 6, 9, 12), (30, 60, 120), (3.0, None))]
A1 = show("A1 commodity TSMOM, 73 families, 2020-01..2026-10 (net: 5 bp trades + monthly roll)", rows, "a1_commodity_grid.csv")
print("  share of 30 cases with gross Sharpe > 0:", f"{(A1.sharpe > 0).mean():.0%}", "| net > 0:", f"{(A1.sharpe_net > 0).mean():.0%}",
      "| median gross / net:", round(A1.sharpe.median(), 2), "/", round(A1.sharpe_net.median(), 2))

# ---------- A2 spread reversion grid
rows = []
for sp in mr.spreads:
    cols = [l["family"] for l in sp["legs"]]
    if any(x not in mr.S.columns for x in cols) or sp.get("kind") == "ratio":
        continue
    L = mr.S[cols].dropna()
    s = sum(l["coef"] * L[l["family"]] for l in sp["legs"])
    notional = sum(abs(l["coef"]) * L[l["family"]] for l in sp["legs"])
    ds = s.diff()
    for win, cap, thr in itertools.product((125, 250, 500), (1.0, 2.0, 3.0), (0.0, 1.0)):
        z = (s - s.rolling(win).mean()) / s.rolling(win).std()
        pos = -z.clip(-cap, cap).where(z.abs() >= thr, 0.0)
        scale = ds.rolling(250).std().shift(1)
        pos = (pos / scale).shift(1)                       # units of spread per unit risk
        gross = pos * ds
        cost = pos.diff().abs() * notional * COST
        g, n = gross.dropna(), (gross - cost).dropna()
        late = g.index >= "2023-01-01"
        ann = lambda x: x.mean() / x.std() * 252 ** 0.5 if x.std() > 0 else np.nan
        rows.append({"spread": sp["name"], "window": win, "cap": cap, "entry": thr,
                     "sharpe": ann(g), "sharpe_net": ann(n), "sharpe_2023": ann(g[g.index >= "2023-01-01"]), "sharpe_net_2023": ann(n[n.index >= "2023-01-01"])})
A2 = pd.DataFrame(rows); A2.to_csv(OUT / "a2_spread_grid.csv", index=False)
print("\nA2 spread z-reversion, 18 cases per spread (window 125/250/500 x cap 1/2/3 x entry 0/1): median Sharpe [min..max]")
for name, g in A2.groupby("spread", sort=False):
    f = lambda col: f"{g[col].median():+.2f} [{g[col].min():+.2f}..{g[col].max():+.2f}]"
    print(f"  {name:16s} gross {f('sharpe')}  net {f('sharpe_net')}  net 2023+ {f('sharpe_net_2023')}")

# ---------- B1 indices since 2010 and B2 SW L1 industries since 2019
I = c.execute(f"select ts_code, trade_date, close from read_parquet('{LAKE}/curated/reference/index_daily.parquet')").df()
I["trade_date"] = pd.to_datetime(I.trade_date)
P = I.pivot(index="trade_date", columns="ts_code", values="close").sort_index()
RI = P.pct_change(fill_method=None)
names = {"000001.SH": "上证指数", "399001.SZ": "深证成指", "000016.SH": "上证50", "000300.SH": "沪深300",
         "000905.SH": "中证500", "000852.SH": "中证1000", "399006.SZ": "创业板指"}
rows = []
for L in (1, 3, 6, 12):
    for mode in ("long-short", "long-flat"):
        rows.append(row(f"7 indices L{L} {mode}", tsmom(RI, L, long_flat=mode == "long-flat", roll=False, start="2011-01-01")))
rows.append(row("7 indices always long (vol-scaled)", tsmom(RI, 12, always=True, roll=False, start="2011-01-01")))
bh = (RI.resample("ME").apply(lambda x: (1 + x).prod() - 1)).mean(axis=1)
bh = bh[(bh.index >= "2011-01-01") & (bh.index < "2026-11-01")]
show(f"B1 A-share indices 2011-01..2026-10 (price index, no futures roll; buy-and-hold equal-weight Sharpe {sr(bh):.2f})", rows, "b1_indices.csv")
per = []
for code in RI.columns:
    for L in (1, 3, 12):
        b = tsmom(RI[[code]], L, long_flat=True, roll=False, start="2011-01-01")
        m1 = (1 + RI[code].fillna(0)).resample("ME").prod() - 1
        m1 = m1[(m1.index >= "2011-01-01") & (m1.index < "2026-11-01")]
        per.append({"index": names[code], "L": L, "long_flat_net": sr(b["net"]), "buy_hold": sr(m1)})
print(pd.DataFrame(per).pivot(index="index", columns="L", values="long_flat_net").round(2).assign(
    buy_hold=pd.DataFrame(per).groupby("index").buy_hold.first().round(2)).to_string())

sw = c.execute(f"""select ts_code, trade_date, close from read_parquet('{LAKE}/curated/sw_daily/**/*.parquet')
  where ts_code in (select index_code from read_parquet('{LAKE}/curated/reference/index_classify.parquet') where level='L1')""").df()
if not sw.empty:
    sw["trade_date"] = pd.to_datetime(sw.trade_date)
    RS = sw.pivot(index="trade_date", columns="ts_code", values="close").sort_index().pct_change(fill_method=None)
    rows = [row(f"{RS.shape[1]} SW L1 L{L} {m}", tsmom(RS, L, long_flat=m == "long-flat", roll=False))
            for L in (1, 3, 12) for m in ("long-short", "long-flat")]
    show("B2 SW L1 industries 2020-01..2026-10 (as a basket; long-short not tradable as such)", rows, "b2_sw_l1.csv")

# ---------- B3 index and bond futures since 2019
F = c.execute(f"""select m.ts_code fam, m.trade_date, d.close/d.pre_close-1 ret
 from read_parquet('{LAKE}/curated/fut_mapping/**/*.parquet') m
 join read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') d on d.ts_code=m.mapping_ts_code and d.trade_date=m.trade_date
 where m.ts_code in ('IF.CFX','IH.CFX','IC.CFX','IM.CFX','T.CFX','TF.CFX','TS.CFX','TL.CFX') and d.pre_close>0""").df()
F["trade_date"] = pd.to_datetime(F.trade_date)
RF = F.pivot_table(index="trade_date", columns="fam", values="ret").sort_index().clip(-0.2, 0.2)
rows = []
for L in (1, 3, 12):
    rows.append(row(f"index fut L{L} (2 bp, roll 4 bp/month)", tsmom(RF[["IF.CFX", "IH.CFX", "IC.CFX", "IM.CFX"]], L, cost=0.0002, roll_cost=0.0004)))
    rows.append(row(f"bond fut L{L} (1 bp, roll 2 bp/quarter)", tsmom(RF[["T.CFX", "TF.CFX", "TS.CFX", "TL.CFX"]], L, cost=0.0001, roll_cost=0.0002 / 3)))
    pass
rows.append(row("bond fut always long (vol-scaled)", tsmom(RF[["T.CFX", "TF.CFX", "TS.CFX", "TL.CFX"]], 12, always=True, cost=0.0001, roll_cost=0.0002 / 3)))
rows.append(row("index fut always long (vol-scaled)", tsmom(RF[["IF.CFX", "IH.CFX", "IC.CFX", "IM.CFX"]], 12, always=True, cost=0.0002, roll_cost=0.0004)))
show("B3 CFFEX futures 2020-01..2026-10 (stock index IF/IH/IC/IM, bond T/TF/TS/TL)", rows, "b3_cffex.csv")

# ---------- B4 ETFs since 2019
E = c.execute(f"""
with b as (select ts_code, name from read_parquet('{LAKE}/curated/reference/fund_basic.parquet')
           where market='E' and list_date < '20200101' and (delist_date is null or delist_date > '20261101')),
d as (select f.ts_code, f.trade_date, f.close/f.pre_close-1 ret, f.amount
      from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet') f join b using (ts_code) where f.pre_close>0),
liq as (select ts_code from d where trade_date >= '20230101' group by 1 having avg(amount) > 50000)  -- > 5千万/日 (千元)
select d.ts_code, b.name, d.trade_date, d.ret from d join liq using (ts_code) join b using (ts_code)
where b.name not like '%货币%' and b.name not like '%快线%' and b.name not like '%短融%'""").df()
E["trade_date"] = pd.to_datetime(E.trade_date)
RE = E.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
enames = E.drop_duplicates("ts_code").set_index("ts_code").name
rows = []
for L in (1, 3, 12):
    for m in ("long-short", "long-flat"):
        rows.append(row(f"{RE.shape[1]} ETFs L{L} {m}", tsmom(RE, L, long_flat=m == "long-flat", roll=False)))
rows.append(row(f"{RE.shape[1]} ETFs always long (vol-scaled)", tsmom(RE, 12, always=True, roll=False)))
eq = [x for x in RE.columns if RE[x].std() * 252 ** 0.5 > 0.12]  # equity-like ETFs only
for L in (1, 12):
    rows.append(row(f"{len(eq)} equity-like ETFs L{L} long-flat", tsmom(RE[eq], L, long_flat=True, roll=False)))
rows.append(row(f"{len(eq)} equity-like ETFs always long", tsmom(RE[eq], 12, always=True, roll=False)))
mE = (1 + RE.fillna(0)).resample("ME").prod().sub(1).where(RE.resample("ME").count() > 10)
bhE = mE[(mE.index >= "2020-01-01") & (mE.index < "2026-11-01")].mean(axis=1)
show(f"B4 liquid ETFs listed before 2020 (> 5千万/日 since 2023), 2020-01..2026-10; buy-and-hold Sharpe {sr(bhE):.2f}", rows, "b4_etfs.csv")
per = []
for code in RE.columns:
    b = tsmom(RE[[code]], 12, long_flat=True, roll=False)
    b0 = tsmom(RE[[code]], 12, always=True, roll=False)
    m1 = mE[code][(mE.index >= "2020-01-01") & (mE.index < "2026-11-01")].dropna()
    per.append({"code": code, "name": enames[code], "lf12_net": sr(b["net"]), "buy_hold": sr(b0["net"]), "t": tst(b["net"] - b0["net"].reindex(b["net"].index).fillna(0))})
PE = pd.DataFrame(per).dropna(); PE.to_csv(OUT / "b4_etf_each.csv", index=False)
print(f"  each ETF, long-flat 12m net vs buy-and-hold: better in {(PE.lf12_net > PE.buy_hold).mean():.0%} of {len(PE)}; "
      f"difference t > 1.96 in {(PE.t > 1.96).sum()}, < -1.96 in {(PE.t < -1.96).sum()}")
print("  examples:", ", ".join(f"{r['name']} {r.lf12_net:+.2f} vs {r.buy_hold:+.2f}" for _, r in PE.sort_values("t", ascending=False).head(6).iterrows()))
