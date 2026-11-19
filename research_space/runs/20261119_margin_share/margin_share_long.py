"""融资余额 / 流通市值 monthly since 2010 from Tushare margin (exchange totals) and daily_info.

Float cap (亿): SH = SH_MARKET, else SH_A + SH_B; SZ = SZ_MARKET minus its fund, bond and warrant
rows (SZ_MARKET includes them in some years). Compared on 2019+ month-ends with the margin_detail /
daily_basic series of margin_share_history.py. Writes 20261119_margin_share_long.csv to the lake's
meta/runs/research.
"""
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.tushare_client import TushareClient

R = "/Volumes/Treasury/quant_cn_lake/meta/runs/research/"
t = TushareClient(Config.load().tushare, Clock())
cal = t.query("trade_cal", {"exchange": "SSE", "start_date": "20100101", "end_date": "20261118",
                            "is_open": "1"}, ["cal_date"])
days = pd.Series(sorted(cal.cal_date))
rows = []
for d in days.groupby(days.str[:6]).max():
    m = t.query("margin", {"trade_date": d}, ["exchange_id", "rzye"])
    i = t.query("daily_info", {"trade_date": d}, ["ts_code", "float_mv"]).set_index("ts_code")
    if m.empty or i.empty:
        continue
    f = i.float_mv.fillna(0)
    sh = f.get("SH_MARKET", 0) or f.get("SH_A", 0) + f.get("SH_B", 0)
    sz_extra = f[[c for c in f.index if c.startswith(("SZ_FUND", "SZ_BOND", "SZ_WR"))
                  and c not in ("SZ_FUND",)]].sum()
    sz_extra = max(sz_extra, f.get("SZ_FUND", 0)) if "SZ_FUND" in f and sz_extra == 0 else sz_extra + f.get("SZ_FUND", 0) - f[[c for c in f.index if c.startswith("SZ_FUND_")]].sum()
    sz = f.get("SZ_MARKET", 0) - sz_extra
    rz = m.rzye.sum() / 1e8
    rows.append({"date": d, "rz": rz, "sh": sh, "sz": sz, "share": rz / (sh + sz) * 100})
df = pd.DataFrame(rows)
short = pd.read_csv(R + "20261119_margin_share.csv", dtype={"trade_date": str}).set_index("trade_date")
df["share_detail"] = df.date.map(short.share)
df.to_csv(R + "20261119_margin_share_long.csv", index=False)
ov = df.dropna(subset=["share_detail"])
print("overlap months", len(ov), "mean diff", round((ov.share - ov.share_detail).mean(), 3),
      "max abs", round((ov.share - ov.share_detail).abs().max(), 3))
df["y"] = df.date.str[:4]
print(df.groupby("y").agg(share_min=("share", "min"), share_max=("share", "max"),
                          rz_max=("rz", "max")).round(2).to_string())
for d in ("201506", "201601", "201812", "202409", "202610"):
    print(df[df.date.str.startswith(d)].round(2).to_string(header=False))
