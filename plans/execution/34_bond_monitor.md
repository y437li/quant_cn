# 34 — China rates and RMB monitor (国债利率与人民币汇率监控)

| | |
|---|---|
| Status | approved 2026-11-18 (user: "show in app"); ph1–4 done |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-17 |
| Notion | pending |
| Decisions | D-080 (中债 curves from AkShare, not yc_cb), D-171 |
| Depends on plans | macro monitor (MacroMonitorBuilder), 30 (volatility page pattern), etf_cta bond switch |

## Goal
One daily view of the China bond market and the RMB in the app and the morning e-mail. It covers government curve levels and moves, curve shape, credit spreads, the policy anchor, the stock–bond yield gap (股债性价比), and RMB against the dollar, euro, yen, HKD and the dollar index, with the PBOC fixing. Every row has a 5-year percentile and a plain trigger state. Today `cn_bond_yield` and `fx_daily` are downloaded daily but shown nowhere.

## Scope
- In (bonds):
  - 中债国债 1Y / 3Y / 5Y / 10Y / 30Y: level, 1w / 1m / 3m / 1y change in bp, 5-year percentile, 1-year high / low.
  - Spreads: 10Y−1Y, 30Y−10Y (term); AAA bank bond − govt 10Y and AAA notes − govt 3Y (credit); govt 1Y − SHIBOR 3M or 1Y LPR (policy anchor, from `shibor` / `shibor_lpr`).
  - 股债性价比: CSI 300 earnings yield − 10Y, with its 5-year percentile.
- In (FX):
  - From `fx_daily` (FXCM, already daily): USDCNH, EURUSD, USDJPY, dollar index (USDOLLAR); derived EUR/CNH, CNH/JPY.
  - 中美利差 = 中债 10Y − US 10Y yield. FXCM 10USNOTE is a price, not a yield, so the US 10Y yield comes from FRED DGS10 (added in ph1 if not already in the lake).
  - New dataset: PBOC central parity (人民币中间价) for USD, EUR, JPY, HKD, GBP and onshore USDCNY close, from AkShare (endpoint chosen and verified in ph1, as for D-080). Rows: fixing, spot − fixing gap (a strong-fixing signal), onshore − offshore gap.
  - Same row format as bonds: level, 1w / 1m / 3m / 1y % change, 5-year percentile, 1-year high / low.
- Triggers (config `config/rates_fx_monitor.yaml`): 10Y at a new 1-year low or high; weekly move ≥ 10bp in 10Y or 30Y; credit spread weekly widening ≥ 10bp; 股债性价比 above its 90th percentile; USDCNH weekly move ≥ 1% or a new 1-year high / low; spot − fixing gap beyond ±1%.
- Out:
  - Trading rules or allocation changes (the ETF CTA bond switch stays as it is).
  - Corporate or LGFV curves beyond the two AAA curves; overseas curves other than the US 10Y; intraday data.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Fixing data | Dataset `cny_fixing` (AkShare): daily central parity per currency and onshore USDCNY, in `config/datasets.yaml` and `make market-data`; backfill from 2015 | Rows every China session since 2015 (gaps listed); 20261117 USD fixing matches the PBOC published value; `make check` passes | — | done 2026-11-18 — cny_fixing (currency_boc_safe, 8,088 rows since 1994, 25 currencies) and us_treasury_yield (bond_zh_us_rate, 3,164 rows since 2015) downloaded, compacted, in MARKET_RANGE_DATASETS; 20261117 USD fixing 671.32 per 100 = 6.7132. Onshore USDCNY close dropped (no stable source, D-171) |
| 2 | Monitor document | `RatesFxMonitorBuilder` writes `$(APP_DATA)/rates_fx_monitor.json`: bond and FX rows (level, changes, percentile, trigger state), daily history since 2021 for charts; `make rates-fx-monitor` in `make track-daily` | TCs on hand series: bp and % changes, percentile, a new-low trigger, a missing point → null, PIT (nothing after as_of). The real 20261117 file matches direct SQL (10Y 1.6055, USDCNH 6.6661) | 1 | done 2026-11-18 — RatesFxSeriesReader + RatesFxMonitorBuilder, rates_fx_monitor.json (27 lines, 24 shown, 490 KB); real file matches direct SQL (10Y 1.6055, USDCNH 6.6661); TC-RFR-001..004, TC-RFM-001..004, TC-RFS-001, TC-RPC-013; `make rates-fx-monitor` in track-daily |
| 3 | App tab | Go `/api/rates-fx`; web `#rates` under 监测 with a 债市 / 汇率 switch: headline, table, charts (curve today vs 1m / 1y ago, 10Y and 30Y, credit spread, 股债性价比; USDCNH with fixing, RMB vs EUR / JPY, 中美利差) | go test, vitest on format helpers, smoke opens both views | 2 | done 2026-11-18 — Go /api/rates-fx (TC-ST-029, TC-API-016), web #rates 利率汇率 under 监测 with 债市 / 汇率 switch, table, curve chart, 5-year charts; vitest TC-RFF-001..002; smoke: 12 bond rows, FX view ok |
| 4 | E-mail section | `RatesFxReportSection` (ReportSection) in the 持仓监测 e-mail after 波动率 / 小盘观察: one line each for 债市 and 汇率, plus triggered rows | Fixture test; the real dry-run e-mail shows the block; `make check` passes | 2 | done 2026-11-18 — RatesFxReportSection (TC-RRS-001..002) after 小盘观察; real dry-run e-mail shows the summary line and the 10-row table |

Status cell: `<state> <YYYY-MM-DD> (<commit>) — <note>`, state one of todo / doing / blocked / done.

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| AkShare client (`AkshareClient` or the existing cn_bond_yield path) | reuse (config only) | `quant_cn.data_loading` | 1 |
| `RatesFxMonitorBuilder` | new (checked against `MacroMonitorBuilder`: that one handles monthly prints with release lags; daily series need their own builder, sharing its percentile helper if one exists) | `quant_cn.calculation` | 2 |
| `LakeQuery`, `DateCodec` | reuse | `quant_cn.lake`, `quant_cn.core` | 2 |
| Go `GetRatesFxMonitor`, React `RatesFxPage` | new | `apps/chain_api`, `apps/chain_web` | 3 |
| `RatesFxReportSection` | new, subclass of `ReportSection` | `quant_cn.visualization` | 4 |

## Risks
- AkShare sources can skip a day, revise or change format; the builder uses the last available date and flags staleness (> 2 sessions).
- FXCM closes at 17:00 New York, the 中债 curve at the China close: the two are a session apart, so rows carry their own dates.
- The CSI 300 PE source must be point in time; check `index_dailybasic` coverage in ph2, else build from members.
- Trigger thresholds are judgement calls; they live in config and are reviewed after a month.

## Open questions
- Triggers as listed, or levels you watch (e.g. 10Y below 1.6% / above 1.8%, USDCNH below 6.6)?
- Other currencies (KRW, GBP, AUD, CFETS basket)? Default: USD, EUR, JPY, HKD, GBP.
- Phone alert (plan 22) on a trigger, or app and e-mail only? Default: app and e-mail only.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-18 | 1–4 | Approved ("show in app") and built: datasets, monitor, #rates tab, e-mail block (D-171) |
| 2026-11-17 | all | Widened to RMB FX at the user's request ("还人民币对美元其他货币的汇率监测"): FX rows, fixing dataset (new ph1) |
| 2026-11-17 | all | Drafted at the user's request ("国债利率的监控-中国债市") |
