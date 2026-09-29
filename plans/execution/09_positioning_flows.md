# 09 — Positioning and forced flows (CSI 300 first)

| | |
|---|---|
| Status | approved 2026-09-28 (confirmed here); doing — phase 1 downloads and phase 2–4 code in progress (quant-cn-b7) |
| Owner | user (confirm) / executor (build) |
| Created | 2026-09-28 |
| Notion | pending |
| Decisions | D-057, D-058, D-059 |
| Depends on plans | 03 (chains, Black-76, rates); datasets in phase 1 |

## Goal
Daily estimates of option dealer gamma exposure and gamma-flip level, index-futures positioning and basis,
and a margin-liquidation ladder for the CSI 300, as lake frames and a notebook with results; validated later
by an event study before any of them is called a signal.

## Scope
- In: `GammaExposureCalculator`, `FuturesPositioning`, `MarginLadderEstimator`, `Black76Model.compute_gamma`; datasets `fut_daily`, `fut_holding`, `fut_basic`, `margin`, `margin_detail`; frames `GEX_PANEL`, `FUTURES_POSITIONING`, `MARGIN_LADDER`, `MARGIN_VINTAGES`; notebook `20260929_positioning_flows.ipynb` with outputs (D-051 pattern); event-study validation.
- Out: intraday positioning, single-stock options, using the levels as trading signals before validation.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Data | five datasets configured and pulled (futures from 2025-01, margin from 2025-01, margin_detail from 2024-01); curated schemas | live pulls land; `fut_holding` top-20 long/short shown as a coverage share of `fut_daily` total OI per product (stable, well below 100% by construction); `margin_detail` Σrzye vs SSE+SZSE `margin` aggregate reported as a daily gap % (target within 2%) | 03 ph1 | doing (downloads running) |
| 2 | Gamma exposure | `Black76Model.compute_gamma`, `GammaExposureCalculator`, `GEX_PANEL`, gamma-flip per day | synthetic chain: Γ matches closed form to 1e-8; flat-IV chain has flip at spot; live IO + ETF chains computed for the sample; signed and unsigned GEX stored | 1 | todo |
| 3 | Futures positioning | `FuturesPositioning`, `FUTURES_POSITIONING` (regimes, net top-20, concentration, annualised basis) | regimes assigned every contract-day; basis matches manual check on 3 days; front/next roll continuous | 1 | todo |
| 4 | Margin ladder | `MarginLadderEstimator` (FIFO vintages, liquidation prices, drawdown ladder), `MARGIN_LADDER`, `MARGIN_VINTAGES` | synthetic vintage test (open, partial repay, full repay) exact; ladder monotone in drawdown; CSI 300 and market scopes computed for the sample | 1 | todo |
| 5 | Notebook | `research_space/notebooks/20260929_positioning_flows.ipynb` calling the package; charts for GEX by strike with flip, futures regimes and basis, ladder vs drawdown; outputs committed | runs top to bottom; every assumption printed with its parameter | 2–4 | todo |
| 6 | Validation | event study (§4 of the design): crossings of high-put-OI strikes, gamma flip, ladder steps vs next-1/3/5 abs return and realised vol; sub-period split | report with confidence intervals; decision recorded on which levels (if any) qualify as signals | 5 | todo |

## Classes

| Class | Action | Package | Phase | Used by (planned) |
|---|---|---|---|---|
| `Black76Model.compute_gamma` | extend | calculation | 2 | `GammaExposureCalculator` |
| `GammaExposureCalculator` | new (`BaseCalculation`) | calculation | 2 | notebook; later `CalculationStep` |
| `FuturesPositioning` | new (`BaseCalculation`) | calculation | 3 | notebook; later `CalculationStep`, ETF pairs basis (ETF_PAIRS_DESIGN) |
| `MarginLadderEstimator` | new (`BaseCalculation`) | calculation | 4 | notebook; later risk conditioning |
| `GEX_PANEL`, `FUTURES_POSITIONING`, `MARGIN_LADDER`, `MARGIN_VINTAGES` | new schemas | core.frames | 2–4 | producers above, notebook, `SeriesChart` |
| `EventStudy` | new | statistic | 6 | validation notebook; reusable by plan 07 event factors |

## Risks
- Dealer-sign assumption may be wrong for A-share ETF options where retail sells puts; the sign is a parameter and OI changes are shown, but a wrong default misplaces the flip.
- `fut_holding` covers top-20 brokers only and mixes client and proprietary books; treat as gross aggregate (D-059).
- Margin parameters differ by broker and over time; a single (1.3, 1.0) pair misplaces individual liquidation prices, though the aggregate ladder is less sensitive. Sensitivity table required in the notebook.
- `margin_detail` since 2024-01 only: the event study has few stress episodes; extend to 2019 if phase 6 needs it.
- Lake write contention: downloads for this plan block `make check` and queries while running.

## Open questions
See POSITIONING_FLOWS_DESIGN §6 (dealer sign, margin parameter mixture, feeding regimes downstream).

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-28 | 1–5 | Executor: frames GEX_PANEL / FUTURES_POSITIONING / MARGIN_LADDER / MARGIN_VINTAGES registered and validated by producers; `PrefectRunner` built and chosen by the user (D-064); `make doctor` trade_cal horizon warning (<90 d); `ServiceBuilder` split from `QuantCnCli` (size limit); margin_detail download finishing, then curate via Prefect, notebook commit, make check, report_rc tier check |
| 2026-09-28 | — | Approval confirmed by user in this session ("approve") |
| 2026-09-28 | 1–2 | Executor report: package code written (GammaExposureCalculator, FuturesPositioning, MarginLadderEstimator, Black76Model.compute_gamma; 39 calculation tests, mypy/ruff clean, uncommitted); notebook section 0 does the phase-1 reconciliation; fut_daily 422/422 pulled, fut_holding / margin / margin_detail in progress. Phase-1 criterion reworded: top-20 vs total OI is a coverage share, not an equality. Frames GEX_PANEL / FUTURES_POSITIONING / MARGIN_LADDER / MARGIN_VINTAGES to be registered in core.frames before the phase-2 commit |
| 2026-09-28 | — | Drafted at quant-cn-b7's request after the user approved the idea in that session; phase 1 downloads already running there |
