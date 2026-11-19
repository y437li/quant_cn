# src/quant_cn/risk/

L5: Barra-style (CNE5 family) multi-factor risk model for A-shares (RISK_MODEL_DESIGN, plan 05, D-045, D-127). May import from: L1-L4. Never imports `factor` (and vice versa); `portfolio` / `back_testing` consume its frames only.

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_risk_model.py` | The risk-model extension point: snapshot per session, portfolio risk | `BaseRiskModel` |
| `bayesian_shrinker.py` | Bayesian shrinkage of specific risk toward size-group means | `BayesianShrinker` |
| `descriptor_builder.py` | Raw CNE5 descriptors per universe member and session | `DescriptorBuilder` |
| `eigenfactor_adjuster.py` | Eigenfactor risk adjustment by Monte-Carlo simulation | `EigenfactorAdjuster` |
| `ewm_window.py` | Exponentially weighted sums over a fixed trailing window | `EwmWindow` |
| `exposure_standardizer.py` | Descriptors -> standardised, orthogonalised, filled style and industry exposures | `ExposureStandardizer` |
| `factor_covariance_estimator.py` | EWMA + Newey-West factor covariance with eigen and regime adjustments | `FactorCovarianceEstimator` |
| `factor_monitor_builder.py` | Factor monitor for the chain app: window returns, forecast / realized vol, sigma move and daily series from the stored risk frames (plan 15 ph7c, D-132) | `FactorMonitorBuilder` |
| `factor_return_estimator.py` | Daily constrained WLS factor returns and residuals | `FactorReturnEstimator` |
| `fundamental_descriptors.py` | Value, leverage and growth descriptors from PIT statements | `FundamentalDescriptors` |
| `analyst_descriptors.py` | CNE5 analyst descriptors EPFWD, EGRSF, EGRLF from the consensus panel (plan 37) | `AnalystDescriptors` |
| `price_descriptors.py` | Beta, momentum, volatility and liquidity descriptors on return matrices | `PriceDescriptors` |
| `risk_decomposer.py` | Euler risk attribution of a portfolio (and active vs benchmark) | `RiskDecomposer` |
| `risk_input_loader.py` | PIT panels for one fitting window through the lake readers | `RiskInputs`, `RiskInputLoader` |
| `risk_model.py` | The CNE5-style model: fitting stages and stored-frame reads | `RiskModel` |
| `risk_model_factory.py` | Build the configured model from RiskModelSettings | `RiskModelFactory` |
| `risk_model_validator.py` | Bias statistics, q-statistics and fit of the model | `RiskModelValidator` |
| `risk_snapshot.py` | One session of a fitted model (X, F, specific vol) | `RiskSnapshot` |
| `specific_risk_estimator.py` | Specific risk: EWMA + NW, structural blend, shrinkage, regime | `SpecificRiskEstimator` |
| `structural_specific_risk.py` | Structural model of specific vol for thin histories | `StructuralSpecificRisk` |
| `volatility_regime_adjuster.py` | Volatility regime adjustment (bias-statistic multiplier) | `VolatilityRegimeAdjuster` |
