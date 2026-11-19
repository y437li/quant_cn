# 36 — Linear-pricing gap factor (线性定价差)

| | |
|---|---|
| Status | done 2026-11-18 (ph1–4); pricing_gap failed criteria 1–2 and stays in the score by the user's choice, to be watched |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-18 |
| Notion | pending |
| Decisions | D-173, D-093 (Shenwan L1 + log mcap neutralisation), D-092, D-147 (precedent) |
| Depends on plans | 04 (factor library and campaign, done) |

## Goal
The factor library has `pricing_gap`: log(market cap ÷ value from consensus FY1–FY3 with fading growth). It is evaluated by the plan 04 campaign on its usual basis: equal weight, Shenwan L1 + log market cap neutral. If it passes, its dearest decile becomes a veto in the watchlist and the opportunity list.

Evidence (research run `20261118_linear_pricing_gap`, 95 month ends 2019–2026, about 1,950 covered stocks a month):
- **Rank IC:** 20-day IC −0.053 (NW t −3.3). Net of forward EP, trailing EP, growth, size, reversal, momentum and turnover: FM t −3.7. At 60 days the net FM t is −2.7.
- **Long-short, equal weight, 10% legs, net of costs:**

  | Neutralisation | Annual return | Sharpe | Max drawdown |
  |---|---|---|---|
  | None | 10.1% | 0.54 | — |
  | Industry | 12.0% | 0.93 | −10% |
  | Industry + size | 10.4% | 0.86 | −12% |

  Industry + size is the most even across years: no year below −2.1%.
- **Large caps (top 40%):** industry + size, equal weight, 6.5% net. Avoiding the dearest 10% works (−0.97% a month, t −2.6); buying the cheapest 10% does not (−0.12%).
- **Second conditions** (40 tested, none at t ≥ 3):
  - dear + 20-day rally top 20%: −1.25% over 20 days (t −2.3);
  - cheap + momentum not in the bottom 20%: +2.6% over 60 days (t 2.3).

## Scope
- In:
  - **Consensus panel:** for every session date the factor needs, the FY1 / FY2 / FY3 median net-profit forecast. Built from report_rc point in time: report_date ≤ date, trailing 90 days, latest per broker.
  - **Factor:** a new factor class with parameters in config: fade 0.7, 7 fade years, exit PE 15, discount 9%, FY3 fill, growth clip [−0.3, 1.0]. Value_raw = gap (higher = dearer, so the factor sign is −).
  - **Campaign:** a run with equal-weight deciles and the standard neutralisation. All research variants are counted in TrialLog: 2 parameter sets, 3 neutralisations, 2 weightings, and 40 rule tests count as 1 family. A large-cap (top 40%) subset report is added to the run.
  - **Use:** in the composite score at weight 1 (user 2026-11-18, "可以，加进综合打分"; was a veto in the draft).
- Out:
  - A long-short book: the user is long-only and A-share shorting is impractical.
  - Cheap-side buy signals for large caps: no edge there.
  - Forward EP as its own factor. FACTOR_LIBRARY lists it; the consensus panel makes it cheap to add later.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Consensus panel | `ConsensusPanelBuilder` (FY1 = as-of year from May, else year before; FY1–FY3 medians, broker count; 90-day window, latest per broker); `FactorInputs.consensus` loaded by `FactorFactory` only when a factor declares it | TCs (window edges, broker dedup, FY roll in May, PIT: a report dated after t is invisible); month-end values equal the research panel's f1 / f2 for 3 spot-checked stock-months | — | done 2026-11-18 — `ConsensusPanelBuilder` (TC-CNS-001..003); notes visible from the session after report_date (report_rc next_session), so stricter than the research (≤ date); `FactorInputs.consensus`, `BaseFactor.consensus_days`, `FactorFactory` month ends from 40 days before the start (TC-FAF-004); 95 month ends in 1.2 s |
| 2 | Factor class | `PricingGapFactor` (BaseFactor) reads consensus + daily_basic.total_mv; config line `pricing_gap` in `config/factors.yaml` (not in score weights) | TCs: known answer on a 3-year fixture, FY3 fill, FY1 or FY2 ≤ 0 → NaN, growth clip, PIT restatement test; raw 20-day IC on month ends within ±0.01 of the research −0.053; registry, `factor/library/INDEX.md`; `make check` passes | 1 | done 2026-11-18 — `PricingGapFactor` (TC-LPG-001..003), value_raw = −gap (higher = cheaper); month-end 20-day rank IC +0.0531 (t 3.32, 93 months) vs research −0.0533; correlation with the research gap −0.996; make check 1,070 passed |
| 3 | Campaign evaluation | Campaign run including `pricing_gap`; TrialLog with the research variants; report IC / ICIR / NW t per horizon, sub-periods, Romano-Wolf, equal-weight LS Sharpe, decay, correlation with `ep_ttm`, large-cap subset | FACTOR_TESTING_DESIGN §6 criteria evaluated and logged with the run id; D-173 updated to accepted / rejected | 2 | done 2026-11-18 — runs 41c88117ae05 / 5f65090ede53: pricing_gap 20-day IC 0.0266, NW t 1.55, BHY p 0.71, sub-periods t 0.61 / 1.80 / 0.98 → fails criteria 1, 2 (month-end-sampled t 4.04 overstated by IC autocorrelation); TrialLog 60 → 72 with the 12 research variants |
| 4 | Score | `pricing_gap` in the campaign weights at 1.0 (user 2026-11-18); `derived/features` rebuilt; the campaign rerun reports the new score against the old. The watchlist veto is dropped: inside the score's top quintile the dearest 10% are ~20 of 480 names a month and removing them adds 0.12%/yr (t 0.58, run `20261118_pricing_gap_complement`) | new score 20-day IC and decile LS Sharpe reported against the old score; `make check` passes | 3 | done 2026-11-18 — score 20-day IC 0.0679 → 0.0691, NW t 4.01 → 4.02, LS Sharpe 1.20 → 1.19; 60-day IC 0.0832 → 0.0847. Kept at weight 1 (user: "放进去吧，当个指标看一看") |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `ConsensusPanelBuilder` | new | calculation | 1 |
| `FactorInputs`, `FactorFactory` | extend (consensus panel) | factor | 1 |
| `PricingGapFactor` | new (BaseFactor) | factor.library | 2 |
| `Neutralizer`, `FactorPreprocessor`, `IcCalculator`, `IcSignificance`, TrialLog, campaign runner | reuse | statistic, factor | 3 |
| config/factors.yaml `campaign.weights`, `FeatureStep` | reuse (weights) | config, pipeline | 4 |

## Risks
- **Selection:** many variants were tried on the same 2019–2026 data. All are counted in the TrialLog. The net t (3.7 at 20 days) is close to the HLZ bar.
- **Edge in small and mid caps:** cap-weighted large caps give 3.4% net. The use is a veto, not a book. The large-cap subset is reported, not hidden.
- **Consensus is stale or optimistic at cyclical peaks:** the cheapest names now (AI hardware, memory) are cheap only if consensus holds. The dossier shows the consensus path and the revision so the reader can judge it.
- **Coverage:** only names with FY1 and FY2 forecasts, about 1,950 a month. The others get NaN, not a value.
- **report_rc volume:** 2.4M rows. The panel is built once per run on month ends plus the as-of date, not per session.

## Open questions
- (none; weighting is equal weight per the user on 2026-11-18, "等权"; neutralisation is the campaign standard, Shenwan L1 + log mcap, D-093)

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-18 | 3–4 | done. Campaign verdict fail (t 1.55); the score barely moves with it. Recommended revert; user kept it in the score as an indicator to watch ("放进去吧，当个指标看一看"). Also found: dividend_yield is t 2.53 under the current campaign (criteria 1–2 fail), although in the score since D-147 |
| 2026-11-18 | 4 | scope changed (user: "可以，加进综合打分" after run 20261118_pricing_gap_complement: score + pricing_gap LS Sharpe 0.75 → 0.98, large caps 0.50 → 0.71; veto alone +0.12%/yr): ph4 is score inclusion, the watchlist veto is dropped |
| 2026-11-18 | 1–2 | done. Consensus on month-end sessions carried to sessions (merge as-of); TC prefixes TC-CNS (TC-CPB taken by CompanyPeriodBuilder) and TC-LPG (TC-PGF taken by ProfitGrowthFactor); factor sign flipped to the library's higher-is-better |
| 2026-11-18 | — | approved (user: "可以") |
| 2026-11-18 | — | drafted from research run 20261118_linear_pricing_gap (user: "等权" after the neutralisation comparison) |
