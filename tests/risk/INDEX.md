# tests/risk/

Tests for `quant_cn.risk` (plan 05). No network, no files outside `tmp_path`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `risk_fakes.py` | RiskInputs built from a synthetic market (no lake) | `InputsBuilder` |
| `sample_risk_lake.py` | mini lake: prices, caps, Shenwan membership, one statement, universe | `SampleRiskLake` |
| `synthetic_market.py` | synthetic market with a planted factor structure (RISK_MODEL_DESIGN §6) | `SyntheticFactorMarket` |
| `test_base_risk_model.py` | tests for `base_risk_model`, one function per TC ID | `FixedModel` |
| `test_bayesian_shrinker.py` | tests for `bayesian_shrinker`, one function per TC ID |  |
| `test_descriptor_builder.py` | tests for `descriptor_builder`, one function per TC ID |  |
| `test_eigenfactor_adjuster.py` | tests for `eigenfactor_adjuster`, one function per TC ID |  |
| `test_ewm_window.py` | tests for `ewm_window`, one function per TC ID |  |
| `test_exposure_standardizer.py` | tests for `exposure_standardizer`, one function per TC ID |  |
| `test_factor_covariance_estimator.py` | tests for `factor_covariance_estimator`, one function per TC ID |  |
| `test_factor_monitor_builder.py` | tests for `factor_monitor_builder`, one function per TC ID |  |
| `test_factor_return_estimator.py` | tests for `factor_return_estimator`, one function per TC ID |  |
| `test_fundamental_descriptors.py` | tests for `fundamental_descriptors`, one function per TC ID |  |
| `test_price_descriptors.py` | tests for `price_descriptors`, one function per TC ID |  |
| `test_risk_decomposer.py` | tests for `risk_decomposer`, one function per TC ID |  |
| `test_risk_input_loader.py` | tests for `risk_input_loader`, one function per TC ID |  |
| `test_risk_model.py` | tests for `risk_model`, one function per TC ID |  |
| `test_risk_model_factory.py` | tests for `risk_model_factory`, one function per TC ID |  |
| `test_risk_model_validator.py` | tests for `risk_model_validator`, one function per TC ID | `FlatModel` |
| `test_risk_snapshot.py` | tests for `risk_snapshot`, one function per TC ID |  |
| `test_specific_risk_estimator.py` | tests for `specific_risk_estimator`, one function per TC ID |  |
| `test_structural_specific_risk.py` | tests for `structural_specific_risk`, one function per TC ID |  |
| `test_volatility_regime_adjuster.py` | tests for `volatility_regime_adjuster`, one function per TC ID |  |
