# research_space/runs/20261113_niche_industries/

Question: 有什么冷门的行业我们没听过的吗 (2026-11-13).

## Files
| File | Purpose | Contains |
|---|---|---|
| `niche_screen.py` | Shenwan L3 industries with few analyst reports per company whose median Q3 YTD revenue growth > 10% and gross margin rose; leading members with growth, coverage, 6-month return and holder-count change |  |
| `coverage.py` | analyst coverage per member of those industries from report_rc: reports and brokers in 12 months, last 3 months vs before, first report, latest rating, FY2026/27 consensus profit, PE27, target-price upside |  |
| `target_prices.py` | target prices per company: report_rc max/min_price vs targets extracted from report PDFs (valuations.jsonl), median vs close |  |
| `chips.py` | 筹码结构 per company: ChipStructureReader signals plus live Tushare cyq_perf winner rate and cost band; industry medians and a focus list |  |
| `lead_zinc.py` | 铅锌 fundamentals: metal prices and curves (futures monitor), single-quarter revenue / gross margin / profit, business mix, balance sheet, cash flow, valuation |  |
| `chihong_chips.py` | 驰宏锌锗 chip time series from parquet: holders, top-10 float holders, northbound, margin, weekly large / small order flow, cyq_perf winner rate and cost bands, RetailGauge |  |
| `rule_backtest.py` | history of the 驰宏 watch rule at quarter ends: layers 下杀, winner rate, large-order weeks, holder decline, margin, gross margin; 3-month absolute and excess returns |  |
| `factor_exposure.py` | risk-model exposures of 驰宏 and metal peers, 驰宏 risk split by factor, exposed factors' 1 / 3 / 12-month returns |  |
| `confirm_entry.py` | immediate vs confirmation entry (20-day mean, cost median) for the washout rule with costs and limit-up / limit-down handling |  |
