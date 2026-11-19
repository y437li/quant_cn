"""招商蛇口 (001979) and 招商积余 (001914): balance sheet path (cash, inventory, contract liabilities,
borrowings excl. current portion, receivables, equity), cash flow, revenue, profit, impairment, the
parent's stake in 积余, and implemented dividends. Writes cmsk_pair.csv to the lake run folder."""
from pathlib import Path

import duckdb
import pandas as pd

from quant_cn.core.config import Config

LAKE = Path(Config.load(Path(".")).lake.root)
OUT = LAKE / "meta/runs/research/20261117_property_services"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(str(LAKE / "meta/quant_cn.duckdb"), read_only=True); q = lambda s: c.execute(s).df()
pd.set_option("display.width", 250)
ENDS = "('20231231','20240930','20241231','20250930','20251231','20260630','20260930')"
frames = []
for code in ["001979.SZ", "001914.SZ"]:
    b = q(f"""SELECT end_date, arg_max(money_cap,ann_date)/1e8 cash, arg_max(inventories,ann_date)/1e8 inv,
        arg_max(contract_liab,ann_date)/1e8 contract_liab,
        (coalesce(arg_max(st_borr,ann_date),0)+coalesce(arg_max(lt_borr,ann_date),0)+coalesce(arg_max(bond_payable,ann_date),0))/1e8 debt_ex_cur,
        arg_max(accounts_receiv,ann_date)/1e8 ar, arg_max(total_hldr_eqy_exc_min_int,ann_date)/1e8 eq
        FROM curated.balancesheet_vip WHERE ts_code='{code}' AND report_type='1' AND end_date IN {ENDS} GROUP BY 1""")
    cf = q(f"SELECT end_date, arg_max(n_cashflow_act,ann_date)/1e8 ocf FROM curated.cashflow_vip WHERE ts_code='{code}' AND report_type='1' AND end_date IN {ENDS} GROUP BY 1")
    inc = q(f"""SELECT end_date, arg_max(revenue,ann_date)/1e8 rev, arg_max(n_income_attr_p,ann_date)/1e8 np,
        arg_max(assets_impair_loss,ann_date)/1e8 impair FROM curated.income_vip WHERE ts_code='{code}' AND report_type='1' AND end_date IN {ENDS} GROUP BY 1""")
    f = b.merge(cf, on="end_date", how="outer").merge(inc, on="end_date", how="outer").sort_values("end_date"); f.insert(0, "ts_code", code)
    frames.append(f); print(code); print(f.round(1).to_string(index=False))
pd.concat(frames).to_csv(OUT / "cmsk_pair.csv", index=False)
print(q("""SELECT holder_name, hold_ratio FROM curated.top10_holders WHERE ts_code='001914.SZ'
  AND end_date=(SELECT max(end_date) FROM curated.top10_holders WHERE ts_code='001914.SZ') ORDER BY hold_ratio DESC LIMIT 3""").to_string(index=False))
print(q("""SELECT ts_code, end_date, cash_div_tax, ex_date FROM curated.dividend WHERE ts_code IN ('001979.SZ','001914.SZ')
  AND end_date>='20221231' AND div_proc='实施' ORDER BY 1,2""").to_string(index=False))
