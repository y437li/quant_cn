# src/quant_cn/statistic/

L4: factor stats (IC, quantile returns), descriptive stats, regressions. May import from: L1–L3.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `block_bootstrap.py` | Stationary and circular block bootstrap of time series (FACTOR_TESTING_DESIGN §10) | `BlockBootstrap` |
| `hac_variance.py` | Newey-West / Bartlett HAC variance of a mean (FACTOR_TESTING_DESIGN §10) | `HacVariance` |
| `ic_calculator.py` | Tradeable forward returns and cross-sectional information coefficients (§10, §11) | `IcCalculator` |
| `ic_significance.py` | Single-factor significance tests on an IC series (FACTOR_TESTING_DESIGN §2, §10) | `IcSignificance` |
| `multiple_testing_adjuster.py` | Multiple-testing corrections across a campaign's factors (FACTOR_TESTING_DESIGN §3, §10) | `MultipleTestingAdjuster` |
| `neutralizer.py` | Cross-sectional neutralisation against industry and size (plan 04 phase 2) | `Neutralizer` |
| `quantile_returns.py` | Forward returns by factor quantile (plan 04 phase 2) | `QuantileReturns` |
| `return_stats.py` | Descriptive statistics of a return series (plan 04 phase 2) | `ReturnStats` |
| `standardizer.py` | Cross-sectional z-scores of factor values (plan 04 phase 2) | `Standardizer` |
| `trial_log.py` | Append-only record of every variant evaluated in a campaign (FACTOR_TESTING_DESIGN §5) | `TrialLog` |
| `winsorizer.py` | Cross-sectional winsorisation of factor values (plan 04 phase 2) | `Winsorizer` |
