# tests/factor/

Tests for `quant_cn.factor`; PIT restatement tests on a mini lake (conftest `reader`) and synthetic price paths.

## Files
| File | Purpose | Contains |
|---|---|---|
| `conftest.py` | shared fixtures: Config over copied YAML, mini lake in tmp_path | `reader` |
| `test_base_factor.py` | tests for `base_factor`, one function per TC ID | `ConstantFactor` |
| `test_factor_acceptance.py` | tests for `factor_acceptance`, one function per TC ID |  |
| `test_factor_evaluator.py` | tests for `factor_evaluator`, one function per TC ID |  |
| `test_factor_factory.py` | tests for `factor_factory`, one function per TC ID |  |
| `test_factor_preprocessor.py` | tests for `factor_preprocessor`, one function per TC ID |  |
| `test_fundamental_factors.py` | tests for `fundamental_factors`, one function per TC ID |  |
| `test_price_factors.py` | tests for `price_factors`, one function per TC ID |  |
| `test_signal_combiner.py` | tests for `signal_combiner`, one function per TC ID |  |
