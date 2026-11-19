# 29 — Capital gains overhang (CGO, 筹码浮盈) on A shares

| | |
|---|---|
| Status | ph4–5 drafted, awaiting approval (avoid flag, D-164 proposed); ph1 done, ph2–3 not triggered |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-15 |
| Notion | pending |
| Decisions | D-060, D-147 (precedent); D-164 (proposed, avoid flag) |
| Depends on plans | 04 (factor library and campaign, done), 25 (`reversal_intraday_1m` as a control) |

## Goal
We know whether our own turnover-decay chip model (Grinblatt & Han 2005 CGO) reproduces Tushare `cyq_perf` and predicts A-share returns beyond reversal, momentum, turnover and size. If it passes, `CapitalGainsOverhangFactor` is in the factor library; if not, the research run is logged and the plan stops after phase 1.

Model, per stock, daily, on the backward-adjusted price and free-float turnover V_t (`turnover_rate_f` / 100):
- chips_t(p) = chips_{t−1}(p) · (1 − α·V_t) + α·V_t · day_t(p), day_t spread over [low, high] (triangular at the VWAP, or uniform);
- reference price RP_t = Σ_n w_n · P_{t−n}, w_n ∝ V_{t−n} · Π_{τ<n}(1 − V_{t−τ}), truncated at N sessions and renormalised;
- CGO_t = (P_t − RP_t) / P_t; winner rate = share of chips below P_t.

## Scope
- In:
  - Research run: CGO and winner rate on the lake, a match against `cyq_perf`, and an IC test.
  - If it passes the bar, the factor class, its config line and a campaign run.
- Out:
  - US stocks (no US single-stock data in the lake; revisit after A shares).
  - Replacing `cyq_perf` in `ChipStructureReader` (open question, after ph1).
  - Score weights before the ph3 decision; execution; a risk-model style.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Research: reproduce and test | Run `research_space/runs/<date>_cgo/`, outputs in lake `meta/runs/research/`. (a) Match: our winner rate and median cost vs `cyq_perf` (2021+) on a 300-stock sample, per-day cross-sectional Spearman. (b) Predict: monthly rank IC of CGO for 20- and 60-session excess returns, 2019–2026, raw and net of size, `reversal_1m`, `reversal_intraday_1m`, momentum and turnover; `cyq_perf.winner_rate` tested side by side from 2021. Variants, each counted as a trial: α ∈ {1, 0.5}, N ∈ {250, 500}, close vs VWAP; plus \|CGO\| (An 2016 V-shape) | RESEARCH_LOG row and INDEX. The report states: match median Spearman (≥ 0.9 = reproduced); IC, NW t and sub-period signs per variant; net IC. Go to ph2 only if one pre-chosen variant has net 20-session NW t ≥ 3 and the same sign in the three sub-periods | — | done 2026-11-15 — bar not met: cgo_tri_a1.5 net 20d IC −0.004 (t −0.5); runs `20261115_cgo_reproduce`, `20261115_cgo_ic` |
| 2 | Factor class | `CapitalGainsOverhangFactor(name, alpha, horizon, min_obs)` in `factor/library/`, reads `prices` and `daily_basic.turnover_rate_f`; config line in `config/factors.yaml`, not in the score | Tests from `test-cases`: known answer on a fixture; zero turnover keeps RP; suspended sessions skipped; `min_obs` boundary; data after t leaves t unchanged (PIT). The value matches the ph1 script within 1e-9 on real lake stocks. Registry, INDEX, `make check` pass | 1 | todo — not triggered (ph1 bar not met) |
| 3 | Campaign and decision | Campaign run with the factor; all ph1 variants in the TrialLog; new decision on score inclusion | FACTOR_TESTING_DESIGN §6 criteria 1–3 logged with the run id; correlation with the reversal factors reported; plan 04 log line | 2 | todo — not triggered |
| 4 | Avoid flag: compute | `ChipSettings` (base.yaml `chips`: `cgo_alpha` 1.5, `cgo_sessions` 500, `cgo_avoid_pct` 0.9). `CgoReader(query, settings).read(as_of)` -> all listed stocks: `cgo` = 1 − mean cost / close (turnover-decay, last `cgo_sessions` sessions, hfq), `cgo_pct` = market percentile. `ChipStructureReader` adds `cgo`, `cgo_pct`; `Condition` chip metrics add `cgo_pct`; `PositionReviewer` adds the chip key and the flag `cgo` 浮盈过高 (全市场前 x%) at or above `cgo_avoid_pct` | Tests from `test-cases`: known answer on a fixture; zero turnover keeps the cost; suspended sessions skipped; only rows on or before as_of used; flag at the boundary. Real lake: the reader's `cgo` matches `20261115_cgo_ic` on 2026-10-30 (rank corr ≥ 0.999); a full run takes < 10 s. Registry, INDEX, `make check` pass | 1 | todo |
| 5 | Avoid flag: display | Holdings page chip column 浮盈分位 (`cgo_pct`, % format) and the flag through the existing flags list; morning report lists the flag with the other holding flags; condition label 浮盈分位 on the watchlist; Go fixtures updated | `make check` and vitest pass; `make app` smoke shows the column and a flagged row from the fixture; the real holdings page shows today's values | 4 | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `CapitalGainsOverhangFactor` | new, subclass of `BaseFactor` | `quant_cn.factor.library` | 2 |
| `FactorInputs`, `FactorFactory`, `BaseFactor` | reuse | `quant_cn.factor` | 2 |
| `FactorPreprocessor`, `IcCalculator`, `IcSignificance`, TrialLog, campaign runner | reuse | `quant_cn.statistic`, `quant_cn.factor` | 3 |
| `ChipSettings` | new | `quant_cn.core` | 4 |
| `CgoReader` | new | `quant_cn.lake` | 4 |
| `Config`, `ChipStructureReader`, `Condition`, `PositionReviewer`, `AppServiceBuilder` | extend | core, lake, portfolio, cli | 4 |
| chain_web condition-format / position-notes, chain_api fixtures | extend | apps | 5 |

## Risks
- Overlap with reversal and momentum: CGO is a weighted past-price ratio, partly the same signal. Mitigation: the bar is on IC net of the reversal factors, momentum, turnover and size.
- Vendor model unknown: a low match to `cyq_perf` does not falsify CGO; the test of record is the IC. Mitigation: report both separately.
- Start-up: a stock needs about N sessions before RP is stable. Mitigation: `min_obs`; no value for new listings.
- Variant search: 8+ trials on the same data. Mitigation: all go in the TrialLog; HLZ t ≥ 3.
- Compute: a price-bin distribution for every stock is heavy. Mitigation: CGO by recursion for all stocks; the winner-rate distribution only on the 300-stock match sample.

## Open questions
- ph4–5 (avoid flag, D-164 proposed) await approval.
- \|CGO\| net of controls: 60d IC −0.024 (t −4.4, all sub-periods), 20d t −2.3. Not the pre-chosen variant and below the 20d bar; a separate 60d test or a chip-row flag (extreme gain or loss) needs a new plan if wanted.
- If the match is ≥ 0.9, should `ChipStructureReader.winner_rate` use our own model (history before 2021, no `cyq_perf` dependency)? Decide after ph1.
- The sign is left to the data: Grinblatt-Han find a positive CGO premium in the US; in A shares the disposition effect is stronger, but CGO also overlaps short-term reversal.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-15 | 4–5 | Drafted: CGO top-decile avoid flag (user: "可以，当一个别买信号" after the long-only and short follow-ups); D-164 proposed. 500-session history ranks match the 2010 start (rank corr 1.000, top-10% overlap 100%) |
| 2026-11-15 | 1 | Done, bar not met; plan stops. CGO raw 20d IC −0.044 (t −2.6, sign opposite to the US); net −0.004 (t −0.5); rank corr −0.70 with reversal_1m. Winner rates (ours, vendor) alike. \|CGO\| net 60d −0.024 (t −4.4) left as an open question |
| 2026-11-15 | 1 | Approved (user: "ok"). 1b: N ∈ {250, 500} replaced by a ∈ {1, 1.5} (the recursion has no truncation; a is the same memory knob). Trials: cgo tri / close × a 1 / 1.5, \|CGO\|, our winner rate, vendor winner rate. Pre-chosen: cgo_tri_a1.5 |
| 2026-11-15 | 1a | Reproduction check run before approval (user: "先考虑能不能复现"), research run `20261115_cgo_reproduce`, 300 stocks 2021–2025. Best variant: triangular at VWAP, free-float turnover, a = 1.5. Winner rate: ts corr 0.94, daily cross-section Spearman 0.90 (at the 0.9 bar), MAE 7.5 pp, bias −4.2 pp. Mean cost within 1.3%, cost_50 / avg within 1.1%. Vendor grid is linear ~100 bins (step ≈ his_high / 100, min 0.1 元); backfill rows use the fetch-date qfq basis. Ranks reproduced, levels not exact |
| 2026-11-15 | all | Drafted, awaiting approval (user: "可以，写个计划，先在A股算CGO验证") |
