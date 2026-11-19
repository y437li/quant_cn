"""Pilot pull of BaoStock 5-minute bars (unadjusted) for every CSI 300 / CSI 500 member in the window.
Resumable: one parquet per stock under <lake>/meta/runs/research/20261113_minute_factors/bars/.
Usage: fetch_5min.py [workers] [limit]"""
import random, sys, time, duckdb, pandas as pd
from multiprocessing import Pool
from pathlib import Path
from quant_cn.core.config import Config
LAKE = Path(Config.load().lake.root)
BARS = LAKE / "meta/runs/research/20261113_minute_factors/bars"; BARS.mkdir(parents=True, exist_ok=True)
START, END = "20250506", "20261112"
FIELDS = "date,time,open,high,low,close,volume,amount"
NUM = ["open", "high", "low", "close", "volume", "amount"]
_bs = None

def login():
    # BaostockClient.query cannot be used here: baostock's get_data() calls the removed
    # DataFrame.append once a result spans more than one 10k-row page, so rows are read with next().
    global _bs
    import baostock as bs
    for k in range(6):
        if str(bs.login().error_code) == "0":
            _bs = bs; return
        time.sleep(10 * (k + 1))
    raise RuntimeError("baostock login failed")

def to_bs(code: str) -> str:
    sym, ex = code.split(".")
    return f"{ex.lower()}.{sym}"

def pull(code: str) -> tuple[str, int, float]:
    out = BARS / f"{code}.parquet"
    if out.exists():
        return code, -1, 0.0
    if _bs is None:
        time.sleep(random.uniform(0, 8))  # stagger logins
        login()
    t = time.time()
    for attempt in range(4):
        rs = _bs.query_history_k_data_plus(to_bs(code), FIELDS, start_date=f"{START[:4]}-{START[4:6]}-{START[6:]}",
                                           end_date=f"{END[:4]}-{END[4:6]}-{END[6:]}", frequency="5", adjustflag="3")
        rows = []
        while str(rs.error_code) == "0" and rs.next():
            rows.append(rs.get_row_data())
        if str(rs.error_code) == "0":
            break
        time.sleep(20); login()
    else:
        return code, -2, time.time() - t
    df = pd.DataFrame(rows, columns=FIELDS.split(","))
    df[NUM] = df[NUM].apply(pd.to_numeric, errors="coerce")
    df.insert(0, "ts_code", code)
    df.to_parquet(out, index=False)
    return code, len(df), time.time() - t

if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    codes = duckdb.sql(f"""select distinct con_code from read_parquet('{LAKE}/curated/index_weight/**/*.parquet',
        hive_partitioning=true, union_by_name=true) where index_code in ('000300.SH','000905.SH')
        and trade_date between '20250401' and '{END}' order by 1""").df().con_code.tolist()[:limit]
    print(len(codes), "codes", flush=True)
    t0 = time.time()
    with Pool(workers) as p:
        for i, (c, n, s) in enumerate(p.imap_unordered(pull, codes), 1):
            if i % 20 == 0 or limit:
                print(f"{i}/{len(codes)} {c} rows={n} {s:.0f}s elapsed={time.time()-t0:.0f}s", flush=True)
