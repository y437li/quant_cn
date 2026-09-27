# Tushare Pro API

Data vendor: **Tushare Pro** (https://tushare.pro, endpoint docs: https://tushare.pro/document/2).
Every dataset in [DATA_CATALOG.md](DATA_CATALOG.md) comes from it.

---

## 1. Authentication & permissions

- One token per account. Read it from the environment: `os.environ["TUSHARE_TOKEN"]`.
- Access is gated by account **points**. Basic endpoints (`daily`, `daily_basic`, `stock_basic`, ...)
  work on a normal tier. The `*_vip` endpoints (whole-market fundamentals by period), `cyq_perf`,
  `stk_mins`/`idx_mins` and a few others need a higher tier or a separate permission.
  The old project's account had all of the endpoints listed below.
- If a call returns a permission error, check the points requirement on that endpoint's doc page.

## 2. Two ways to call it

### a) Python SDK (`pip install tushare`)

```python
import tushare as ts
pro = ts.pro_api(os.environ["TUSHARE_TOKEN"])      # pass token explicitly
df = pro.daily(trade_date="20260828")               # returns a pandas DataFrame
df = pro.daily_basic(trade_date="20260828", fields="ts_code,trade_date,pe_ttm,pb,total_mv")
```

### b) Raw HTTP (no dependencies — what the old project's newer downloaders used)

```
POST http://api.tushare.pro
Content-Type: application/json

{"api_name": "daily",
 "token":    "<TOKEN>",
 "params":   {"trade_date": "20260828", "limit": 6000, "offset": 0},
 "fields":   "ts_code,trade_date,open,high,low,close,vol,amount"}
```

Response:

```json
{"code": 0, "msg": "",
 "data": {"fields": ["ts_code", "trade_date", "open", ...],
          "items":  [["000001.SZ", "20260828", 12.3, ...], ...]}}
```

- `code != 0` → error; the reason is in `msg` (often Chinese).
- `fields` empty string → the endpoint's default columns.
- The SDK is just a wrapper over this same POST.

## 3. Conventions & limits

| Topic | Rule |
|---|---|
| Dates | Strings `YYYYMMDD` everywhere (`trade_date`, `ann_date`, `end_date`, `period`) |
| Stock codes | `ts_code` = `600000.SH`, `000001.SZ`, `830799.BJ` |
| Index codes | `000300.SH` (CSI 300), `000905.SH` (CSI 500), `000852.SH` (CSI 1000), `000001.SH`, `399001.SZ`, `399006.SZ`, `000016.SH` |
| Row cap | ~5,000–6,000 rows per response. Page with `limit` + `offset` until a page comes back short |
| Paging exception | **`share_float` ignores `offset`** (returns the same page forever). Page it by calendar window (one month per call) instead |
| Rate limit | Per-minute call cap per endpoint. Error `msg` contains `每分钟` or `频率` → sleep ~65 s and retry |
| Other errors | Network/timeouts → retry after ~6 s, up to 3–4 times |
| Concurrency | Old project ran 8 threads with a single writer thread; worked fine |
| Empty result | Non-trading day, or no events that day — not an error |

## 4. Minimal client (stdlib only)

Condensed from `scripts/data/download_date_sweep.py`:

```python
import json, os, time, urllib.request

API_URL = "http://api.tushare.pro"
TOKEN = os.environ["TUSHARE_TOKEN"]
PAGE = 6000

def api_call(api, params, fields="", retries=4):
    payload = json.dumps({"api_name": api, "token": TOKEN,
                          "params": params, "fields": fields}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API_URL, data=payload,
                                         headers={"Content-Type": "application/json"})
            resp = json.load(urllib.request.urlopen(req, timeout=90))
            if resp["code"] != 0:
                raise RuntimeError(resp["msg"])
            return resp["data"]
        except Exception as exc:
            if attempt == retries - 1:
                raise
            rate_limited = "每分钟" in str(exc) or "频率" in str(exc)
            time.sleep(65 if rate_limited else 6)

def fetch_paged(api, params, fields=""):
    """All rows for one call, following offset paging. Returns (fields, rows)."""
    rows, offset = [], 0
    while True:
        d = api_call(api, {**params, "offset": offset, "limit": PAGE}, fields)
        rows.extend(d["items"])
        if len(d["items"]) < PAGE:
            return d["fields"], rows
        offset += PAGE

# usage
import pandas as pd
f, rows = fetch_paged("daily", {"trade_date": "20260828"})
df = pd.DataFrame(rows, columns=f)
```

Resumability: before each call check a "done" set keyed by `(endpoint, date_or_period)`; after a
successful write, add the key. The old project stored this in a `pit_fetch_log(phase, key, n_rows, fetched_at)` table.

## 5. Endpoint reference

**Sweep by** = the parameter to loop over so that each call returns the whole market.
Field lists are what the old project requested; omit `fields` to get the defaults.

### Reference / universe

| Endpoint | Sweep by | Fields used | Notes |
|---|---|---|---|
| `trade_cal` | one call: `exchange='SSE', start_date, end_date` | `cal_date,is_open,pretrade_date` | Use this as the trading calendar (old project derived it from price data — fragile) |
| `stock_basic` | `list_status` = `L`, `D`, `P` (3 calls) | `ts_code,symbol,name,area,industry,market,list_date,list_status,delist_date` | All three statuses or you get survivorship bias |
| `namechange` | none, page with offset | `ts_code,name,start_date,end_date,ann_date,change_reason` | Name history; ST/*ST status comes from here |

### Daily market data (per trading day)

| Endpoint | Sweep by | Fields used | Notes |
|---|---|---|---|
| `daily` | `trade_date` | `ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount` | **Unadjusted** prices. Suspended stocks have no row |
| `adj_factor` | `trade_date` | `ts_code,trade_date,adj_factor` | **Not used by the old project — recommended.** Adjusted price = close × adj_factor |
| `daily_basic` | `trade_date` | `ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv` | Valuation + size |
| `moneyflow` | `trade_date` | `ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,buy_md_*,sell_md_*,buy_lg_*,sell_lg_*,buy_elg_*,sell_elg_*,net_mf_vol,net_mf_amount,trade_count` | Order-size buckets: sm/md/lg/elg |
| `stk_limit` | `trade_date` | `trade_date,ts_code,up_limit,down_limit` | Exact limit prices. Use this, don't guess from board prefix (guess missed 33% of limit-ups) |
| `cyq_perf` | `trade_date` | `ts_code,trade_date,his_low,his_high,cost_5pct,cost_15pct,cost_50pct,cost_85pct,cost_95pct,weight_avg,winner_rate` | Chip distribution. Higher tier |
| `margin_detail` | `trade_date` | `ts_code,trade_date,rzye,rqye,rzmre,rzche` | Margin financing balances |
| `index_daily` | `ts_code` + `start_date`/`end_date` (per index) | `ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount` | One index per call |
| `index_weight` | `index_code` + date range | `index_code,con_code,trade_date,weight` | Index constituents (monthly snapshots) |

### Fundamentals (per report period)

`period` = quarter-end: `YYYY0331`, `YYYY0630`, `YYYY0930`, `YYYY1231`. The `*_vip` endpoints
return the whole market for one period; the non-vip versions need `ts_code`.

| Endpoint | Sweep by | Fields used | Notes |
|---|---|---|---|
| `fina_indicator_vip` | `period` | `ts_code,ann_date,end_date,eps,dt_eps,roe,roe_dt,roa,grossprofit_margin,netprofit_margin,netprofit_yoy,dt_netprofit_yoy,or_yoy,tr_yoy,debt_to_assets,current_ratio,quick_ratio,assets_turn,working_capital,retained_earnings,ebit,ebitda,fcff,ocfps,roic,invest_capital,interestdebt,netdebt,profit_dedt,update_flag` | Old project only had it from 2017 |
| `income_vip` | `period` | `ts_code,ann_date,f_ann_date,end_date,report_type,total_profit,n_income_attr_p,rd_exp,invest_income,income_tax` | |
| `balancesheet_vip` | `period` | `ts_code,ann_date,f_ann_date,end_date,report_type,total_assets,total_liab,total_cur_assets,total_cur_liab,accounts_receiv,fix_assets,lt_borr,oth_receiv,prepayment,money_cap,lt_rec,contract_liab,adv_receipts,inventories,goodwill,cip` | |
| `cashflow_vip` | `period` | `ts_code,ann_date,f_ann_date,end_date,report_type,n_cashflow_act,free_cashflow,depr_fa_coga_dpba,c_pay_acq_const_fiolta` | |
| `forecast_vip` / `forecast` | `period` (or `ann_date`) | `ts_code,ann_date,end_date,type,p_change_min,p_change_max,net_profit_min,net_profit_max,last_parent_net,first_ann_date,summary,change_reason,update_flag` | Earnings guidance. Keep **all** versions (revisions) |
| `express_vip` / `express` | `period` | `ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,diluted_eps,diluted_roe,yoy_net_profit,bps,perf_summary,update_flag` | Preliminary results |
| `disclosure_date` | `end_date` (quarter) | `ts_code,ann_date,end_date,pre_date,actual_date` | Planned vs actual report dates |

The old project asked for one table per field list; in a fresh build, request all fields for an
endpoint in a single call instead.

### Events / ownership

| Endpoint | Sweep by | Fields used | Notes |
|---|---|---|---|
| `stk_holdertrade` | `ann_date` (every weekday) | `ts_code,ann_date,holder_name,holder_type,in_de,change_vol,change_ratio,after_share,after_ratio,avg_price,total_share` | Insider buy/sell. `ann_date` is the only (and PIT-correct) date |
| `share_float` | `start_date`/`end_date` one **month** at a time | `ts_code,ann_date,float_date,float_share,float_ratio,holder_name,share_type` | Lock-up expiries; scheduled out to ~2035. Offset paging broken — see §3 |
| `stk_holdernumber` | `enddate` (quarter) | `ts_code,ann_date,end_date,holder_num` | Note param is `enddate`, not `end_date` |

### Other endpoints the old project touched

| Endpoint | Use |
|---|---|
| `weekly`, `monthly` | Weekly/monthly bars (never actually populated) |
| `stk_mins`, `idx_mins` | Intraday bars (`freq` = `1min`/`5min`/`15min`/`30min`/`60min`). Separate permission |
| `stk_auction` | Opening call-auction data |
| `ths_index`, `ths_member`, `ths_daily` | Tonghuashun concept/theme indices, members, daily bars |
| `index_classify`, `index_member_all`, `sw_daily` | Shenwan industry classification, members, daily bars |
| `hm_list`, `hm_detail` | Hot-money (游资) seat list and trade details |
| `irm_qa_sh`, `irm_qa_sz` | Investor Q&A on the SSE/SZSE interaction platforms |
| `opt_basic`, `opt_daily` | Options (used for the VIX-style index) |
| `shibor`, `yc_cb` | Interest rates / yield curve |
