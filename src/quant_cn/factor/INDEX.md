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
| `factor_factory.py` | Factors from config/factors.yaml and the panels they need (SRC_DESIGN §2.5) | `FactorFactory` |
