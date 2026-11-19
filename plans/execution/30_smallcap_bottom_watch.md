# 30 — Small-cap bottom watch (小盘抄底观察)

| | |
|---|---|
| Status | approved 2026-11-17 (user: "可以"); ph1, ph2 done; ph3 todo (optional); ph4 融资余额 done 2026-11-19 |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-17 |
| Notion | pending |
| Decisions | D-152, D-153 |
| Depends on plans | 03 ph6 (volatility monitor), 15 ph7e (morning e-mail), 22 (phone alerts, optional) |

## Goal
Every trading day, the morning e-mail and the app's 波动率监测 page show one 小盘观察 table. It holds the signals the user is waiting on before buying 512100 (中证1000) or 科创50, with triggered rows in red.

## Evidence (research runs, 2026-11-16 / 17)
- `20261116_market_regime/bottom_signals_bt.py`:
  - panic day (≥ 500 limit-downs) → 中证1000 20-day return 7/7 positive, mean +13%;
  - low-volume ("drought") signal → mean −1.7%.
- `20261116_market_regime/breadth_thrust_bt.py`: breadth confirmations are weak (+1.5..+2.8% over 20 days).
- `20261116_vix_divergence/exit_rules.py`: after the 1000−300 realised-vol gap ≥ 90th pct, 中证1000 beats 300 by +1.5% over 20 days (11/15). Exit when the gap falls below the 70th pct (≈ 11) or after 60 sessions.
- 2026-11-16/17 broad-ETF flows: about 3,500亿 net inflow since 10-15, mostly 沪深300; 512100 only +2亿 on 11-16.
- `20261118_marginal_trader/margin_turn_bt.py` (2019-01 → 2026-11, financing balance = Σ margin_detail rzye):
  - balance ≥ 10% below its 250-day high and its 5-day change turning ≥ 0 → 12 events, 中证1000 60-day +7.4% (hit 80%) vs +1.7% unconditional;
  - but in 2026 it fired on 08-06 and 09-18 and both failed (−13.7% over 60 days); today the balance is 26.8% below its high, the deepest since 2019, and still falling (10-day −2.7%).
- User rules (memory `smallcap-entry-watch`, 2026-11-17): main tranche on a panic day, or at 中证1000 6,075 and then 5,500.

## Scope
- In (per day, all thresholds in `config/smallcap_watch.yaml`):
  - Market panic:
    - limit-down count (daily vs stk_limit);
    - share of stocks at a 60-day low;
    - share above MA20.
  - Index levels: 中证1000 level vs the user's levels (6,075 / 5,500) and its distance; drawdown from the 2026 high.
  - Volatility:
    - 中证1000 20-day realised vol and its 3-year pct (90th-pct line);
    - 1000−300 realised-vol gap and its 3-year pct;
    - entry (≥ 90th pct) and exit (< 70th pct) states.
  - Broad-ETF net flow (亿): 11 broad ETFs (config list), one day and 5 days. 512100 and 588000 are shown on their own rows.
  - Each row: value, trigger level, state (✓ / ✗ / 接近), plain-language note.
- Out:
  - Orders or position sizing; scoring stocks; intraday data (stk_mins limits, D-152 notes).
  - New signals without a research run behind them.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Signal | `core.SmallCapWatchSettings` (`config/smallcap_watch.yaml`). `calculation.SmallCapWatchBuilder` reads `daily`, `stk_limit`, `reference/index_daily`, `fund_share` and `fund_daily` and returns the rows above plus 1-year history. CLI `smallcap-watch` writes `$(APP_DATA)/smallcap_watch.json`; added to `make track-daily` | TCs on hand fixtures: limit-down count at the boundary, 60-day-low share, gap pct, trigger at the threshold and not one tick inside, ETF flow = Δshare × close. The real lake for 20261116 reproduces the research values: 68 limit-downs, 27% at a 60-day low, gap ≈ 22.9 (97th pct), 11-ETF flow ≈ +171亿. `make check` passes | — | done 2026-11-17 — make check green (981 passed, lint 0); real 20261116: 68 limit-downs, 27.5% at a 60-day low, gap 22.2 (97th pct), 11-ETF flow +170.7亿 |
| 2 | Display | `MonitorReportRenderer` gets a 小盘观察 section with triggered rows first and in red. The Go `VolatilityMonitor` store reads `smallcap_watch.json`. A React panel on `#volatility` holds the table and a 中证1000 chart with the level lines | `go test`, vitest (format helpers), and smoke opens the panel; the e-mail fixture shows a triggered and an untriggered row; `make check` passes | 1 | done 2026-11-17 — make check: lint 0 findings, mypy clean, pytest 1015 passed, go test ok, vitest 49 passed; only the project-catalog step was skipped (catalog locked by a running CNINFO download) |
| 3 | Phone line (optional) | `AlertMessageBuilder` sends one plain line when a panic-day or index-level trigger first fires (behind a new `smallcap` trigger, off until the user says) | The user approves the dry-run text; there is a plan log row | 2 | todo |
| 4 | 融资余额 rows and chart | `SmallCapWatchSettings` gains `margin_dd_trigger: -0.10`, `margin_turn_days: 5`. `SmallCapWatchBuilder` reads `curated.margin` (all exchanges; a day missing an exchange is skipped, never summed half) and adds group 杠杆: 融资余额 (亿, 5- and 20-day change, 20-day mean), drawdown from its 250-day high, 融资余额 / 流通市值 with its percentile (user: "两融绝对水平呢？"), and a 企稳 row: on when the drawdown ≤ −10% and the 5-day change turns ≥ 0, note citing the 12-event history and the two 2026 failures; `history` gains the daily balance. `#volatility` panel draws the balance line and the share-of-float-cap line; the e-mail table gets the rows. Refetch `margin` for 20261106 (SSE only in the lake) after the running update-all | TCs on hand fixtures: missing-exchange day skipped; drawdown and 5/20-day change; 企稳 fires on the first ≥ 0 day at −10% and not at −9.9%. Real lake 20261118: balance ≈ 22,083 亿, 20-day change negative, 企稳 off. vitest, smoke shows the line. `make check` passes | 2 | done 2026-11-19 (uncommitted) — lint clean for these files, pytest 1125 passed (2 failures from the concurrent retail_gauge factor work, not this phase), go test ok, vitest 62, SMOKE OK incl. 3 杠杆 rows + 2 charts, no overflow at 390 px; real 20261118: 融资余额 22,083 亿 (5d −2.9%, 20d −9.9%, −26.6% from high), 2.53% of float cap (3y pct 65%), 企稳 off; margin 20261106 refetched (3 exchanges, 22,549 亿); make check complete 2026-11-19 after the peer writes: lint 0, 1126 passed, catalog stale 0, release-lags ok |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `SmallCapWatchSettings` | new | `quant_cn.core` | 1 |
| `SmallCapWatchBuilder`, `SmallCapWatchRows` | new | `quant_cn.portfolio` (needs EtfFlowCalculator, layer 5) | 1 |
| `VolatilityMonitorBuilder` | reuse (realised-vol helpers if exposed; else a small shared helper via registry) | `quant_cn.calculation` | 1 |
| `MonitorReportRenderer`, `MorningReportBuilder`, Go store / handlers, React `#volatility` | extend | python / Go / React | 2 |
| `AlertMessageBuilder` | extend | `quant_cn.notify` | 3 |

## Risks
- The thresholds come from 7–27 episodes, so the rows are context, not signals. The e-mail says "研究信号，不构成交易建议".
- `stk_limit` starts in 2019-01, so the limit-down history before then is missing. The 3-year percentiles are fine.
- ETF share data lands a day late. The flow row shows its own date.
- The user's index levels (6,075 / 5,500) are personal and live in a git-ignored `config/local.smallcap_watch.yaml` override.

## Open questions
- Settled 2026-11-17 by approval with defaults: 持仓监测 e-mail; 科创50 rows (realised vol pct, 588000 flow) with no level lines.
- Phone line (phase 3): stays off until the user asks.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-19 | 4 | Done. Share-of-float-cap percentile ranked on the margin_detail sum (curated.margin starts 2025; a 2025-only window showed 44% vs 65% over 3 years); balance axis in 万 |
| 2026-11-18 | 4 | Approved ("批准"). Scope: + 融资余额 / 流通市值 row and chart (now 2.51%, 86th pct since 2019; 2024-09 bottom 2.2%); MA crossings tested and dropped as triggers (MA20 60d +1.6% vs 5-day turn +7.4%), MA20 kept in the note; 企稳 days not marked on the chart (the chart component draws one line) |
| 2026-11-18 | 4 | Drafted: 融资余额 rows, 企稳 state and chart (user: "把融资余额也加到app里track，感觉行情在明年了"); evidence 20261118_marginal_trader; awaiting approval |
| 2026-11-17 | 2 | Done. `SmallCapReportSection` (visualization) in the 持仓监测 e-mail after 波动率; Go `GetVolatilityMonitor` attaches smallcap_watch.json as `smallcap`; `SmallCapPanel` on #volatility above the VIX cards (table, triggered first, 中证1000 chart with the levels); `VolatilityChart` now takes points + refs. User asked after seeing #volatility without realised vol |
| 2026-11-17 | 1 | Done. `SmallCapWatchSettings` (core) and `SmallCapWatchBuilder` + `SmallCapWatchRows` (portfolio, beside EtfFlowCalculator) are built; CLI `smallcap-watch`; `make smallcap-watch` is in track-daily. 000688.SH (科创50) added to `enum_values.indices` for index_daily. Breadth uses derived.prices_adj. User levels are in the git-ignored config/local.smallcap_watch.yaml |
| 2026-11-17 | all | Approved (user: "可以"), with the defaults for the open questions; build order: 30 first, then 21 |
| 2026-11-17 | all | Drafted, awaiting approval. User: "每天更新吧" on the daily small-cap watch offer, then "可以" to writing the plan |
