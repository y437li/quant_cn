# src/quant_cn/calculation/

L4: domain financial computations over lake frames (CBOE VIX, Black-76); pure, no I/O. May import from: L1. Independent of statistic and pipeline.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `black76_model.py` | Black-76 option prices on a forward and implied volatility by bisection | `Black76Model` |
| `expiry_clock.py` | How time to expiry is measured: calendar minutes (CBOE) or trading sessions | `ExpiryClock` |
| `forward_price_estimator.py` | Forward price and K0 from put-call parity (CBOE white paper step 1) | `ForwardPriceEstimator` |
| `option_chain_builder.py` | Tidy option chains from opt_basic + opt_daily, and per-term strike quote tables | `OptionChainBuilder` |
| `risk_free_curve.py` | Risk-free rate for any tenor from SHIBOR fixings (CALCULATION_DESIGN §2 step 2) | `RiskFreeCurve` |
| `term_interpolator.py` | Blend two term variances to the constant-maturity index (CBOE white paper step 4) | `TermInterpolator` |
| `term_selector.py` | Pick the near and next expiries around the 30-day target (CBOE rule, CALCULATION_DESIGN §2) | `TermSelector` |
| `variance_strip_calculator.py` | Per-term variance from the out-of-the-money option strip (CBOE white paper steps 2-3) | `VarianceStripCalculator` |
| `vix_calculator.py` | CBOE-method volatility index for one option underlying over a date range (plan 03) | `VixCalculator` |
