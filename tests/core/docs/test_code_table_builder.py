from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.code_table_builder import COLUMNS, CodeTableBuilder
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.registry_reader import RegistryReader
from tests.support import SampleRepo

THING = '''class Thing:
    """
    Purpose:
        Do it.

    Contract:
        Input:
            x: int
        Output:
            int
        Raises:
            (none)

    Used by:
        pkg.User.run  -- calls

    Test cases:
        TC-TH-001  it works
    """

    def run(self) -> None:
        """
        Purpose:
            Go.

        Contract:
            Input:
                (none)
        """
'''
REGISTRY = """\
## A. Index
| Class | Tests | Added |
|---|---|---|
| `Thing` | t.py (1) | 2026-09-27 |

## B. Class details
### `Thing` — `quant_cn.pkg.thing` (L2)
| Method | Purpose | Input -> Output | Raises |
|---|---|---|---|
| `run` | go | — -> None | — |

## C.
## D.
## E.
## F.
"""


def build_tables(root: Path) -> dict[str, pd.DataFrame]:
    builder = CodeTableBuilder(
        root, CodeScanner(), DocstringParser(), RegistryReader(MarkdownTableReader())
    )
    return builder.build_tables()


# TC-CTB-001
def test_tc_ctb_001_tables(tmp_path: Path) -> None:
    files = {
        "src/quant_cn/pkg/thing.py": THING,
        ".claude/CLASS_REGISTRY.md": REGISTRY,
        "tests/test_thing.py": "def test_tc_th_001_ok() -> None: ...\n",
    }
    tables = build_tables(SampleRepo.build_repo(tmp_path / "r", files))
    assert set(tables) == set(COLUMNS) and all(
        list(tables[k].columns) == COLUMNS[k] for k in COLUMNS
    )
    cls = tables["classes"].iloc[0]
    assert (cls["name"], cls["module"], cls["layer"], cls["added"]) == (
        "Thing",
        "quant_cn.pkg.thing",
        None,
        "2026-09-27",
    )
    assert tables["methods"][["name", "input_output"]].values.tolist() == [["run", "— -> None"]]
    assert tables["used_by"][["caller_class", "caller_method"]].values.tolist() == [["User", "run"]]
    assert tables["test_cases"][["tc_id", "description", "test_function"]].values.tolist() == [
        ["TC-TH-001", "it works", "test_tc_th_001_ok"]
    ]
    assert len(tables["contracts"]) == 2


# TC-CTB-002
def test_tc_ctb_002_not_in_registry(tmp_path: Path) -> None:
    root = SampleRepo.build_repo(tmp_path / "r", {"src/quant_cn/pkg/thing.py": THING})
    tables = build_tables(root)
    assert tables["classes"]["in_registry"].tolist() == [False]
    assert tables["methods"]["in_registry"].tolist() == [False]
