# 37 — Analyst descriptors in the risk model (远期 EP 与预期增长)

| | |
|---|---|
| Status | done 2026-11-18 (ph1–3); cne5_v4 adopted (user: "新版") |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-18 |
| Notion | pending |
| Decisions | D-127 (CNE5 model), D-148 (current version), D-180 (gate outcome, adopted) |
| Depends on plans | 05 (risk model), 36 (ConsensusPanelBuilder) |

## Goal
The risk model's Earnings Yield and Growth styles use the CNE5 analyst descriptors they lack today:
- EPFWD: forecast 12-month earnings / price;
- EGRSF: short-term forecast growth;
- EGRLF: long-term forecast growth.

They are adopted only if the plan 05 gate shows the model fits and forecasts at least as well.

## Scope
- In:
  - **Descriptors**, from the consensus panel (plan 36; month-end readings carried to sessions, notes visible from the next session):
    - EPFWD = 12-month forward earnings / market value. The forward earnings are FY1 and FY2 blended by the months left in FY1.
    - EGRSF = FY2 / FY1 − 1.
    - EGRLF = (FY3 / FY1)^(1/2) − 1, the longest horizon the consensus covers.
    - A stock without a consensus gets no analyst descriptor. Its style weights are renormalised over the descriptors it has, as CNE5 does and as `FundamentalDescriptors` already does.
  - **Style weights (CNE5, RISK_FACTOR_LIST §1)**:
    - Earnings Yield: EPFWD 0.68, CETOP 0.21, ETOP 0.11.
    - Growth: EGRLF 0.18, EGRSF 0.11, EGRO 0.24, SGRO 0.47.
  - **Gate**: a candidate fit `cne5_v4` against the current `cne5_v3_dy` on the same dates.
- Out:
  - The RetailGauge as a style. It is plan 21 phase 6, after the gauge is productionised.
  - Analyst dividend forecasts (DPIBS).
  - Any change to the composite score.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Analyst descriptors | `AnalystDescriptors` (risk): EPFWD, EGRSF, EGRLF per session from `ConsensusPanelBuilder` month ends (merge as-of); wired into `DescriptorBuilder` | TCs: known answer on a fixture consensus; FY1 / FY2 blend across the May roll; non-positive FY1 → no EGRSF / EGRLF; a note dated after t is invisible (PIT); coverage report: share of the estimation universe (by circ_mv weight) with each descriptor per year | 36 | done 2026-11-18 — `AnalystDescriptors` (TC-AND-001..003), RiskInputs.consensus, RiskInputLoader (TC-RIL-004), DescriptorBuilder columns (TC-DB-007), RiskModelSettings.consensus_days (0 = off); coverage by circ_mv weight 83.9% (2019) → 94.0% (2026-11) for EPFWD, 81.0% → 89.1% for EGRLF (run 20261118_analyst_coverage); make check 1,075 passed |
| 2 | Gate | Candidate config `cne5_v4` fitted next to `cne5_v3_dy`. The comparison report shows: <br>• cross-sectional R²; <br>• share of days with \|t\| > 2 for Earnings Yield and Growth; <br>• bias statistics on the 100 random portfolios and the CSI 300 / 500 / 1000 benchmarks (plan 05 ph5); <br>• the score's style-residual IC (run 20261118_score_vs_barra method) | report logged with run ids; adopt only if bias does not worsen (random-portfolio mean bias within ±0.02 of the current) and R² does not fall; the decision is written either way | 1 | done 2026-11-18 — run f39696bd936d (cne5_v4) vs cne5_v3_dy, report `research_space/runs/20261118_risk_v4_gate`: adj R² 0.2745 → 0.2744 (last year 0.3039 → 0.3038); random portfolios in band 100% both, median bias 1.026 → 1.026; CSI 300 / 500 / 1000 bias 0.927 / 1.087 / 1.051 → 0.926 / 1.086 / 1.050; Earnings Yield factor bias 1.032 → 1.062, Growth 1.007 → 1.000; \|t\| > 2 share 0.43 / 0.44; score style-residual IC20 0.020 (t 4.4), large caps 0.001. Passes (bias within ±0.02, R² flat within 0.0001); no material gain |
| 3 | Adopt | If the gate passes: `config/risk_model.yaml` becomes `cne5_v4`, the model is refit, and the holdings risk page and morning report carry the new styles' exposures (names unchanged) | `make risk-model` and `make check` pass; holdings_risk.json rebuilt; RISK_FACTOR_LIST rows marked ok | 2 | done 2026-11-18 — config name cne5_v4 (D-180); derived/risk_* from run f39696bd936d; holdings_risk.json rebuilt (11 positions, as of 20261117); RISK_FACTOR_LIST EPFWD / EGRSF / EGRLF ok |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `AnalystDescriptors` | new | risk | 1 |
| `ConsensusPanelBuilder` | reuse | calculation | 1 |
| `DescriptorBuilder`, `StyleBuilder` / risk model step, validation report | extend / reuse | risk, pipeline | 1–3 |
| `RiskModelSettings` | reuse (config only) | core | 3 |

## Risks
- **Coverage.** About 2,000–2,900 stocks have a consensus; the rest rely on renormalised weights. Small caps then carry trailing-only Earnings Yield and Growth, as today.
- **Stale consensus.** The tech crash showed analyst forecasts lagging prices. A stale EPFWD mislabels a stock's Earnings Yield exposure until brokers revise.
- **Monthly refresh.** Exposures jump at month ends. The gate checks whether the bias statistics care.
- **History.** report_rc is dense from 2019, so the gate covers the whole risk-model window.

## Open questions
- (none; weights are CNE5's, horizons follow the consensus panel)

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-18 | 2–3 | done. Gate neutral (R² flat, bias marginally better, Earnings Yield factor bias 1.03 → 1.06); agent recommended adoption for CNE5 completeness; user: "新版". D-180 |
| 2026-11-18 | 1 | done (see table) |
| 2026-11-18 | — | approved (user: "可以") |
| 2026-11-18 | — | drafted (user: "把远期EP和预期增长散户温度计加入模型？"); the gauge part is plan 21 phase 6 |
