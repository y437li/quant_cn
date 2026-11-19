"""珀莱雅 (603605.SH) beyond stock_review.py: single-quarter expense ratios, DuPont path (app API),
risk-model exposures and risk split, RetailGauge, weekly large-order flow, winner-rate trend."""
import json
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

CODE, AS_OF = "603605.SH", "20261113"
c = Config.load(Path(".")); LAKE = Path(c.lake.root)
src = lambda t, root="curated": f"read_parquet('{LAKE / root}/{t}/**/*.parquet', hive_partitioning=true, union_by_name=true)"
q = lambda s: duckdb.sql(s).df()
pd.set_option("display.width", 220)

inc = q(f"""SELECT end_date, revenue, oper_cost, sell_exp, admin_exp, rd_exp, n_income_attr_p, assets_impair_loss, credit_impa_loss
           FROM (SELECT *, row_number() OVER (PARTITION BY end_date ORDER BY ann_date DESC) rn FROM {src('fundamentals/income')}
                 WHERE ts_code = '{CODE}' AND report_type = '1' AND end_date >= '20240101') WHERE rn = 1 ORDER BY end_date""")
inc["y"] = inc["end_date"].str[:4]
num = ["revenue", "oper_cost", "sell_exp", "admin_exp", "rd_exp", "n_income_attr_p", "assets_impair_loss", "credit_impa_loss"]
for col in num:
    inc[col] = inc.groupby("y")[col].diff().fillna(inc[col])
r = inc.set_index("end_date")
tab = pd.DataFrame({"收入亿": r["revenue"] / 1e8, "毛利率%": (1 - r["oper_cost"] / r["revenue"]) * 100,
                    "销售费用率%": r["sell_exp"] / r["revenue"] * 100, "管理费用率%": r["admin_exp"] / r["revenue"] * 100,
                    "研发费用率%": r["rd_exp"] / r["revenue"] * 100, "减值亿": (r["assets_impair_loss"].fillna(0) + r["credit_impa_loss"].fillna(0)) / 1e8,
                    "净利亿": r["n_income_attr_p"] / 1e8, "净利率%": r["n_income_attr_p"] / r["revenue"] * 100})
print("单季"); print(tab.round(1).T.to_string())

dp = json.load(urllib.request.urlopen(f"http://127.0.0.1:8787/api/companies/{CODE}"))["company"].get("dupont") or []
print("\n杜邦"); print(pd.DataFrame(dp)[["p", "roe", "npm", "at", "lev"]].to_string(index=False))

D = "derived"
ex = q(f"SELECT factor, exposure FROM {src('risk_exposure', D)} WHERE year = 2026 AND trade_date = '{AS_OF}' AND ts_code = '{CODE}'").set_index("factor")["exposure"]
cov = q(f"SELECT factor_i, factor_j, cov FROM {src('risk_factor_cov', D)} WHERE year = 2026 AND trade_date = '{AS_OF}'").pivot(index="factor_i", columns="factor_j", values="cov")
sig = q(f"SELECT sigma FROM {src('risk_specific_risk', D)} WHERE year = 2026 AND trade_date = '{AS_OF}' AND ts_code = '{CODE}'")["sigma"].iloc[0]
x = ex.reindex(cov.index).fillna(0.0); fv = float(x @ cov @ x); sv = sig ** 2
contrib = (x * (cov @ x)) / (fv + sv)
fr = q(f"SELECT trade_date, factor, ret FROM {src('risk_factor_return', D)} WHERE trade_date >= '20251101'").pivot(index="trade_date", columns="factor", values="ret").sort_index()
cum = lambda n: ((1 + fr.iloc[-n:]).prod() - 1) * 100
styles = ex[~ex.index.str.startswith("ind_")].drop("country", errors="ignore")
ind = ex[ex.index.str.startswith("ind_") & (ex.abs() > 0.05)]
print(f"\n风险：日波动 {np.sqrt(fv + sv):.4f}（年化约 {np.sqrt((fv + sv) * 250):.0%}），因子 {fv / (fv + sv):.0%} / 个股 {sv / (fv + sv):.0%}")
out = pd.DataFrame({"暴露": styles, "方差贡献": contrib.reindex(styles.index), "因子3月%": cum(63).reindex(styles.index), "因子12月%": cum(250).reindex(styles.index)})
print(out.round(2).sort_values("暴露").to_string())
print("行业:", {k: round(v, 2) for k, v in ind.items()}, "贡献", round(float(contrib.reindex(ind.index).sum()), 3),
      "行业因子3月%", cum(63).reindex(ind.index).round(1).to_dict(), "12月%", cum(250).reindex(ind.index).round(1).to_dict())

g = pd.read_parquet(LAKE / "meta/runs/holder_nowcast/holders_forecast_q4.parquet").loc[CODE]
print("\n散户温度计", round(float(g["pct"]), 3), "档", int(g["dec"]), "Q4户数中位预测", f"{g['50%']:+.1%}", "市场", f"{g['mk_q4']:+.1%}")
mf = q(f"""SELECT trade_date, (buy_lg_amount + buy_elg_amount - sell_lg_amount - sell_elg_amount) / 1e4 AS lg,
          (buy_sm_amount - sell_sm_amount) / 1e4 AS sm FROM {src('moneyflow')} WHERE ts_code = '{CODE}' AND trade_date >= '20260815'""")
mf["d"] = pd.to_datetime(mf["trade_date"])
print("\n每周大单/小单（亿）"); print(mf.set_index("d")[["lg", "sm"]].resample("W-FRI").sum().round(2).tail(10).T.to_string())
cy = TushareClient(c.tushare, Clock()).query("cyq_perf", {"ts_code": CODE, "start_date": "20260601", "end_date": AS_OF}, [])
cy["d"] = pd.to_datetime(cy["trade_date"])
print("\n获利盘与成本"); print(cy.set_index("d").sort_index().resample("ME").last()[["winner_rate", "cost_15pct", "cost_50pct", "cost_85pct"]].round(1).T.to_string())
