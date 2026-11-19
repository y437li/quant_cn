"""筹码结构 of the niche-industry companies (as of 2026-11-13).

Lake: ChipStructureReader (holders, top-10 institutions, northbound, margin, large-order flow,
unlocks, insider sales, RetailGauge). Tushare cyq_perf (live call, not in the lake): winner
rate and the 15/85% cost band on the last session. Washout study (20261113_washout_study):
after a fall, winner rate <= 10% plus 20-day large-order inflow was the best combination;
retail rushing in (holder count up) the worst.
"""
from pathlib import Path

import pandas as pd

from quant_cn.app_service_builder import GAUGE_FILE
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

AS_OF = "20261113"
c = Config.load(Path("."))
OUT = Path(c.lake.root) / "meta/runs/research/20261113_niche_industries"
tp = pd.read_csv(OUT / "target_prices.csv")
cov = pd.read_csv(OUT / "coverage.csv").set_index("ts_code")
codes = cov.index.tolist()
cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
chips = ChipStructureReader(LakeQuery(cat), Path(c.lake.root) / GAUGE_FILE).read(codes, AS_OF)
cat.close()
client = TushareClient(c.tushare, Clock())
cyq = []
for code in codes:
    d = client.query("cyq_perf", {"ts_code": code, "start_date": "20261101", "end_date": AS_OF}, [])
    if not d.empty:
        cyq.append(d.sort_values("trade_date").iloc[-1])
cyq = pd.DataFrame(cyq).set_index("ts_code") if cyq else pd.DataFrame()
df = cov[["l3_name", "name", "close", "mv", "brokers_12m"]].join(chips)
if not cyq.empty:
    df["winner_rate"] = cyq["winner_rate"]
    df["cost_15"], df["cost_85"] = cyq["cost_15pct"], cyq["cost_85pct"]
df["tp_upside"] = tp.set_index("ts_code")["upside"]
df.to_csv(OUT / "chips.csv")
pd.set_option("display.width", 260)
ind = df.groupby("l3_name").agg(
    n=("name", "size"), holders_chg=("holders_chg_q", "median"), inst_pp=("inst_top10_dq_pp", "median"),
    margin_60d=("margin_chg_60d", "median"), lg_net_20d=("lg_net_20d", "median"),
    winner=("winner_rate", "median"), gauge=("retail_gauge", "median"),
    unlock=("unlock_6m_pct", "median"))
print("by industry (medians)"); print(ind.round(3).to_string())
focus = ["浙江龙盛", "闰土股份", "吉华集团", "安诺其", "建新股份", "驰宏锌锗", "株冶集团", "兴业银锡", "中金岭南",
         "盛达资源", "金徽股份", "四方达", "美畅股份", "凤形股份", "国机精工", "惠丰钻石", "钒钛股份", "方大炭素"]
cols = ["l3_name", "name", "close", "holders_chg_q", "inst_top10_dq_pp", "north_chg_pp", "margin_chg_60d",
        "lg_net_20d", "lg_weeks_pos_4w", "winner_rate", "cost_15", "cost_85", "retail_gauge", "unlock_6m_pct",
        "insider_sell_6m_pct", "tp_upside"]
print("\nfocus"); print(df[df["name"].isin(focus)][cols].round(3).to_string(index=False))
