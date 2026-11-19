"""How wide is the gap between small-cap / tech and large-cap A-share VIX today, and what followed similar gaps?
VIX lines come from VolatilityMonitorBuilder (CBOE method on A-share options, config/volatility_monitor.yaml) with the window
widened to the full option history. Gap = 中证1000 VIX − 300ETF VIX (and 科创50 − 50ETF). Forward returns from ETF closes
(fund_daily pct_chg, chained): 512100 (中证1000), 510300 (沪深300), 588000 (科创50), 510050 (上证50); entry at the
signal day's close. Buckets of the gap's expanding percentile (no look-ahead) -> next 5 / 20 sessions."""
import duckdb, numpy as np, pandas as pd
from quant_cn.calculation.volatility_monitor_builder import VolatilityMonitorBuilder
from quant_cn.core.config import Config
from quant_cn.core.volatility_monitor_settings import VolatilityMonitorSettings
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
cfg = Config.load(); LAKE = cfg.lake.root
OUT = LAKE / "meta/runs/research/20261116_vix_divergence"; OUT.mkdir(parents=True, exist_ok=True)
s = VolatilityMonitorSettings.load(cfg.repo_root).model_copy(update={"window": 3000})
cat = LakeCatalog(LAKE, cfg.datasets, read_only=True)
try:
    doc = VolatilityMonitorBuilder(s, LakeQuery(cat)).build(None)
finally:
    cat.close()
V = pd.DataFrame({l["key"]: pd.Series({h["date"]: h["value"] for h in l["history"]}) for l in doc["lines"]}).sort_index()
V.to_csv(OUT / "vix_lines.csv")
print("first dates:", {k: V[k].first_valid_index() for k in V}, "| last", V.index[-1])
r = lambda t: f"read_parquet('{LAKE}/curated/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
E = {"512100.SH": "c1000", "510300.SH": "c300", "588000.SH": "star50", "510050.SH": "c50"}
px = duckdb.sql(f"""select ts_code, trade_date, pct_chg from {r('fund_daily')} where ts_code in {tuple(E)} and trade_date >= '20190101'""").df()
# chained from pct_chg (vs the split-adjusted pre_close), so share consolidations (512100, 2022-09) do not show as returns
P = (1 + px.pivot(index="trade_date", columns="ts_code", values="pct_chg").rename(columns=E).sort_index() / 100).cumprod()
P = P.reindex(V.index).ffill()
pairs = {"1000−300": ("cn_1000", "cn_300", "c1000", "c300"), "科创50−50": ("cn_star50", "cn_50", "star50", "c50")}
pd.set_option("display.width", 220)
for name, (hi, lo, ph, pl) in pairs.items():
    g = (V[hi] - V[lo]).dropna(); g = g[g.index >= g.index[0]]
    pct = g.expanding(min_periods=120).rank(pct=True)
    print(f"\n== {name}: now {g.iloc[-1]:.1f} (VIX {V[hi].iloc[-1]:.1f} vs {V[lo].iloc[-1]:.1f}); full-history pct {(g <= g.iloc[-1]).mean():.0%}; "
          f"median {g.median():.1f}, p90 {g.quantile(.9):.1f}, max {g.max():.1f} on {g.idxmax()}; since {g.index[0]} ({len(g)} days)")
    print("   last 10 days:", g.tail(10).round(1).to_dict())
    rows = []
    for h in (5, 20):
        fh = np.log(P[ph].shift(-h) / P[ph]); fl = np.log(P[pl].shift(-h) / P[pl])
        d = pd.DataFrame({"pct": pct, "hi": fh, "lo": fl}).dropna()
        d["rel"] = d.hi - d.lo; d["b"] = pd.cut(d.pct, [0, .5, .8, .9, 1.0], labels=["<50%", "50-80%", "80-90%", "≥90%"])
        t = d.groupby("b", observed=True).agg(n=("rel", "size"), small_abs=("hi", "mean"), large_abs=("lo", "mean"), rel=("rel", "mean"), rel_up=("rel", lambda x: (x > 0).mean()))
        t[["small_abs", "large_abs", "rel"]] *= 100; t["H"] = h; rows.append(t)
    print(pd.concat(rows).round(2).to_string())
