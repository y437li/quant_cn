# src/quant_cn/factor/

L5: factor definitions, factory, preprocessing and evaluation (SRC_DESIGN §2.5). May import from: L1-L4.

## Folders
| Folder | Purpose |
|---|---|
| [`library/`](library/INDEX.md) | TODO purpose |

## Files
| File | Purpose | Contains |
|---|---|---|
| `__init__.py` | package marker |  |
| `base_factor.py` | The factor extension point (SRC_DESIGN §2.5): one value per stock and session, PIT-safe | `FactorInputs`, `BaseFactor` |
| `factor_acceptance.py` | The FACTOR_TESTING_DESIGN §6 acceptance bar applied to a campaign's IC_TEST | `FactorAcceptance` |
| `factor_evaluator.py` | Evaluate a campaign of factors: IC, significance, adjustments, ladders (SRC_DESIGN §2.5) | `FactorReport`, `FactorEvaluator` |
| `factor_factory.py` | Factors from config/factors.yaml and the panels they need (SRC_DESIGN §2.5) | `FactorFactory` |
| `factor_preprocessor.py` | Winsorise, standardise and neutralise factor values per date (SRC_DESIGN §2.5, D-093) | `FactorPreprocessor` |
| `signal_combiner.py` | Combine processed factors into one score (SRC_DESIGN §2.5) | `SignalCombiner` |
