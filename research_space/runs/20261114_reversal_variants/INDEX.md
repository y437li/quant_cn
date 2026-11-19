# research_space/runs/20261114_reversal_variants/

Question: 要加截面反转的factor吗？ (2026-11-14; asked as "洁面反转"). reversal_1m already exists, so: is there a better 1-month reversal?

## Files
| File | Purpose | Contains |
|---|---|---|
| `reversal_variants.py` | month-end 2019-02..2026-09 on derived/universe: 21-day reversal split into overnight / intraday and high / low turnover days, plus intraday-on-high-turnover-days; rank IC at 5 / 20 / 60 sessions (entry open t+1), raw and net of reversal_1m + size + turnover_60d; decile spread | |
| `campaign_check.py` | plan 25 ph2 checks on derived.features: raw 20-day IC vs the research, correlation with reversal_1m, Fama-MacBeth with both | |
| `record_trials.py` | appends the 7 research variants to the campaign TrialLog (idempotent) | |
