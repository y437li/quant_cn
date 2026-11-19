"""Pull Tushare stk_mins 15-minute bars for the main broad-index ETFs (the national-team proxy set, D-126), 2 pages each
(8,000 rows a page, about 500 sessions), newest first. This account allows 1 stk_mins call a minute, so calls are spaced 62 s.
One parquet per ETF under <lake>/meta/runs/research/20261116_etf_close_15m/bars/. Resumable: an ETF with a file is skipped."""
import os, time, requests, pandas as pd
from pathlib import Path
from quant_cn.core.config import Config
OUT = Path(Config.load().lake.root) / "meta/runs/research/20261116_etf_close_15m/bars"; OUT.mkdir(parents=True, exist_ok=True)
ETFS = ["510300.SH", "510310.SH", "510330.SH", "159919.SZ", "510050.SH", "510500.SH", "512100.SH", "159915.SZ", "588000.SH", "563360.SH"]
PAGES, GAP = 2, 62
def call(code, end):
    for attempt in range(5):
        r = requests.post("http://api.tushare.pro", json={"api_name": "stk_mins", "token": os.environ["TUSHARE_TOKEN"],
            "params": {"ts_code": code, "freq": "15min", "start_date": "2019-01-01 09:00:00", "end_date": end}, "fields": ""}, timeout=90).json()
        if r.get("code") == 0:
            d = r["data"]; return pd.DataFrame(d["items"], columns=d["fields"])
        print(code, "retry", r.get("code"), r.get("msg"), flush=True); time.sleep(GAP)
    raise RuntimeError(code)
for code in ETFS:
    f = OUT / f"{code}.parquet"
    if f.exists(): continue
    parts, end = [], "2026-11-16 15:30:00"
    for p in range(PAGES):
        df = call(code, end); time.sleep(GAP)
        if df.empty: break
        parts.append(df); first = df.trade_time.min()
        end = (pd.Timestamp(first) - pd.Timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        if len(df) < 8000: break
    b = pd.concat(parts).drop_duplicates(["trade_time"]).sort_values("trade_time"); b.to_parquet(f)
    print(code, len(b), b.trade_time.min(), b.trade_time.max(), flush=True)
