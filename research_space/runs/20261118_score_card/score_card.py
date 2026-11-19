"""Score card of the user's indicators for holdings, watchlist and any codes given: percentile among all
stocks (1 = best by the factor's sign) of the composite score and its factors, plus the RetailGauge
(the Q4 forecast file the app reads; high = retail entering) and the winner rate (cyq_perf). Usage:
score_card.py [code ...]; with no codes, the holdings and watchlist (git-ignored local files)."""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]
GAUGE = "meta/runs/holder_nowcast/holders_forecast_q4.parquet"  # the reading the app uses (ChipStructureReader)
FACTORS = {"score": "综合打分", "reversal_intraday_1m": "日内反转", "turnover_60d": "60日换手(低好)",
           "pricing_gap": "定价差(便宜好)", "dividend_yield": "股息率", "roe_ttm": "ROE",
           "profit_growth_ttm": "利润增长", "momentum_12_1": "12-1动量"}


def list_codes() -> dict[str, str]:
    pat = re.compile(r"\d{6}\.S[HZ]")
    out = {}
    for name, tag in (("local.positions.yaml", "持仓"), ("local.watchlist.yaml", "自选")):
        path = REPO / "config" / name
        if path.exists():
            for c in pat.findall(path.read_text(encoding="utf-8")):
                out.setdefault(c, tag)
    return out


def main() -> None:
    codes = {c: "查询" for c in sys.argv[1:]} or list_codes()
    cfg = Config.load(REPO)
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    q = LakeQuery(cat)
    day = q.sql("SELECT max(trade_date) d FROM derived.features")["d"].iloc[0]
    f = q.sql("SELECT ts_code, factor, value FROM derived.features WHERE trade_date = ? AND factor IN (SELECT UNNEST(?))", [day, list(FACTORS)])
    names = q.sql("SELECT ts_code, name FROM curated.stock_basic").set_index("ts_code")["name"]
    win = q.sql("SELECT ts_code, arg_max(winner_rate, trade_date) w FROM curated.cyq_perf WHERE trade_date <= ? AND trade_date > ? "
                "GROUP BY 1", [day, str(int(day) - 100)]).set_index("ts_code")["w"]
    cat.close()
    pct = f.assign(p=f.groupby("factor")["value"].rank(pct=True)).pivot(index="ts_code", columns="factor", values="p")
    gpath = Path(cfg.lake.root) / GAUGE
    g = pd.read_parquet(gpath)
    gday = dt.date.fromtimestamp(gpath.stat().st_mtime).strftime("%Y%m%d")
    rows = []
    for c, tag in codes.items():
        r = {"代码": c, "名称": names.get(c, ""), "类别": tag}
        r |= {lab: round(float(pct.at[c, k]), 2) if c in pct.index and pd.notna(pct.at[c, k]) else None for k, lab in FACTORS.items()}
        r["散户温度计"] = round(float(g.at[c, "pct"]), 2) if c in g.index else None
        r["温度计日期"] = gday if c in g.index else ""
        r["获利盘%"] = round(float(win.get(c)), 1) if c in win.index else None
        rows.append(r)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    out = pd.DataFrame(rows).sort_values(["类别", "综合打分"], ascending=[True, False])
    print(f"因子截至 {day}；分位 0–1，1 = 该因子最好（全市场）；散户温度计 1 = 散户进得最多\n")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
