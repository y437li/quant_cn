# apps/chain_web/src/features/conditions/

Structured conditions (plan 15 ph7f): chips and pure formatters used by the 观察账本 cards and the 持仓 notes section. Every value is computed in Python (`ConditionEvaluator`, `PositionReviewer`).

## Files
| File | Purpose | Contains |
|---|---|---|
| `condition-chips.tsx` | one chip per condition: met / unmet / unknown, tooltip with value and threshold | `ConditionChips` |
| `condition-format.ts` | metric units, chip marks and titles, counts, status labels, chip-row columns, alert lines, RetailGauge colour bands | `GAUGE_BANDS`, `gaugeBand`, `metricText`, `conditionTitle`, `stateMark`, `conditionCount`, `conditionStatusLabel`, `CHIP_COLUMNS`, `listAlerts` |
| `condition-format.test.ts` | TC-CF-001..004 |  |
