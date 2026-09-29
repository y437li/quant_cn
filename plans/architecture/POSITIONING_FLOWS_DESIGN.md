# Positioning and Forced Flows Design (v1.0, approved 2026-09-28; D-057–D-059 accepted)

Three estimators of *who is positioned where* and *where forced buying or selling would start*, for the CSI 300
first. Each rests on a stated assumption; until the validation phase the levels are hypotheses, not signals.
Lives in `calculation` (L4): pure computations on lake frames.

## 1. Option dealer gamma exposure (GEX)
- Inputs: option chains (IO on CFFEX; 510300.SH and 159919.SZ ETF options) from `opt_basic` + `opt_daily`
  (`OptionChainBuilder`), spot `S` from `index_daily` / `fund_daily`, rates from `RiskFreeCurve`.
- Per option: implied vol from its own price (`Black76Model.compute_implied_vol`), Γ from Black-76 at that IV
  (`Black76Model.compute_gamma`, new). `GEX(K) = Γ · OI · multiplier · S² · 1%` = CNY dealer hedge flow per 1% move.
- **Dealer sign assumption (D-057)**: dealers are long calls and short puts (customers buy puts, sell calls), so
  call GEX is positive and put GEX negative. Sign is a parameter; the output stores both signed and unsigned GEX.
- Outputs: `GEX_PANEL` (`trade_date, underlying, strike, gex_call, gex_put, gex_net, oi_call, oi_put, d_oi_call,
  d_oi_put`), plus per day `gamma_flip` (spot level where cumulative net GEX crosses zero), total net GEX,
  and the strikes with the largest put and call OI. Open-interest changes are shown next to levels.
- Multipliers: IO 100; ETF options 10,000 (adjusted contracts excluded, D-048).

## 2. Futures positioning (IF/IH/IC/IM)
- Inputs: `fut_daily` (price, settle, oi, vol), `fut_holding` (CFFEX daily top-20 brokers: long/short volume
  and OI per broker), `index_daily` for spot.
- **Assumption (D-059)**: `fut_holding` is a gross broker aggregate (member firm books), not client intent;
  net = Σ long OI − Σ short OI across listed brokers, with concentration (top-5 share) as a caveat column.
- Regime from ΔOI × Δprice: new longs (OI↑, P↑), short covering (OI↓, P↑), new shorts (OI↑, P↓), long
  liquidation (OI↓, P↓); per contract month and rolled front/next.
- Annualised basis: `(F − S)/S · 365/days_to_expiry` per contract; roll-adjusted term structure.
- Output: `FUTURES_POSITIONING` (`trade_date, contract, oi, d_oi, price_chg, regime, net_top20, top5_share, basis_ann`).

## 3. Margin liquidation ladder
- Inputs: `margin_detail` per stock (`rzye` financing balance, `rzmre` buys, `rzche` repayments), `daily` closes,
  `margin` exchange aggregates for reconciliation.
- **Vintage accounting (D-058)**: daily net new financing (`rzmre − rzche`, floored at 0 for new debt) is a
  vintage opened at that day's close; repayments retire vintages first-in-first-out. Each open vintage has a
  liquidation price `entry · maintenance / (1 + initial_margin)` with parameters maintenance 1.3 and initial
  margin 1.0 (both config, both flagged as assumptions; brokers vary 1.3–1.5 and 0.5–1.0).
- Aggregation: for each stock and each hypothetical drawdown step (0, −5, −10 … −50%), the CNY of vintages
  whose liquidation price is reached; summed over CSI 300 constituents (`index_weight`) and the whole market.
- Output: `MARGIN_LADDER` (`trade_date, scope, drawdown_pct, forced_sale_cny, share_of_float_cny`) and per-stock
  `MARGIN_VINTAGES` (`trade_date, ts_code, vintage_date, balance, liquidation_price, distance_pct`).

## 4. Validation (later phase)
Event study: do CSI 300 moves accelerate when spot crosses (a) high-put-OI strikes, (b) the gamma flip into
negative-gamma territory, (c) drawdown steps with large forced-sale CNY? Measure next-1/3/5-session absolute
return and realised vol conditional on crossing vs matched non-crossing days; report with confidence intervals.
Acceptance for calling any of these a signal: effect significant at 5% in two non-overlapping sub-periods.

## 5. Data
| Dataset | Endpoint | Sweep | From | Notes |
|---|---|---|---|---|
| `fut_daily` | `fut_daily` | `trade_date`, `exchange=CFFEX` | 2025-01 | price, settle, oi, vol per contract |
| `fut_holding` | `fut_holding` | `trade_date`, `exchange=CFFEX` | 2025-01 | top-20 broker long/short |
| `fut_basic` | `fut_basic` | `exchange=CFFEX` | — | multipliers, delivery dates |
| `margin` | `margin` | `trade_date` | 2025-01 | exchange aggregates |
| `margin_detail` | `margin_detail` | `trade_date` | 2024-01 | per stock; 2019+ later if the ladder proves useful |

## 6. Open questions
Closed 2026-09-28 with the recommendations: dealer-sign default kept, OI changes shown, revisit after validation; single market-wide margin parameters with a mixture sensitivity in the notebook; downstream regime conditioning only after the event study.
