# apps/chain_web/src/features/buyback/

回购增持 page at `#buyback` (plan 32, D-169). Read-only display of `GET /api/buyback`; every number comes from the Python `BuybackMonitorBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `buyback-page.tsx` | 回购 / 增持 switch, headline, the window's events, totals by purpose / holder type and funding, month chart, live programmes with tag / 专项贷款 / size filters, notes | `BuybackPage` |
| `month-chart.tsx` | SVG bars of new programmes' planned high per announcement month, 专项贷款 part darker | `MonthChart` |
| `buyback-format.ts` | pure helpers: 亿 / 万 amounts, ranges, percents, row filters, headline, labels | `formatYi`, `formatRange`, `formatPct`, `filterRows`, `buybackHeadline`, `KIND_LABEL`, `EVENT_LABEL`, `LOAN` |
| `buyback-format.test.ts` | vitest TC-BBF-001..002 |  |
