# apps/chain_web/src/features/company/

Company dossier.

## Files
| File | Purpose | Contains |
|---|---|---|
| `company-dossier.tsx` | header and the ten tabs | `CompanyDossier` |
| `tabs-basic.tsx` | overview, products, customers, suppliers, evidence |  |
| `tabs-more.tsx` | peers, chain, quarterly |  |
| `tab-valuation.tsx` | 估值与指标: synthesized views, statistics, sector KPIs, reports | `ValuationTab` |
| `tab-business.tsx` | 商业模式: archetype, drivers, lifecycle, cycle clocks, moat numbers | `BusinessTab` |
| `broker.tsx` | broker statistics line and synthesized view card | `BrokerStatLine`, `BrokerViewCard` |
| `financial-table.tsx` | FY2023–FY2025 income statement with expense ratios (D-117) | `FinancialTable` |
| `quarterly-table.tsx` | last 8 single quarters: revenue, margins, expense ratios, YoY | `QuarterlyTable` |
| `dupont-chart.tsx` | DuPont plane (asset turnover × ROE) path over L3 peers, SVG | `DupontChart` |
| `pricing-card.tsx` | pricing power with signal votes, posterior archetype check, DeepSeek variant / pricing reading (D-118) | `PricingCard` |
| `moat-card.tsx` | moat width and trend from ROIC, claimed advantages tested against numbers (§4.4) | `MoatCard` |
