# ETF Pairs Trading Design (v1.0, approved 2026-09-28; D-056 accepted)

Long/short pairs among A-share listed ETFs. Written as a research track first (notebooks over lake data);
promoted to `strategy`-level classes in `portfolio`/`back_testing` only if the research passes its bar.

## 1. What can actually be shorted in this market
| Short leg | Mechanism | Practical notes |
|---|---|---|
| Equity ETF | 融券 (securities lending) on margin-eligible ETFs | eligibility list changes; borrow cost roughly 6–10% p.a. (verify with broker); T+1 for equity ETFs |
| Index exposure | CFFEX futures IH (SSE 50), IF (CSI 300), IC (CSI 500), IM (CSI 1000) | liquid, cheap; basis (usually discount) is itself a signal/cost; margin |
| Cross-border / commodity / bond ETFs | 融券 where eligible; these trade T+0 | QDII ETFs carry premium/discount to NAV |
| Options | synthetic short via put − call on 50/300/500 ETFs | plan 03 data covers it |
Consequence: the pair universe is ETFs with a borrowable short leg **or** pairs where the short leg is an
index future. Single-stock shorting is out of scope.

## 2. Pair families worth testing
| Family | Example pairs | Economic link | Expected behaviour |
|---|---|---|---|
| Same-index, different issuer/exchange | 510300.SH vs 159919.SZ (CSI 300), 510500 vs 159922 (CSI 500), 510050 vs 510710 | identical underlying | tiny, fast-reverting spread; capacity and cost-limited; a data-quality benchmark for the pipeline |
| ETF vs its index future | 510300 vs IF, 510500 vs IC, 510050 vs IH | cash-futures basis | basis mean-reverts to zero at expiry; carry trade rather than pairs |
| Large vs small cap | 510050 (SSE 50) vs 512100 (CSI 1000) / IM | size premium | slow, regime-driven; needs a regime filter (`VIX_PANEL.regime`) |
| Style pairs | 510880 (dividend) vs 159915 (ChiNext), value vs growth ETFs | style rotation | months-long cycles |
| Sector pairs | securities 512880 vs banks 512800; liquor 512690 vs pharma 512010; semis 512480 vs new energy 516160 | shared macro driver, different beta | candidate cointegration |
| Commodity duplicates | gold ETFs 518880 vs 159934 vs 518800 | same underlying | near-arbitrage, T+0 |
| Cross-border duplicates | Nasdaq 513100 vs 159941; HSTECH 513180 vs 513130 | same underlying, premium/discount to NAV | premium spread mean-reverts; check NAV and quota status |
| Bond ETFs | 511010 (treasury) vs 511260 (10y) | duration | duration-neutral spreads |

## 3. Method
1. **Universe**: ETFs from `fund_basic` (market `E`), ≥ 250 sessions history, average daily amount ≥ 20m CNY,
   short-leg eligibility flag (margin target list) or an index-future proxy.
2. **Candidate screening** (per rolling 2-year window): correlation of daily returns ≥ 0.7; Engle-Granger
   cointegration p ≤ 0.05 on log prices; Johansen as cross-check; spread half-life (OU fit) between 3 and 60
   sessions; Hurst exponent < 0.5. Same-index duplicates skip cointegration and use the NAV premium.
3. **Hedge ratio**: rolling OLS on log prices (window 120) or Kalman filter; hedge in CNY notional; futures leg
   sized by contract multiplier and basis-adjusted.
4. **Signal**: spread z-score over the estimation window; enter at |z| ≥ 2, exit at |z| ≤ 0.5, stop at |z| ≥ 4
   or when cointegration fails on refresh; maximum holding = 3 half-lives.
5. **Costs**: ETF commission (no stamp duty), borrow fee accrued daily on the short leg, futures fees and
   margin, bid-ask via `daily` spreads proxy (no quotes); T+1 constraint on equity ETFs (no same-day close).
6. **Evaluation**: per pair and per family: Sharpe, max drawdown, hit rate, mean holding period, turnover,
   capacity (ADV share), sensitivity to entry/exit thresholds, out-of-sample walk-forward (fit 2 y, trade 6 m).
7. **Portfolio**: equal risk across live pairs, family caps, gross exposure cap, `VIX_PANEL.regime` filter for
   size pairs.

## 4. Data to add
| Dataset | Endpoint | Sweep | Purpose |
|---|---|---|---|
| `fund_basic` | `fund_basic` | `market=E` | ETF master (name, index tracked, list date, fund type) |
| `fund_daily` | `fund_daily` | `trade_date` (replace the `option_etfs` enum) | all ETF prices |
| `fund_nav` | `fund_nav` | `nav_date` or per `ts_code` | NAV for premium/discount |
| `fund_share` | `fund_share` | `trade_date` | shares outstanding (flows) |
| `margin_secs` (verify name) | margin target list | `trade_date` | short-leg eligibility |
| `fut_basic`, `fut_daily` | CFFEX futures | `exchange=CFFEX`, `trade_date` | IF/IH/IC/IM prices, settle, oi |
| `index_daily` (have) | | | underlying index for basis |

## 5. Classes (only if promoted from research)
`statistic.CointegrationTest` (Engle-Granger, Johansen), `statistic.OrnsteinUhlenbeckFit` (half-life),
`statistic.KalmanHedgeRatio`; `calculation.EtfPremium` (price vs NAV), `calculation.FuturesBasis`;
`portfolio.PairsConstructor` (`BasePortfolioConstructor`: spread z → target weights per leg);
`back_testing` gains a short-leg borrow-cost and futures-margin `CostModel` variant and a T+1 rule per asset
class. Frames: `PAIR_CANDIDATES`, `SPREAD_PANEL` (date, pair, spread, z, hedge_ratio, half_life).

## 6. Where it sits on the roadmap
A research notebook track after plan 04 phase 1 (read API) and the new ETF/futures datasets: candidate
screening and spread statistics need no strategy code. Promotion to classes lands with plan 06 (portfolio +
backtest), where the pairs constructor and the short-leg cost model are natural additions.

## 7. Open questions
Closed 2026-09-28 with the recommendations: short legs restricted to index futures and T+0 ETF duplicates until a broker 融券 list and fee schedule are supplied; futures only for leveraged/inverse exposure; promotion bar = out-of-sample Sharpe ≥ 1.0 after costs on ≥ 3 pairs in 2 families. Eligibility source: the official SSE/SZSE 融资融券标的 lists (plan 11 ph10, D-065), with the broker's own list as an optional narrowing when supplied.
