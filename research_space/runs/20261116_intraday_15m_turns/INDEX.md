# 20261116_intraday_15m_turns

Do 15-minute turning signals (变盘信号) on 6 A-share indices predict the next moves, 2015-01 .. 2026-08? Logged in `research_space/RESEARCH_LOG.md` (2026-11-16).

| File | Purpose |
|---|---|
| `turn_signals_15m.py` | resamples the legacy 5-minute index cache to 16 bars a day; tests bar autocorrelation by time slot, big-bar follow-through, 3-bar runs, high-volume reversal candles, and the first up bar after a > 1% morning drop |
| `next30.py` | follow-up: sign of a 15-minute bar x the next 30 minutes, all and big bars, by index, era and time slot |
