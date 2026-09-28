from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.registry_reader import RegistryReader

REGISTRY = """# Class Registry

## A. Index
| Class | Module | Public methods (count) |
|---|---|---|
| `Foo` | `quant_cn.x.foo` | 1 |

## B. Class details
### `PascalName` — `quant_cn.package.module` (L?)
| Method | Purpose |
|---|---|
| `method_a(x)` | template |

### `Foo` — `quant_cn.x.foo` (L2)
| Method | Purpose |
|---|---|
| `__init__` | wire |
| `run` | go |
| `_helper` (private) | long helper |

## C. Abstract base classes
| Class | Module |
|---|---|
| `BaseFoo` | `quant_cn.x.base_foo` |

## D. Exceptions
| Class | Module |
|---|---|
| `FooError` | `quant_cn.core.exceptions` |

## E. Schemas
| Schema | Module |
|---|---|
| `PRICE_PANEL` | `quant_cn.core.frames` |

## F. Allowed standalone functions
"""


# TC-RR-001
def test_tc_rr_001_sections(tmp_path: Path) -> None:
    path = tmp_path / "CLASS_REGISTRY.md"
    path.write_text(REGISTRY)
    info = RegistryReader(MarkdownTableReader()).read(path)
    assert list(info.index) == ["Foo"] and info.index["Foo"]["Public methods (count)"] == "1"
    assert set(info.methods) == {"Foo"}
    assert (
        info.abstract == {"BaseFoo"}
        and info.exceptions == {"FooError"}
        and info.schemas == {"PRICE_PANEL"}
    )


# TC-RR-002
def test_tc_rr_002_method_names(tmp_path: Path) -> None:
    path = tmp_path / "CLASS_REGISTRY.md"
    path.write_text(REGISTRY)
    info = RegistryReader(MarkdownTableReader()).read(path)
    assert info.methods["Foo"] == ["__init__", "run", "_helper"]


# TC-RR-003
def test_tc_rr_003_method_rows(tmp_path: Path) -> None:
    path = tmp_path / "CLASS_REGISTRY.md"
    path.write_text(REGISTRY)
    rows = RegistryReader(MarkdownTableReader()).read(path).method_rows["Foo"]
    assert rows[1] == {"Method": "`run`", "Purpose": "go"}
