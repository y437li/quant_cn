# 20261116_etf_close_15m

Was there buying in the last 15 minutes of the main ETFs on 2026-11-16, and does the last 15 minutes predict the next day? Logged in `research_space/RESEARCH_LOG.md` (2026-11-16).

| File | Purpose |
|---|---|
| `fetch_etf_15m.py` | Tushare stk_mins 15-minute pull for 10 broad ETFs; stopped: the account allows 1 call a minute and 1 an hour |
| `close_bar_next_day.py` | index 5-minute cache 2015-01..2026-08: last-15-min return and volume vs next-day overnight / first 30 min / rest / full day; recent daily ETF amounts |
| `close_push_streaks.py` | consecutive closing pushes (any up last bar / top-30% last bar / top-30% on 1.2x volume) vs 1 / 5 / 20-day excess returns, by streak length, index and era |
| `first10_last5.py` | watch 14:45-14:55, act 14:55-15:00: does the 10-minute move continue into the last 5 minutes (incl. the closing auction), and what follows next day from 14:55 or 15:00 entry |
| `next_open_entry.py` | after a late push: next-day overnight vs open→10:00 vs 10:00→close, and entry at 14:55 vs next open vs next 10:00, held 1 and 5 days |
