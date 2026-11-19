"""铅锌 fundamentals (as of 2026-11-13): metal prices and curves, single-quarter financials,
business mix, balance sheet, cash flow, valuation of the 13 Shenwan 铅锌 members."""
import json
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

AS_OF = "20261113"
c = Config.load(Path("."))
LAKE = Path(c.lake.root)
OUT = LAKE / "meta/runs/research/20261113_niche_industries"
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 60)

# 1) metals from the futures monitor document of the same day
fm = json.loads(Path("research_space/prototypes/chain_view/futures_monitor.json").read_text())
fam = {f["family"]: f for f in fm["families"]}
rows = []
for k in ("ZN.SHF", "PB.SHF", "AG.SHF", "SN.SHF", "CU.SHF"):
    f = fam[k]; b = f.get("broker") or {}
    rows.append({"metal": f["name"], "price": f["price"], "chg_3m": f["chg_3m"], "chg_1y": f["chg_1y"],
                 "pct_1y": f["pct_1y"], "pct_5y": f["pct_5y"], "front_vs_4th": f["front_vs_4th"],
                 "f4_pct_5y": f["front_vs_4th_pct"], "shape": f["shape"], "oi_chg_5d": f["oi_chg_5d"],
                 "broker_net_share": b.get("net_share"), "broker_pct_5y": b.get("net_share_pct_5y")})
print("metals (dominant contract)"); print(pd.DataFrame(rows).round(3).to_string(index=False))

cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
q = LakeQuery(cat)
mem = q.sql("""SELECT ts_code, name FROM curated.index_member_all WHERE l3_name = '铅锌'
               AND (out_date IS NULL OR out_date = '' OR out_date > ?)""", [AS_OF]).drop_duplicates("ts_code")
codes = mem["ts_code"].tolist()
names = mem.set_index("ts_code")["name"]

def latest(table: str, cols: str) -> pd.DataFrame:
    d = q.sql(f"""SELECT ts_code, end_date, f_ann_date, {cols} FROM curated.{table}
                  WHERE list_contains(?, ts_code) AND end_date >= '20250101' AND f_ann_date <= ?
                  AND report_type = '1'""", [codes, AS_OF])
    return d.sort_values("f_ann_date").drop_duplicates(["ts_code", "end_date"], keep="last")

inc = latest("income_vip", "revenue, oper_cost, n_income_attr_p")
# 2) single quarters from YTD figures
inc = inc.sort_values(["ts_code", "end_date"])
inc["year"] = inc["end_date"].str[:4]
for col in ("revenue", "oper_cost", "n_income_attr_p"):
    inc[f"q_{col}"] = inc[col] - inc.groupby(["ts_code", "year"])[col].shift().fillna(0)
inc["q_gm"] = (1 - inc["q_oper_cost"] / inc["q_revenue"]) * 100
inc["q"] = inc["end_date"].str[2:4] + "Q" + (inc["end_date"].str[4:6].astype(int) // 3).astype(str)
gm = inc.pivot_table(index="ts_code", columns="q", values="q_gm").round(1)
np_q = (inc.pivot_table(index="ts_code", columns="q", values="q_n_income_attr_p") / 1e8).round(2)
rev_q = (inc.pivot_table(index="ts_code", columns="q", values="q_revenue") / 1e8).round(1)
print("\nsingle-quarter gross margin %"); print(gm.rename(index=names).to_string())
print("\nsingle-quarter net profit to parent, 亿"); print(np_q.rename(index=names).to_string())
print("\nsingle-quarter revenue, 亿"); print(rev_q.rename(index=names).to_string())

# 3) business mix (latest disclosed, by product)
mb = q.sql("""SELECT ts_code, end_date, bz_item, bz_sales, bz_profit FROM curated.fina_mainbz_p
              WHERE list_contains(?, ts_code) AND end_date >= '20250601'""", [codes])
mb = mb[mb["end_date"] == mb.groupby("ts_code")["end_date"].transform("max")].drop_duplicates(["ts_code", "bz_item"])
mb["share"] = mb["bz_sales"] / mb.groupby("ts_code")["bz_sales"].transform("sum") * 100
mb["gp_share"] = mb["bz_profit"] / mb.groupby("ts_code")["bz_profit"].transform("sum") * 100
top = mb.sort_values(["ts_code", "bz_profit"], ascending=[True, False]).groupby("ts_code").head(3)
top["item"] = [f"{i} {s:.0f}%收入/" + ("—" if pd.isna(g) else f"{g:.0f}%") + "毛利"
               for i, s, g in zip(top["bz_item"], top["share"], top["gp_share"], strict=True)]
mix = top.groupby("ts_code").agg(period=("end_date", "first"), top_items=("item", "；".join))
print("\nbusiness mix (top 3 by gross profit)"); print(mix.rename(index=names).to_string())

# 4) balance sheet, cash flow, valuation
bs = latest("balancesheet_vip", "total_assets, total_liab, money_cap, st_borr, lt_borr, bond_payable")
bs = bs[bs["end_date"] == "20260930"].set_index("ts_code")
cf = latest("cashflow_vip", "n_cashflow_act, c_pay_acq_const_fiolta")
cf = cf[cf["end_date"] == "20260930"].set_index("ts_code")
ytd = inc[inc["end_date"] == "20260930"].set_index("ts_code")
val = q.sql("""SELECT ts_code, pe_ttm, pb, dv_ttm, total_mv / 1e4 AS mv FROM curated.daily_basic
               WHERE trade_date = ? AND list_contains(?, ts_code)""", [AS_OF, codes]).set_index("ts_code")
fi = q.sql("""SELECT ts_code, roe, or_yoy, dt_netprofit_yoy FROM curated.fina_indicator_vip
              WHERE end_date = '20260930' AND ann_date <= ? AND list_contains(?, ts_code)""", [AS_OF, codes])
fi = fi.drop_duplicates("ts_code", keep="last").set_index("ts_code")
cat.close()
debt = bs["st_borr"].fillna(0) + bs["lt_borr"].fillna(0) + bs["bond_payable"].fillna(0)
tab = pd.DataFrame({
    "mv_yi": val["mv"], "pe_ttm": val["pe_ttm"], "pb": val["pb"], "div_yld": val["dv_ttm"],
    "roe_ytd": fi["roe"], "rev_yoy": fi["or_yoy"], "dedt_yoy": fi["dt_netprofit_yoy"],
    "liab_ratio": bs["total_liab"] / bs["total_assets"] * 100,
    "net_debt_yi": (debt - bs["money_cap"]) / 1e8,
    "ocf_to_np": cf["n_cashflow_act"] / ytd["n_income_attr_p"],
    "capex_yi": cf["c_pay_acq_const_fiolta"] / 1e8,
}).rename(index=names).round(2)
print("\nbalance sheet, cash flow, valuation (Q3 YTD)"); print(tab.sort_values("pe_ttm").to_string())
tab.to_csv(OUT / "lead_zinc_table.csv"); gm.to_csv(OUT / "lead_zinc_q_gm.csv"); mix.to_csv(OUT / "lead_zinc_mix.csv")
