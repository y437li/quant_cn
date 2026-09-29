# Commodity, Macro and Sector Data Design (v0.1 draft, 2026-09-28; D-062 proposed)

Adds commodity prices (oil, gold, industrial and agricultural), macro series (rates, FX) and sector indices to
the lake, builds roll-adjusted continuous series, and exposes them to the risk model (macro-sensitivity
factors), the factor library (commodity spillover, regime variables), ETF pairs and positioning research.

## 1. Data
### 1.1 Domestic commodity futures (Tushare, have `fut_daily`/`fut_basic` config from plan 09)
| Exchange | Contracts (initial set) | Notes |
|---|---|---|
| INE | SC crude oil, LU low-sulphur fuel oil, BC copper (international) | SC is the domestic oil benchmark |
| SHFE | AU gold, AG silver, CU copper, AL aluminium, ZN zinc, NI nickel, RB rebar, HC hot-rolled coil, FU fuel oil, BU bitumen, RU rubber, SS stainless |
| DCE | I iron ore, J coke, JM coking coal, M soybean meal, Y soybean oil, P palm oil, C corn, L PE, PP, V PVC, EG, EB |
| CZCE | TA PTA, MA methanol, SR sugar, CF cotton, RM rapeseed meal, OI rapeseed oil, SA soda ash, FG glass, UR urea, AP apple |
| CFFEX | IF/IH/IC/IM (have), T/TF/TS treasury futures | T for the rates factor |
Datasets: `fut_basic` (all exchanges, sweep `exchange`), `fut_daily` (sweep `trade_date` + `exchange`), `fut_mapping`
(main-contract map per trading day; sweep `trade_date`), `fut_holding` (have, extend exchanges), `fut_wsr`
(warehouse receipts, weekly; optional), `fut_settle` (optional).

### 1.2 Gold spot and precious metals
`sge_basic`, `sge_daily` (Shanghai Gold Exchange: Au99.99, Au(T+D), Ag(T+D)); sweep `trade_date`.

### 1.3 International benchmarks (second source required)
Brent, WTI, COMEX gold, LME copper, Bloomberg-style commodity index, DXY, US 10y. Tushare Pro does not carry
these reliably (`index_global` covers equity indices only). Options: **AkShare** (free Python library wrapping
Sina/Eastmoney foreign futures quotes and FRED), **FRED** (EIA oil, LBMA gold, DGS10, DTWEXBGS via CSV API,
free key), **Stooq** CSV. Design: a second `BaseApiClient` implementation per source (`FredClient`,
`AkShareClient`) behind the same `BaseFetcher`/`DatasetSpec` machinery; datasets declare `source:` (default
`tushare`). Recommendation: FRED for oil/gold/rates/DXY (stable, documented, daily), AkShare only for series
FRED lacks (LME). Data licence note: FRED is free for research use; AkShare scrapes public pages (fragile;
keep a raw copy, D-009).

### 1.4 Macro (Tushare)
`shibor` (have), `shibor_lpr`, `yc_cb` (China treasury yield curve, sweep `trade_date`, curve `1001.CB`),
`fx_daily` (USDCNY etc.; sweep `trade_date`), `cn_cpi`, `cn_ppi`, `cn_pmi`, `cn_m` (monthly, known-on = release
date: Tushare gives the stat month only → use a fixed release-lag rule per series, e.g. CPI released ~10th of
the following month; documented in `datasets.yaml.release_lag_days`).

### 1.5 Sector indices
`index_classify` + `index_member_all` (Shenwan L1/L2/L3, plan 05 ph1), `sw_daily` (Shenwan index bars; sweep
`trade_date`; permission tier), CSI sector indices via `index_daily` (`ts_code` enum, e.g. 000928.SH energy …),
`ths_index`/`ths_daily` (Tonghuashun concept indices, optional), sector ETFs already covered by `fund_daily`.

## 2. Derived series (`calculation`)
| Class | Purpose |
|---|---|
| `ContinuousFutures` | roll-adjusted continuous price per product from `fut_daily` + `fut_mapping`: roll on main-contract change (or N days before expiry), back-adjust by ratio (default) or difference; stores roll dates and adjustment factors; outputs `CONTINUOUS_PANEL` (`trade_date, product, close_adj, close_raw, contract, roll_flag, oi, vol`) |
| `TermStructure` | annualised roll yield / basis between front and next contract per product (backwardation / contango) |
| `MacroSeries` | aligned daily macro panel (`MACRO_PANEL`: `trade_date, series, value, known_on`) from Tushare macro, FRED, SGE, FX, yields; monthly series forward-filled from their release date only (PIT) |
| `SectorIndexPanel` | sector index returns (Shenwan L1/L2, CSI sectors) as `PRICE_PANEL`-shaped frame keyed by index code |
All pure computations over lake frames; `pipeline.CalculationStep` writes `derived/commodities/`, `derived/macro/`,
`derived/sectors/`.

## 3. Uses
### 3.1 Risk model (optional macro-sensitivity factors, RISK_FACTOR_LIST §4b)
Per stock, 252-session betas (half-life 63) of excess returns to **market-orthogonalised** commodity/macro
returns: `OilBeta` (SC or Brent), `GoldBeta` (AU or COMEX), `MetalsBeta` (CU/I basket), `RatesBeta` (Δ 10y CGB
yield), `CnyBeta` (USDCNY). Enter the model as style factors only if they raise adjusted R² and keep bias
statistics inside the band (RiskModelValidator decides; D-061 v3 gate). Industry factors already absorb most
commodity exposure; these capture within-industry differences (e.g. refiners vs producers).
### 3.2 Factor library (FACTOR_LIBRARY §5b)
Commodity-spillover momentum: 20/60-session return of a stock's linked commodity (mapping table
`config/commodity_links.yaml`: industry → products) as a factor for the linked industries; gold/oil momentum and
term structure as **regime variables** alongside `VIX_PANEL.regime`; sector momentum / sector relative strength
from `SectorIndexPanel` (replaces the industry-momentum descriptor's dependence on stock aggregation).
### 3.3 ETF pairs and positioning
Commodity ETFs (gold 518880/159934, oil 161129 etc.) vs `ContinuousFutures` (basis pairs); `FuturesPositioning`
extended to SHFE/DCE/CZCE (`fut_holding` covers them); `TermStructure` as a carry signal.

## 4. Frames
`CONTINUOUS_PANEL`, `MACRO_PANEL`, `TERM_STRUCTURE` (`trade_date, product, front, next, basis_ann, days_front`),
`SECTOR_PANEL` (sector index bars), `COMMODITY_LINKS` (industry → product, weight).

## 5. PIT rules specific to this data
- Futures settle and mapping are known at the close of `trade_date`; a roll decided on day `t` applies from `t+1`.
- Monthly macro releases are visible from their **release date**, not the reference month; `release_lag_days`
  per series with the official calendar where Tushare exposes it (`cn_cpi` has none → rule), flagged in `known_on`.
- FRED series are dated by observation day (US time); treat as visible on the next China session.
- SGE and fx are same-day close.

## 6. Open questions
1. Second source: FRED (+ AkShare for LME) as recommended, or AkShare only (one dependency, less stable)?
2. Continuous-futures adjustment: ratio (default, right for returns) or difference (right for spreads); store both?
3. Initial product set: the ~40 above, or start with oil (SC, Brent), gold (AU, COMEX), copper (CU, LME), iron ore (I), 10y (T, DGS10), USDCNY and add on demand? Recommendation: the small set first.
4. `sw_daily` permission tier: verify; fallback = compute Shenwan L1 index returns from members and `index_member_all` (cap-weighted) ourselves.
