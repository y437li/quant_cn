# apps/chain_web/src/features/holdings/

持仓 page at `#holdings` (plan 15 phase 7d, D-132). Read-only display of `GET /api/holdings-risk`; every number comes from the Python `HoldingsRiskBuilder`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `holdings-page.tsx` | headline, risk tiles, positions by share of risk, style exposures with bars, per-stock exposure heat table, industries, model correlation heat table, notes | `HoldingsPage` |
| `holdings-format.ts` | pure helpers: CNY, shares, exposures, style / industry lists, P&L class, 盈亏% with 已回本 (D-166), headline | `yuan`, `share`, `expo`, `listStyles`, `listIndustries`, `pnlClass`, `pnlPct`, `holdingsHeadline` |
| `holdings-format.test.ts` | vitest TC-HRW-001..003 |  |
| `holdings-risk.fixture.json` | HoldingsRiskBuilder sample (same as the Go fixture) |  |
| `position-notes.tsx` | 持仓笔记与筹码 section: flags, stop / target, chip row, conditions and the note per position (plan 15 ph7f) | `PositionNotes` |
