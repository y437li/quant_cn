"""Factor exposures of 驰宏锌锗 and the lead-zinc / metal peers in the risk model (as of the last
risk session): style and industry exposures, risk split (factor vs specific, by factor), the
exposed factors' returns over 1 / 3 / 12 months, and how the 有色 industry factor sits now."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root); D = LAKE / "derived"
OUT = LAKE / "meta/runs/research/20261113_niche_industries"
src = lambda t: f"read_parquet('{D}/{t}/**/*.parquet', hive_partitioning=true)"
q = lambda s: duckdb.sql(s).df()
CODES = {"600497.SH": "驰宏锌锗", "603132.SH": "金徽股份", "600338.SH": "西藏珠峰", "600961.SH": "株冶集团",
         "000060.SZ": "中金岭南", "000426.SZ": "兴业银锡", "601899.SH": "紫金矿业"}
last = q(f"SELECT max(trade_date) d FROM {src('risk_exposure')} WHERE year = 2026")["d"][0]
ex = q(f"SELECT ts_code, factor, exposure FROM {src('risk_exposure')} WHERE year = 2026 AND trade_date = '{last}'")
ex = ex[ex["ts_code"].isin(CODES)].pivot(index="factor", columns="ts_code", values="exposure").rename(columns=CODES)
styles = ex[~ex.index.str.startswith("ind_") & (ex.index != "country")]
inds = ex[ex.index.str.startswith("ind_")]
pd.set_option("display.width", 220)
print("as of", last); print("\nstyle exposures (std)"); print(styles.round(2).to_string())
print("\nindustry factors with weight"); print(inds[(inds.abs() > 0.05).any(axis=1)].round(2).to_string())

cov = q(f"""SELECT factor_i, factor_j, cov FROM {src('risk_factor_cov')} WHERE year = 2026 AND trade_date = '{last}'""")
cov = cov.pivot(index="factor_i", columns="factor_j", values="cov")
spec = q(f"SELECT ts_code, sigma FROM {src('risk_specific_risk')} WHERE year = 2026 AND trade_date = '{last}'").set_index("ts_code")["sigma"]
code = "600497.SH"
x = ex[CODES[code]].reindex(cov.index).fillna(0.0)
fv = float(x @ cov @ x); sv = float(spec.get(code, np.nan)) ** 2
contrib = (x * (cov @ x)) / (fv + sv)
print(f"\n驰宏 risk (annualised if cov is): total {np.sqrt(fv + sv):.3f}, factor share {fv / (fv + sv):.0%}, specific {sv / (fv + sv):.0%}")
print("top contributors (share of variance)"); print(contrib.sort_values(ascending=False).head(8).round(3).to_string())

fr = q(f"SELECT trade_date, factor, ret FROM {src('risk_factor_return')} WHERE trade_date >= '20251101'")
fr = fr.pivot(index="trade_date", columns="factor", values="ret").sort_index()
cum = lambda n: (1 + fr.iloc[-n:]).prod() - 1
top = contrib.sort_values(ascending=False).head(6).index.tolist() + ["ind_non_ferrous", "momentum", "residual_volatility", "beta"]
top = [f for f in dict.fromkeys(top) if f in fr.columns]
tab = pd.DataFrame({"1m": cum(21), "3m": cum(63), "12m": cum(250), "驰宏暴露": x.reindex(top)}).loc[top]
print("\nfactor returns (cumulative)"); print((tab.drop(columns="驰宏暴露") * 100).round(1).join(tab["驰宏暴露"].round(2)).to_string())
ex.to_csv(OUT / "metal_exposures.csv"); contrib.to_csv(OUT / "chihong_risk_contrib.csv")
