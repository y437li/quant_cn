# research_space/runs/20261113_cost_break/

Question: 跌破筹码成本区后是否说明还没跌完？(2026-11-13). Events are the first close below cyq cost_5pct in 60 sessions, float cap ≥ 50亿, 2021-03 to 2026-08; compared with every stock sampled every 20 sessions.

## Files
| File | Purpose | Contains |
|---|---|---|
| `cost_break.py` | event study after a break below the modelled chip floor: 20 / 60-session excess, hit rate, further ≥ 10% drop, split by prior 20-day large-order flow |  |
| `cost_break_retail.py` | the same breaks split by holder-count change: last announced (point in time) and realised over the break quarter (look-ahead, what RetailGauge nowcasts), with the all-stock baseline |  |
