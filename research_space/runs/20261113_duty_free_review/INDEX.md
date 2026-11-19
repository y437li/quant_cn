# research_space/runs/20261113_duty_free_review/

Question: 中国中免是否到了可以买的时候 (2026-11-13). Run from the repo root; `stock_review.py` needs `--env-file .env` (cyq_perf), `book_what_if.py` opens the lake catalog read-only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `stock_review.py` | per-stock review: quarterly revenue / GM / profit, consensus revisions, valuation vs 5y, holders, top-10 float holders, insider trades, unlocks, big-order flow and margin, chip distribution; codes as arguments |  |
| `touch_odds.py` | odds of touching 48 / 46 / 44 within 21 / 63 / 126 sessions: full history, 2024+, zero-drift vol model |  |
| `book_what_if.py` | add 601888.SH at 0 / 3 / 5 / 8% funded from cash: book vol, momentum, USD, beta; correlation with each holding |  |
