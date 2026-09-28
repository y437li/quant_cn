from __future__ import annotations

from quant_cn.core.docs.markdown_table import MarkdownTableReader

DOC = """# Title

## Folders
| Folder | Purpose |
|---|---|
| [`core/`](core/INDEX.md) | base classes |

## Files
| File | Purpose | Contains |
|---|---|---|
| `a.py` | uses `x \\| y` | `A`, `B` |
"""


# TC-MTR-001
def test_tc_mtr_001_tables_and_headings() -> None:
    tables = MarkdownTableReader().read(DOC)
    assert [t.heading for t in tables] == ["Folders", "Files"]
    assert tables[1].header == ("File", "Purpose", "Contains")
    assert tables[1].get_column("File") == ["`a.py`"]


# TC-MTR-002
def test_tc_mtr_002_escaped_pipe_and_separator() -> None:
    files = MarkdownTableReader().read(DOC)[1]
    assert len(files.rows) == 1
    assert files.rows[0][1] == "uses `x | y`"


# TC-MTR-003
def test_tc_mtr_003_list_ticked() -> None:
    assert MarkdownTableReader().list_ticked("`A`, `B` and `C`") == ["A", "B", "C"]
