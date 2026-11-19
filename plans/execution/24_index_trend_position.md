# 24 — Index trend position (指数趋势仓位) on the 波动率监测 page

| | |
|---|---|
| Status | drafted, awaiting approval |
| Owner | user (approve) / executor (build) |
| Created | 2026-11-14 |
| Notion | pending |
| Decisions | D-157 (proposed), D-152, D-153 |
| Depends on plans | 03 ph6 (volatility monitor), 15 ph7 (app page, e-mail), 22 (phone alerts) |

## Goal
Every day the 波动率监测 page, e-mail block and (optionally) the phone alert show, for each A-share broad index, a research-based suggested position from a short-trend blend with volatility sizing, next to its fear reading (A-share VIX where options exist, realised volatility otherwise) and what that combination meant historically.

## Evidence (research runs, 2026-11-14)
- `20261114_tsmom_robust/short_trend_check.py`: 4 indices 2011–2026, blend of 10/21/42/252-session signals with volatility sizing (min(1, 20% / 60-day vol)): Sharpe 0.54 (hold 0.22), max drawdown −29% (hold −63%), 0.51 / 0.57 in 2011–18 / 2019–26, 0.41 at 15 bp. A single window (21 days) scores similar but is window- and period-sensitive.
- `20261114_tsmom_robust/signal_lag.py`: the 12-month signal alone exits a median 8 months after a top at −35%.
- `20261114_vix_vs_trend/vix_vs_trend.py`: fear high (≥ 90th pct of a year) mostly comes with trend off. Next 60 sessions: fear-high + trend-off +3.2% (57% up) against +2.0% (50%) on all days; fear-high + trend-on −0.6% (40% up, blow-off tops). Adding "buy when fear is high" to the blend lowers Sharpe 0.47 → 0.32 and deepens drawdown −31% → −46%. So fear is shown as context, not added to the position.

## Scope
- In:
  - Indices: 沪深300, 中证500, 中证1000, 创业板指 (in `index_daily` since 2010); fear source per index: 300ETF / 500ETF / 中证1000 VIX line from the monitor, realised 20-day vol for 创业板指.
  - Per index each day: the four window signals (up / down), blend (0–100%), 60-day volatility, size factor, suggested position = blend × size, fear percentile and state, the historical row for the current fear × trend bucket (next-20 / 60-session mean return and share up, from a fixed research table), 1-year history of index, blend and position.
  - Parameters in `config/volatility_monitor.yaml` section `trend` (windows, vol window, target, fear percentile, indices and their VIX line).
  - Flags when the suggested position crosses a 25-point step; e-mail rows; app panel; phone-alert line behind the existing `volatility` trigger (plain words, off by default until the user says).
- Out:
  - Orders or automated trading; sizing beyond the index level; stocks or sectors (no evidence, research runs `20261114_tsmom_single`, `trend_rules` SW L1).
  - Adding fear-buy to the position (made it worse).
  - 科创50 / 上证50 trend (not in the index list yet; see open questions).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Signal | `core.TrendSettings` (section `trend` of volatility_monitor.yaml); `calculation.IndexTrendSignal` (reads curated `reference/index_daily`, returns per-index signals, blend, vol, size, position, fear pct, bucket row, history, flags); `VolatilityMonitorBuilder` gains a `trend` part (injected like FuturesMonitorBuilder's helpers) | TCs on hand price paths: each window signal, blend steps, size cap at 100%, fear from the VIX line or realised vol, flag at a 25-point crossing and only once; real lake 20261113 reproduces the research numbers (blend 25% on all four, size 52–100%); `make check` green | — | todo |
| 2 | Display | `VolatilityReportSection` rows for the trend part; Go `VolatilityMonitor` struct gains `trend`; React panel on `#volatility`: table (index, four ✓/✗, blend, vol, suggested position, fear tag, historical row) + chart (index with shaded position); "研究信号，不构成交易建议" note | `go test`, vitest (format helpers), smoke opens the panel; e-mail renders on today's document; `make check` green | 1 | todo |
| 3 | Alert and review | `AlertMessageBuilder` plain line for a position-step flag (behind `volatility`, `volatility_groups` A股) if the user wants it; research run re-checked after 3 months live | dry-run text approved by the user; plan log row with the live record | 2 | todo |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `TrendSettings` (+ `TrendIndex`) | new (pydantic, part of `VolatilityMonitorSettings`) | core | 1 |
| `VolatilityMonitorSettings` | extend (`trend` field) | core | 1 |
| `IndexTrendSignal` | new (reuses `calculation.TrendPosition`, built for plan 27 on 2026-11-14) | calculation | 1 |
| `VolatilityMonitorBuilder` | extend (`trend` part, injected `IndexTrendSignal`) | calculation | 1 |
| `VolatilityReportSection` | extend | visualization | 2 |
| Go `store.VolatilityMonitor`, React `features/volatility` | extend | apps | 2 |
| `AlertMessageBuilder` | extend | visualization | 3 |

## Risks
- Overfitting: windows were chosen after looking at 2011–2026 data. Mitigation: a blend, not the best single window; a 3-month live check in phase 3; parameters in config.
- Short real VIX history (from 2025-11): the fear rows use realised volatility history; the VIX is shown but not used in the bucket table.
- Read as trading advice: the page and alerts say "研究信号，不构成交易建议"; the phone line stays off until the user asks.
- Costs: about 75 small position changes a year at 5 bp; the page shows the change, not an order size.
- Shared files: `handlers.go`, `store.go`, `report_commands.py`, `app-route.ts` and the volatility page belong to the uncommitted plan 15 ph7 / plan 03 ph6 work; nothing is committed until the user decides the repo history.

## Open questions
- Phone alert for position steps: on (to 妈妈, plain words) or app / e-mail only?
- Add 科创50 (000688.SH) and 上证50 to `index_daily` so they get a trend row next to their VIX?
- Should the step size for flags be 25 points (each window) or 50?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-14 | — | Drafted (user: "可以，写个计划放进监测页。A股Vix逢高买比较有参考性，看看这俩有重叠没有"); research `20261114_vix_vs_trend` added the fear × trend context and kept fear out of the position |
| 2026-11-14 | 1 | `calculation.TrendPosition` (blend x vol size on any price series) built under plan 27; IndexTrendSignal reuses it |
