# 20261118_priced_in

Is A-share earnings news priced in before disclosure ("不抬轿子"), and is bad news punished harder at high valuations? Earnings event study 2019–2026. Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `priced_in.py` | first disclosure per quarter (forecast / express / income), SUE deciles within each end_date, excess vs the equal-weight market over pre [-60,-1], [-20,-1], reaction [0,+1], post [+2,+21], [+2,+61]; spread t-stats, rank IC, SUE × pre-run quintile, by year; writes events.parquet to the lake's meta/runs/research/20261118_priced_in |
| `valuation_split.py` | the same windows for SUE deciles 0 / 9 by pre-event PE TTM quintile (loss-makers apart) |
| `tech_bull_case.py` | the tech bull 2025-07..2026-11: per-quarter SUE-quintile windows for 电子 / 通信 / 计算机, and the 12 largest tech names (peak, drawdown, PE at peak and now, single-quarter profit yoy, pre / reaction / post per report) |
| `sector_peak_signal.py` | sector top signal per SW L2 and quarter (PIT membership): best-surprise events' pre60 ≥ 15% and reaction ≤ 1%; sector excess vs the mean L2 index 60 / 120 sessions after 80% of the sector has reported; prior 120-session rally; median shareholder-count change (crowding); cases 白酒 / 光伏 / 电池 / 半导体 / 通信设备 / 元件 / 医疗服务 / 煤炭 |
| `tech_implied_growth.py` | tech leaders at the 2026 peak and now: TTM profit, reverse-DCF constant growth (ImpliedExpectations, exit PE 12 / 25), consensus FY2026–28 medians, forward PE |
| `tech_fade_growth.py` | the same caps with growth fading ×0.7 a year (first-year growth needed) and the 2028 exit PE implied by consensus FY2028 |
| `tech_fomo_premium.py` | FOMO premium: market cap over a value from consensus FY2026–28, growth after 2028 fading ×0.7 to 2035, exit PE 15, 9% (peak and now; no-fade variant) |
