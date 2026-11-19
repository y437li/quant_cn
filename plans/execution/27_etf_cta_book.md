# 27 — ETF CTA book (只做多的 ETF 版 CTA)

| | |
|---|---|
| Status | approved 2026-11-14 ("每周看，2点不动，开工吧"); ph2 done; ph5 (views) done |
| Owner | user (approve) / executor (build) |
| Created | 2026-11-14 |
| Notion | pending |
| Decisions | D-160, D-157, D-159, D-162, D-163 |
| Depends on plans | 24 (A股 trend position), 15 ph7 (app page, e-mail), 26 (QDII premium, optional) |

## Goal
Every week the app and the morning e-mail show the target weights of a long-only ETF book: 60% in 股票 / 黄金 / 商品 at equal risk with trend timing on A股 (plan 24 rule), 40% in 5-year + 30-year government bonds with a trend switch (D-160 update). They also show the changes against last week and a paper track record, so the user can follow it with liquid ETFs only.

## Evidence (research, 2026-11-14)
- `research_space/runs/20261114_etf_universe/` (2020-02..2026-11, long only, 15 bp):
  - Risk budget 1:1:1:1: Sharpe 1.20, +6.9%/y, max dd −4.5%.
  - + A股 plan-24: 1.13–1.21, +6.3%, −4.3%.
  - Full (+ bond switch, no 30-year, bond cap 65%): 0.90, +5.5%, −4.3%.
  - 股40/债60: 0.27, −14%.
- What did not help:
  - Vol timing of the total (0.98–1.12).
  - VIX helpers on A股 (all worse than plan 24).
  - Trend switches on 黄金 / 商品.
  - Covariance ERC.
  - Splitting 有色 / 能源.
- Bond bears from the curve proxy (2010–): bond switch max dd −9.0% → −4.2%.
- 2014-01..2026-11 on backfilled history (D-159, commodity futures proxy before 2019-12): Sharpe ① 0.80 ② 0.79 ⑤ 0.69, +5.1%/y, max dd −5.4%, every year positive; no-bond and 60/40 股金商 / 5-year variants in `duration_return.py` (Sharpe 0.66–0.69, duration 0 / 1.8).
- Split sweep (`split_sweep.py`): Sharpe 0.66–0.70 for 100/0 … 30/70; return scales with risk.
- Bond sleeve (`bond_mix.py`, bond ETFs before listing from the curve): chosen 60/40 with 5y + 30y equal capital, +7.6%/y, Sharpe 0.84, max dd −7.5%, no losing year 2014–2026, full-weight duration 4.7. 30y yield 4.7% (2014) → 2.06% now, so the long-end gain is not expected to repeat.
- 30y yield spikes 2010–: worst week +36 bp, worst month +51 bp; a rise above 30 bp within a month 1.1% of the time.

## Scope
- In:
  - Groups and ETFs in `config/etf_cta.yaml`:
    - 风险资产 60% of capital, risk weights 1:1:1 across:
      - 股票: 510300 / 510500 / 512100 / 159915 : 159920 / 513050 / 513130 = 2 : 1.
    - 债券 40% of capital: 511010 (5y) and 511090 (30y), equal capital.
    - 黄金: 518880.
    - 商品: 159980 / 159981 / 161129 (原油: 易方达 161129, user's pick 2026-11-14; no exchange ETF tracks crude, oil-stock ETFs rejected).
    - Cash: 511880.
  - Vol window 60, monthly risk weights inside 风险资产; weekly overlays: A股 plan-24 position and the bond trend switch (21/63/252 on the bond sleeve NAV); a no-trade band. Freed weight to 511880.
  - Each Friday after the close: target weights per ETF, change against last week, a group summary, and the signals behind it (group vol, A股 blend and size, bond switch).
  - A paper book from a start date (costs 15 bp), with history and drawdown.
  - Flags: a group weight change of 5 points or more; the bond switch turning; the A股 position stepping.
  - QDII / LOF premium guard (161129 first): buy or add only below 3% premium; at 10% or more no adds, hold until the next rebalance; flag when above 20% (501018 as the lower-premium alternative). Plan 26 data.
- Out:
  - Orders, broker links, sizing to the user's account (weights only).
  - Futures, shorting, leverage.
  - Phone alerts (the recipient is 妈妈, A股 focus), unless asked.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Long backtest | Re-run `full_scheme.py` from 2013 with the backfilled ETFs (commodity proxy from main futures before 2019-12) and pick the variant (② A股 only vs ⑤ full) with the user | Report by year 2013–2026, the two bond bears, 2015, 2018; user picks the variant and parameters | — | done (60/40 股金商 + 5y/30y; `bond_mix.py`) |
| 2 | Weights | `core.EtfCtaSettings` (config/etf_cta.yaml); `calculation.TrendPosition` (plan 24 rule, shared); `portfolio.EtfCtaWeights`, `EtfCtaPaperBook`, `EtfCtaBook` (curated fund_daily / fund_nav → group vol, risk weights, overlays, targets, held, trades, flags, premium guard, back-test and paper book); `make etf-cta` writes `etf_cta.json` | TCs on hand price paths (risk weights ∝ 1/vol, 60/40 split, monthly hold, overlays, band, flags once, paper book costs); real lake reproduces `bond_mix.py` 60/40 5y+30y for 2020–2026 within 0.05 Sharpe; `make check` green | 1 | done (2026-11-14: make check green, 859 passed, 0 lint findings; 2020-02..2026-11 Sharpe 0.88 vs research 0.87) |
| 5 | Views (观点倍数) | `core.EtfCtaViews` reads git-ignored `config/local.etf_cta_views.yaml` (`views_file` in etf_cta.yaml): (1) scale a group, subset (A股 / 港股 / 5年 / 30年) or ETF by 0.5–2 (inside a group: group total kept), (2) relative: move ≤ 5 points from one set to another, (3) optional price condition (ETF close below / above, latches once met); each view has reason, start, expiry ≤ 92 days; optional A股 floor. `portfolio.EtfCtaViewTilt` applies them; `EtfCtaBook` writes the 含观点 track (rows, paper record, view statuses, group effect) beside 系统; `portfolio.EtfCtaRecord` takes the record maths out of the book (size limit) | TCs: no file = no views; bounds, expiry > 92 days, unknown target rejected; expired view ignored and flagged; subset scale keeps the group total; relative moves capped by the source and skipped into a zero target; condition waits then latches; per-ETF combined multiplier clipped 0.5–2; total ≤ 100%; floor lifts A股 only below it; tracks equal with no views; `make check` green | 2 | done (2026-11-14: make check green, 880 passed, lint 0; real lake: no views = identical tracks; demo 黄金 ×0.7, 股票 ×1.5, 港股 over A股 3 points, floor 0.3 → 股票 9.4% → 16.5%, 黄金 20.6% → 14.4%) |
| 3 | Display | E-mail section rows; app page (weights table, changes, group pie, paper NAV and drawdown); "研究信号，不构成交易建议"; shows both tracks and the live views | `go test`, vitest, smoke opens the page; e-mail renders; `make check` green | 2, 5 | todo |
| 4 | Live check | Paper book reviewed after 3 months against the backtest | Plan log row with the live record | 3 | todo |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `EtfCtaSettings` (+ group model) | new (pydantic) | core | 2 |
| `EtfCtaBook` | new | portfolio | 2 |
| `TrendPosition` | new (plan 24's `IndexTrendSignal` reuses it) | calculation | 2 |
| `EtfCtaWeights`, `EtfCtaPaperBook` | new | portfolio | 2 |
| `EtfCtaViews` (+ view model) | new (pydantic) | core | 5 |
| `EtfCtaViewTilt` | new | portfolio | 5 |
| `EtfCtaBook` | extend (two tracks, views block) | portfolio | 5 |
| report section, Go store, React page | new / extend | visualization, apps | 3 |

## Risks
- Regime dependence: the 2020–26 results ride bond and gold bull markets. Phase 1 tests 2013– before anything is built; expectations stated as 3–5%/y, −5..−8% drawdown.
- Rates: 40% bonds with 30y in the sleeve, duration up to 4.7 when the switch is fully on; a fast rise beats the weekly switch (worst month +51 bp ≈ −2% on the book).
- Overfitting: parameters come from earlier research and are not tuned here. Variants shown side by side, paper book before any reliance; tuned parameters lost out of sample (D-162). Views are bounded 0.5–2× with an expiry ≤ 92 days, and the system track is always shown beside the views track.
- QDII / LOF premiums (原油 LOF, 港股 QDII): guarded by the plan 26 premium check.
- Shared files: e-mail and app files belong to the uncommitted plan 15 ph7 work; nothing is committed until the user decides the repo history.

## Open questions
- Premium thresholds 3% / 10% as proposed?
- Paper book: starts 2026-11-13 in weights only (default taken); a 元 amount for lot rounding?
- Add US QDII (纳指 / 标普) when their premium is below 3%?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-14 | — | Drafted (user: "不看了，我们自己做"; choices "只做多的 ETF 版 CTA", "风险预算，只在A股择时呢") |
| 2026-11-14 | 1 | Long backtest done (2014-01..2026-11); user worried about duration ("利率反弹久期会很惨"), split sweep added; oil stays as 易方达 161129 with premium guard (user: "易方达") |
| 2026-11-14 | 1 | Done: 60/40, bonds 5y + 30y equal capital with switch (user: "可以，就按60/40定"); D-160 updated, still proposed until build approval |
| 2026-11-14 | 2 | Approved ("每周看，2点不动，开工吧"); band applied per group (a 1% A股 ETF is bought when its group is 2 points off); back-test record from 2020-04 (commodity ETFs list 2020-01; the 2014– research used futures proxies); `make etf-cta` in track-daily |
| 2026-11-14 | 2 | Done: make check green (859 passed, lint 0) |
| 2026-11-14 | — | D-162: Optuna (dev group, research only) walk-forward 2018..2026: tuned OOS Sharpe 0.88 / 0.85 vs base 0.91; parameters unchanged, vol window 120 noted for the ph4 review (`20261114_etf_tuning`) |
| 2026-11-14 | 5 | Drafted views phase (user: "我可以根据我的view来调整他们的weight吗", "ok" to multiplier method + keep A股 timing, "好，写观点倍数的计划吧"); D-163 proposed |
| 2026-11-14 | 5 | Approved with view kinds 1 scale, 2 relative, 3 price condition (user: "可以，按1、2、3类做，开工吧"); multipliers act on final weights (recommended default, no objection); D-163 accepted |
| 2026-11-14 | 5 | Done: `EtfCtaViews` / `EtfCtaWhen` / `EtfCtaView` (core), `EtfCtaViewTilt`, `EtfCtaRecord` (portfolio, record maths moved out of the book for the size limit); `subsets` and `views_file` in etf_cta.yaml; template `config/local.etf_cta_views.yaml` (git-ignored, no views); make check green (880 passed) |
