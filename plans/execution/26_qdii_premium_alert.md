# 26 — QDII premium alert (QDII 溢价提醒)

| | |
|---|---|
| Status | drafted, awaiting approval |
| Owner | user (approve) / executor (build) |
| Created | 2026-11-14 |
| Notion | pending |
| Decisions | D-158 (proposed), D-126 |
| Depends on plans | 15 ph7b (etf_proxy.json, ETF e-mail section) |

## Goal
Every day the ETF part of the app and the morning e-mail list the premium of the liquid QDII / cross-border ETFs over their NAV, and flag when one falls below the buy threshold (default 3%) or rises back above it.

## Evidence (research, 2026-11-14)
- `research_space/runs/20261114_etf_universe/`: close vs same-day NAV on 2026-11-05/06: 纳指100 +20..25% (two-month range +7..25%), 标普500 +12..13%, 道指 +7%, 日经225 +3.5..5%, 白银 LOF +7%, 豆粕 ETF +3%; 港股 / 黄金 / 国债 ≈ 0.
- The user cannot trade futures and keeps to liquid ETFs (memory `etf-only-liquid`); buying a +20% premium loses it when quota reopens.

## Scope
- In:
  - Data: `fund_nav` (market E) added to the `etf-proxy` refresh (last 14 days, like fund_daily) (D-158).
  - Watch list: listed funds whose name has QDII or that are in a configured extra list (白银 LOF 161226, 豆粕 159985), 60-session mean amount ≥ 1 亿; config section `premium` in `config/etf_proxies.yaml` (buy_below 3%, high 10%, min amount, extras).
  - Premium = close / unit_nav − 1 on the latest date where both exist (QDII NAV lags one or two sessions; the date is shown). Per ETF: latest premium and date, 20-session mean, 60-session min / max, state 可买 (< 3%) / 偏高 / 很高 (≥ 10%), grouped by tracked market (纳指, 标普, 道指, 日经, 德国 / 法国, 原油 (161129 used by plan 27; 501018 / 160723 as alternatives), 其他).
  - Flags: crossing below buy_below (可以买了) and back above; once per crossing.
  - Display: rows in the ETF e-mail section; a table in the app's ETF panel; flagged rows first.
- Out:
  - Phone alerts (recipient is 妈妈 only, A股 focus; plan 22 rules), unless the user asks.
  - Intraday IOPV premium (needs real-time quotes); buy orders; HK-connect ETFs (premium ≈ 0).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Signal | `fund_nav` in `ETF_PROXY_DATASETS`; `core.EtfPremiumSettings` (section `premium`); `portfolio.EtfPremiumMonitor` (reads curated fund_basic / fund_daily / fund_nav: watch list, premium, state, history, flags); `EtfProxyBuilder` writes a `premium` part into `etf_proxy.json` | TCs on hand frames: same-date join with a lagged NAV, state cut-offs, a flag only on a crossing, liquidity filter, extras included; real lake reproduces the research premiums (纳指 ≈ +20%); `make check` green | — | todo |
| 2 | Display | `EtfReportSection` rows (market, ETF, premium, state, 20-day mean); Go `EtfProxy` struct + React ETF panel table; "溢价按前一交易日净值计算" note | `go test`, vitest, smoke opens the panel; e-mail renders on today's document; `make check` green | 1 | todo |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `EtfPremiumSettings` | new (pydantic, part of `EtfProxySettings`) | core | 1 |
| `EtfProxySettings` | extend (`premium` field) | core | 1 |
| `EtfPremiumMonitor` | new | portfolio | 1 |
| `EtfProxyBuilder` | extend (injected `EtfPremiumMonitor`, `premium` part) | portfolio | 1 |
| `EtfReportSection` | extend | visualization | 2 |
| Go `store.EtfProxy`, React `features/watchlist/etf-proxy-panel` | extend | apps | 2 |

## Risks
- NAV timing: QDII NAV is published one or two sessions late; comparing with the same-date close is correct but the reading is one or two days old. The page shows the NAV date.
- fund_nav sweep cost: one call per date for market E; 14 days a run is small.
- Shared files: `etf_proxy_builder.py`, `etf_report_section.py`, the Go store and the ETF panel are part of the uncommitted plan 15 ph7 work; nothing is committed until the user decides the repo history.

## Open questions
- Where should the alert reach you: app + morning e-mail only, or also a phone message to you (plan 22 sends only to 妈妈 today)?
- Threshold: buy below 3% (default), or another level?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-14 | — | Drafted (user: "加一个QDII溢价提醒") |
