# 22 — Phone alerts by iMessage

| | |
|---|---|
| Status | done — daily text alerts to 妈妈 only (pictures off) |
| Owner | user (approve) / executor (build) |
| Created | 2026-11-13 |
| Notion | pending |
| Decisions | D-153 |
| Depends on plans | 15 ph7 (monitor documents), 03 ph6 (volatility monitor) |

## Goal
After each daily run, new alerts reach the recipients' iPhones (first: the user's mother) as one short plain-language iMessage, sent by this Mac's Messages app.

## Scope
- In:
  - Triggers: volatility alerts (`volatility_monitor.json`); watchlist names entering the buy range or meeting their buy conditions (`watchlist.json`); new futures signals and new macro prints (`futures_monitor.json`, `macro_monitor.json`).
  - Plain-language Chinese text (user: "要写大白话一点"):
    - no English abbreviations or jargon (VIX → 恐慌指数; no 分位, 信号, 条件, 期限结构, CPI / PPI);
    - each number compared with its normal level ("平时在 17 左右");
    - one short line per item, ending in what it means ("还算平稳", "市场紧张").
  - One message per run; each alert sent once (sent log).
  - Recipients, on / off per trigger and a daily cap in git-ignored `config/local.notify.yaml` (phone numbers never in git); committed `config/notify.example.yaml`.
  - CLI `notify` with `--dry-run`; it runs at the end of `track-daily` (06:xx US Eastern = 19:xx Beijing).
- Out:
  - SMS gateways (China SMS platforms need a company signature).
  - WeChat.
  - Intraday alerts (the data is end of day).
  - Holdings alerts (not chosen).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Sender | `core.NotifySettings` (+ `NotifyRecipient`) from `config/local.notify.yaml`; `core.MessageSender` base + `core.IMessageSender` (osascript through an injected command runner); `config/notify.example.yaml` | tests with a fake runner (TC IDs); one real test iMessage to the **user's own** number arrives; `make check` green | — | todo |
| 2 | Alert text + CLI | `visualization.AlertMessageBuilder` (plain-language lines per trigger from the four documents); sent log `notify_sent.json` in the app data folder; CLI `notify [--dry-run]`; `make notify` at the end of `track-daily` | dry-run on today's documents prints the message; a second run sends nothing new; `make check` green | 1 | done 2026-11-13 — first real send to Ella (中国巨石 line + trimmed card); picture lost (deleted too early, fixed below); a second run: "1 active alerts, none new" |
| 3 | Go live | the user reviews a dry-run and adds their mother's number; first real send | the mother receives the message; plan log row | 2 | done 2026-11-13 — text-only sample sent to 妈妈 15:39 |

## Classes

| Class | Action | Package | Phase |
|---|---|---|---|
| `NotifyRecipient`, `NotifySettings` | new (pydantic, like `MailSettings`) | core | 1 |
| `MessageSender` | new base | core | 1 |
| `IMessageSender` | new (subclass) | core | 1 |
| `AlertMessageBuilder` | new | visualization | 2 |
| `ReportCommands` | extend (`notify` subcommand) | cli | 2 |
| `MailSender`, `MorningReportBuilder` | reuse (pattern only) | core / visualization | — |

## Risks
- Messages must be signed in to an Apple ID on this Mac. The 06:00 launchd job needs a one-time macOS Automation permission for Messages; without it the send fails. The failure is logged and the run continues.
- Mac asleep or off at run time: no message that day. The next run catches up because unsent alerts stay in the log.
- Plain-language text oversimplifies signals: technical futures signals are summarised by family name and direction only, with a pointer to the app.
- Spamming: one message per run, a daily cap, and each alert key sent once.

## Open questions
- The mother's number: contact 唐升玲 in this Mac's Contacts (user: "我妈是唐升玲"); read it from there into `config/local.notify.yaml` (git-ignored) at phase 3.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-13 | 3 | Recipients cut to 妈妈 only (user: "ella不用收到，我也不用"). Sender shows the Apple ID e-mail; the user chose not to change the Messages sender setting ("就这样吧") |
| 2026-11-13 | 3 | Done. User: "别发图片了，就文字吧" → `max_images: 0` in local.notify.yaml (sample mode honours it; pictures folder removed). Text-only sample (417 characters) sent to 妈妈 at 15:39. Daily `make notify` now goes to Ella, 我 and 妈妈 |
| 2026-11-13 | 3 | (user: "可以发一整套给我看看，然后发给我妈") `notify --sample`: today's full set from real data (A股 volatility status line, watchlist, every futures signal, latest CPI / PPI / PMI) with a sample note, one picture per line, sent log untouched (TC-AMB-005, TC-RPC-008); pictures get plain titles (科创板恐慌指数, 工厂出厂价格（比去年）…) and no percentile. Recipients 我 (own Apple ID) and 妈妈 (唐升玲 from Contacts, +86 mobile) added to the git-ignored file. Sample sent to 我 at 15:37 (5 pictures, before the title change) |
| 2026-11-13 | 2 | Pictures never arrived: self-test of two AppleScript forms, only `send (POSIX file … as alias)` delivers (user: "B可以看见"); `FILE_SCRIPT` switched. Watchlist wording (user: "不应该只是简单的买入区间"): the alert spells out the buy conditions (met k of n, unmet ones in plain words via `PLAIN_COND`, act / wait), key carries k; phone card keeps the conditions box (TC-AMB-004) |
| 2026-11-13 | 2 | Fix (user: "没有图片"): the 15:29 picture never arrived because the file was deleted right after `send` returned, while Messages still uploads in the background. Pictures are now deleted at the start of the next run instead (TC-RPC-007 updated); the card was resent to Ella with a note |
| 2026-11-13 | 2 | Done (user "ok"): `make notify` sent the 中国巨石 alert with its card to Ella at 15:29; pictures and folder cleaned; rerun sent nothing; `notify_sent.json` git-ignored |
| 2026-11-13 | 2 | Built: `AlertMessageBuilder` (+ `Alert`, `CardShot`; TC-AMB-001..003), `CardScreenshotter` + `apps/chain_web/tests/shot_cards.mjs` (phone style: watchlist card trimmed to name, price and chart; TC-CSS-001..002), `SentAlertLog` (`notify_sent.json`, once per episode; TC-SAL-001..002), `IMessageSender` images (TC-IMS-003), CLI `notify` from documents (TC-RPC-007), `make notify` (NOTIFY_ARGS=--dry-run) at the end of track-daily. User: "要写大白话一点"; "发送完了要清理" → pictures and their empty folder deleted after a real send; "重点中国相关，不用管美股vix" → `NotifySettings.volatility_groups` default [A股]. Dry-run 20261113: one line, 中国巨石 27.37 in 27–30, with its trimmed card. 769 tests pass; `make check` lint blocked only by a peer's research folder without INDEX.md |
| 2026-11-13 | 1 | Test text plus a card picture (US VIX) sent to Ella; delivered (user "ok") |
| 2026-11-13 | 1 | Built and started at the user's request ("发给ella试一试", Canadian number chosen in the question): `NotifyRecipient`, `NotifySettings`, `MessageSender`, `IMessageSender` (TC-NS-001..002, TC-IMS-001..002), CLI `notify --text [--to] [--dry-run]` (TC-RPC-006), `config/notify.example.yaml`, git-ignored `config/local.notify.yaml`. Messages signed in; iMessage account resolved by osascript; test message accepted by Messages (37 characters) |
| 2026-11-13 | — | Drafted (user: "可以做个发信息的功能吗？" → 手机信息, 发给妈妈 (iPhone), 大白话; triggers 波动率提醒, 观察账本到价, 期货 / 宏观新信号) |
