# src/quant_cn/factor/library/

One BaseFactor subclass per module, registered by class name; listed in config/factors.yaml.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `dividend_yield_factor.py` | Dividend yield: trailing 12-month dividends over market cap (FACTOR_LIBRARY §1 DP, D-148) | `DividendYieldFactor` |
| `earnings_yield_factor.py` | EP TTM: trailing net profit over market value (FACTOR_LIBRARY §8) | `EarningsYieldFactor` |
| `intraday_reversal_factor.py` | Intraday high-turnover reversal: minus intraday returns on the busiest of the last 21 sessions (plan 25) | `IntradayReversalFactor` |
| `pricing_gap_factor.py` | Linear-pricing gap: -log(market value / consensus value with fading growth), higher = cheaper (plan 36) | `PricingGapFactor` |
| `retail_gauge_factor.py` | minus the latest 散户温度计 reading, higher = retail leaving (plan 21 ph6) | `RetailGaugeFactor` |
| `momentum_factor.py` | Momentum 12-1: past-year return skipping the last month (FACTOR_LIBRARY §8) | `MomentumFactor` |
| `profit_growth_factor.py` | Profit growth: year-on-year change of TTM net profit (FACTOR_LIBRARY §8) | `ProfitGrowthFactor` |
| `reversal_factor.py` | Short-term reversal: minus the last month's return (FACTOR_LIBRARY §8) | `ReversalFactor` |
| `roe_factor.py` | ROE TTM: trailing net profit over latest equity (FACTOR_LIBRARY §8) | `RoeFactor` |
| `turnover_factor.py` | Turnover: minus the mean free-float turnover over 60 sessions (FACTOR_LIBRARY §8) | `TurnoverFactor` |
