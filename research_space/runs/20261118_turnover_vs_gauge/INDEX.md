# 20261118_turnover_vs_gauge

Does the RetailGauge (散户温度计) overlap the score's turnover_60d, and does it improve the score? Month ends 2023-01 → 2026-10 (gauge history from 2023). Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `turnover_vs_gauge.py` | month-end panel (turnover_60d processed value, latest gauge reading, fwd20 / fwd60 excess): correlation, ICs, Fama-MacBeth with both, turnover tercile × hot gauge; all and large caps; `load()` reused below |
| `score_with_gauge.py` | current score vs score + z(−gauge) at equal weight: IC 20 / 60, quintile and decile long-short, top-bucket excess; all and large caps |
