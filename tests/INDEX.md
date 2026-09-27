# tests/

Mirrors `src/quant_cn`; one `test_<module>.py` per module, one test per TC ID (CODING_STANDARD §6).

## Folders
| Folder | Purpose |
|---|---|
| [`back_testing/`](back_testing/INDEX.md) | tests for `quant_cn.back_testing` |
| [`core/`](core/INDEX.md) | tests for `quant_cn.core` |
| [`data_loading/`](data_loading/INDEX.md) | tests for `quant_cn.data_loading` |
| [`lake/`](lake/INDEX.md) | tests for `quant_cn.lake` |
| [`pipeline/`](pipeline/INDEX.md) | tests for `quant_cn.pipeline` |
| [`portfolio/`](portfolio/INDEX.md) | tests for `quant_cn.portfolio` |
| [`statistic/`](statistic/INDEX.md) | tests for `quant_cn.statistic` |
| [`visualization/`](visualization/INDEX.md) | tests for `quant_cn.visualization` |

_Planned (plan 01 phase 1): `conftest.py` (mini lake in tmp_path), `test_contracts.py` (contract + index linter)._
