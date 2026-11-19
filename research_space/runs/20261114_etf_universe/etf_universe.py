"""Listed exchange funds the user can buy, grouped for the CTA-style ETF book (2026-11-14).

fund_basic market E, listed, not delisted; liquidity = mean daily amount over the last 60 sessions of fund_daily
(千元 -> 亿元); classified by name keywords into 债券 / 黄金白银 / 商品期货 / 海外 / 货币 / A股宽基 / A股行业主题.
Writes etf_universe.csv (all) and prints the top funds per group by liquidity, one per tracked index name.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_etf_universe"; OUT.mkdir(parents=True, exist_ok=True)
c = duckdb.connect()
pd.set_option("display.width", 240); pd.set_option("display.max_rows", 400)
D = c.execute(f"""
with b as (select ts_code, name, management, list_date, benchmark, m_fee, invest_type, fund_type
           from read_parquet('{LAKE}/curated/reference/fund_basic.parquet')
           where market = 'E' and (delist_date is null or delist_date = '') and list_date is not null),
last as (select distinct trade_date from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
         order by trade_date desc limit 60),
liq as (select ts_code, avg(amount) / 1e5 amt_yi, count(*) n, arg_max(close, trade_date) last_close
        from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
        where trade_date in (select trade_date from last) group by 1)
select b.*, liq.amt_yi, liq.last_close from b join liq using (ts_code) where liq.n >= 40""").df()
RULES = [("货币", r"货币|快线|短融|添益|日利|保证金|现金"),
         ("债券", r"债|利率|信用|可转|城投"),
         ("黄金白银", r"黄金|金ETF|上海金|白银"),
         ("商品期货", r"豆粕|有色|能源化工|能化|原油|商品"),
         ("海外", r"纳斯达克|纳指|标普|道琼斯|日经|德国|法国|东南亚|沙特|巴西|亚太|美国|恒生|港股|H股|中概|海外|国际|全球|QDII|香港|中韩|日本|欧洲|英国|越南|印度|纳100|互联网50")]
BROAD = r"沪深300|中证500|中证1000|中证2000|创业板|科创|上证50|A50|中证A500|A500|上证180|深证100|双创|红利|MSCI中国A|中证800|国证2000|北证50|上证指数|综指|深证成指|自由现金流|价值|成长|基本面"
def classify(n: str) -> str:
    import re
    for g, pat in RULES:
        if re.search(pat, n):
            return g
    return "A股宽基/风格" if re.search(BROAD, n) else "A股行业主题"
D["group"] = D.name.map(classify)
D = D.sort_values("amt_yi", ascending=False)
D.to_csv(OUT / "etf_universe.csv", index=False)
print("count by group (liquid = 近60日日均成交 > 1 亿):")
print(D.groupby("group").agg(n=("ts_code", "size"), liquid=("amt_yi", lambda x: int((x > 1).sum()))).to_string())
for g in ("A股宽基/风格", "债券", "黄金白银", "商品期货", "海外", "货币", "A股行业主题"):
    s = D[D.group == g].head(25 if g != "A股行业主题" else 30)
    print(f"\n== {g} (top by 60-day amount, 亿元)")
    print(s[["ts_code", "name", "management", "list_date", "amt_yi", "m_fee"]].round(2).to_string(index=False))
