# 25 — Intraday high-turnover reversal factor (日内放量反转因子)

| | |
|---|---|
| Status | doing 2026-11-14 — phase 1 done, phase 2 next |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-14 |
| Notion | pending |
| Decisions | D-060, D-093, D-095, D-147 (precedent); D-156 (to be written in ph3) |
| Depends on plans | 04 (factor library and campaign, done) |

## Goal
The factor library has `reversal_intraday_1m`: minus the sum of intraday returns (open → close) on the 10 highest-turnover sessions of the last 21. It is tested by the plan 04 campaign. On that evidence it either replaces `reversal_1m` in the score or stays a single factor.

Evidence (research run `20261114_reversal_variants`):
- 20-day rank IC 0.076 (t 6.3) vs `reversal_1m` 0.046 (t 4.4).
- Net of `reversal_1m`, size and turnover: 0.045 (t 5.6). 60-day IC 0.091. Both sub-periods hold.
- The overnight part of the monthly return is momentum, not reversal (IC −0.031). This is why `reversal_1m`, which mixes the two, is weaker.

## Scope
- In:
  - New factor class, its config line and tests.
  - A campaign run with the new factor, judged on FACTOR_TESTING_DESIGN §6 criteria 1–3. The 8 research variants count as trials.
  - Comparison with `reversal_1m`; score weights updated by decision.
  - `derived/features` rebuilt.
- Out:
  - An overnight-momentum factor (IC −0.031 as reversal; weaker, a separate test later).
  - A minute-bar version (research run `20261113_minute_factors` showed no gain on 18 months).
  - A risk-model style for it.
  - Execution timing (plan 06).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Factor class | `IntradayReversalFactor(name, window=21, top_k=10, min_obs=15)` subclasses `ReversalFactor` (reuses the window check and `lookback`). It reads `prices` (open, close) and `daily_basic.turnover_rate_f`. value_raw = −Σ ln(close/open) over the `top_k` highest-turnover traded sessions in the window; NaN if fewer than `min_obs` traded sessions. Config line `reversal_intraday_1m` in `config/factors.yaml`, not yet in the score weights | Tests derived with `test-cases`: known answer on a 21-session fixture; ties in turnover broken by date; suspended sessions skipped; `min_obs` boundary; changing prices or turnover after t leaves t unchanged (PIT). Registry row and block, `factor/library/INDEX.md`; `make check` passes | — | todo |
| 2 | Campaign evaluation | Campaign run with the 8 factors. TrialLog records the new factor plus the 7 other research variants as trials. Report: IC / ICIR / NW t per horizon, sub-periods, Romano-Wolf, LS Sharpe, decay, correlation with `reversal_1m`, IC net of `reversal_1m` | Criteria 1–3 of FACTOR_TESTING_DESIGN §6 evaluated and logged with the run id. The raw-signal 20-day IC agrees with the research run within ±0.01 before preprocessing; any larger gap is explained | 1 | todo |
| 3 | Score decision and rebuild | Decision D-156 records the score outcome. If the new factor passes and beats `reversal_1m` on ICIR and LS Sharpe, it replaces `reversal_1m` in the weights; `reversal_1m` stays in the campaign as a single factor, as `ep_ttm` did under D-147. Otherwise the weights are unchanged. `derived/features` is rebuilt | The new score's 20-day ICIR and LS Sharpe are reported against the old score. The app shows the factor's name in Chinese, as done for dividend_yield. `make check` passes; plan 04 log has a line pointing here | 2 | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `IntradayReversalFactor` | new, subclass of `ReversalFactor` | `quant_cn.factor.library` | 1 |
| `FactorInputs`, `FactorFactory`, `BaseFactor` | reuse | `quant_cn.factor` | 1 |
| `FactorPreprocessor`, `IcCalculator`, `IcSignificance`, TrialLog, campaign runner | reuse | `quant_cn.statistic`, `quant_cn.factor` | 2 |
| `FeatureStep` | reuse | `quant_cn.pipeline` | 3 |

## Risks
- Selection: 8 variants were tried on the same 2019–2026 data. Mitigation: all 8 are counted in the TrialLog; HLZ t ≥ 3 applies; the research t is 6.3.
- Deeper worst month (decile spread −18.7% vs −13.5%). Mitigation: report the drawdown; the score blends six factors.
- Turnover fill: `turnover_rate_f` missing on some sessions. Mitigation: rank only sessions where it is present, and use `min_obs`.
- Correlation 0.70 with `reversal_1m`. Holding both would double the reversal weight in the score; ph3 chooses one.

## Open questions
- Resolved 2026-11-14 (user: "ok"): replace `reversal_1m` in the score if ph2 passes, following the D-147 precedent.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-14 | 1 | Done. `IntradayReversalFactor` in `factor/library/intraday_reversal_factor.py`, config `reversal_intraday_1m` (not in the score). Real-lake check: 49 stocks on 20260930 match the research formula to 6e-17. `ReversalFactor.inputs` got a ClassVar annotation so the subclass can widen it (type-only). `test_tc_c_012_factors` now expects 8 factors |
| 2026-11-14 | all | Approved with the replace default (user: "ok"); waiting for "start phase 1" |
| 2026-11-14 | all | Drafted, awaiting approval (user: "可以加一下吧" after research run 20261114_reversal_variants) |
