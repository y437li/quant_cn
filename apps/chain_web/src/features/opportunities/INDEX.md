# apps/chain_web/src/features/opportunities/

机会清单 page at `#opportunities` (plan 21 ph5). Read-only display of `GET /api/opportunities` (opportunities.json from the Python `OpportunityDocument`).

## Files
| File | Purpose | Contains |
|---|---|---|
| `opportunities-page.tsx` | headline; listed (new, stayed) and near-miss rows with gauge, profit growth, valuation vs median, order-flow weeks, winner rate, cap, missing rule; dropped names; rule legend | `OpportunitiesPage` |
| `opportunities-format.ts` | pure helpers: rule labels, signed percent, row group, valuation text, headline | `RULE_LABEL`, `formatSignedPct`, `rowGroup`, `formatValuation`, `opportunityHeadline` |
| `opportunities-format.test.ts` | vitest TC-OPF-001..002 |  |
