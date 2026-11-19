"""Plan 21 rules on themes (grid, gas turbine, rare earth, minor metals) and on franchise-licence names.

Needs the panel from ../20261113_opportunity_list/market_panel.py and the drawdown/chip table from
../20261113_washout_study/washout_event_study.py.
"""
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).resolve().parent
PANEL = (HERE.parent / "20261113_opportunity_list" / "rule_screen.py").read_text(encoding="utf-8")
exec(PANEL.split("u=x[(x.cmv")[0])  # builds x (panel + gauge + factors + flows), L, LAKE, s
OUT = LAKE / "meta/runs/research/20261113_theme_screen"
OUT.mkdir(parents=True, exist_ok=True)
GAS_TURBINE = ["600875.SH", "603308.SH", "000534.SZ", "002595.SZ", "002353.SZ", "605060.SH", "600893.SH",
               "688510.SH", "300855.SZ", "300034.SZ", "600399.SH", "688231.SH", "601727.SH", "688122.SH"]
FRANCHISE = {"600161.SH": "血制品", "002007.SZ": "血制品", "002252.SZ": "血制品", "000403.SZ": "血制品",
             "300294.SZ": "血制品", "002262.SZ": "精麻药", "600079.SH": "精麻药", "601888.SH": "免税",
             "600859.SH": "免税", "600185.SH": "免税", "600111.SH": "稀土", "000831.SZ": "稀土",
             "000657.SZ": "钨", "600549.SH": "钨"}
RULES = ["R1_利润拐点", "R2_散户离开", "R3_大单流入", "R4_估值合理", "R5_因子不加重"]
v = x.copy()
v["R1_利润拐点"] = ((v.y3 > 0.15) & (v.y3 > v.y2 + 0.05) & (v.q3 > 0.2) & (v.q3ly > 0.03)) | ((v.g27 > 0.15) & (v.rev27 >= 0))
v["R2_散户离开"] = v.pct <= 0.30
v["R3_大单流入"] = (v.lg_weeks_pos >= 3) & (v.lg_4w > 0)
v["R4_估值合理"] = (v.pe_ttm > 0) & (v.pe_ttm < v.pe_med)
v["R5_因子不加重"] = (v.momentum >= -0.2) & (v.usd_sensitivity >= -0.3)
v["hits"] = v[RULES].sum(axis=1)
v["missing"] = v[RULES].apply(lambda r: ",".join(c.split("_")[1] for c in RULES if not r[c]), axis=1)
v = v.join(pd.read_parquet(LAKE / "meta/runs/research/20261113_washout_study/washout_now.parquet")[["dd", "winner_rate"]])
themes = {"grid": v.l3.isin(["电网自动化设备", "输变电设备", "配电设备", "线缆部件及其他", "电工仪器仪表"]),
          "gas_turbine": v.index.isin(GAS_TURBINE), "rare_earth": v.l3.isin(["稀土", "磁性材料"]),
          "minor_metals": v.l3.isin(["钨", "钼", "钴", "锂", "镍", "其他小金属"]), "franchise": v.index.isin(list(FRANCHISE))}
cols = ["name", "l3", "cmv", "pe_ttm", "pe_med", "y3", "g27", "rev27", "pct", "lg_weeks_pos", "lg_4w", "dd",
        "winner_rate", "momentum", "usd_sensitivity", "hits", "missing"]
pd.set_option("display.width", 300)
for name, mask in themes.items():
    g = v[mask & ((v.cmv >= 30) | (name == "franchise"))]
    print(f"\n== {name}: n={len(g)} | PE/median {(g.pe_ttm / g.pe_med).median():.2f} | gauge {g.pct.median():.2f} "
          f"| large orders 4w {g.lg_4w.sum():.1f} 亿 | 2027E revision {g.rev27.median() * 100:.1f}%")
    print(g.sort_values(["hits", "cmv"], ascending=False)[cols].head(15).round(2).to_string())
    g[cols].to_csv(OUT / f"{name}.csv")
