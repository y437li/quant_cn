from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.index_reader import IndexReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader


# TC-IR-001
def test_tc_ir_001_rows(tmp_path: Path) -> None:
    path = tmp_path / "INDEX.md"
    path.write_text(
        "# src/\n\n## Folders\n| Folder | Purpose |\n|---|---|\n"
        "| [`core/`](core/INDEX.md) | base |\n\n"
        "## Files\n| File | Purpose | Contains |\n|---|---|---|\n| `a.py` | thing | `A`, `B` |\n"
    )
    info = IndexReader(MarkdownTableReader()).read(path)
    assert info.title == "src/" and list(info.folders) == ["core"]
    assert info.files["a.py"].contains == ("A", "B")


# TC-IR-002
def test_tc_ir_002_missing_tables(tmp_path: Path) -> None:
    path = tmp_path / "INDEX.md"
    path.write_text("# empty/\n\nNothing here.\n")
    info = IndexReader(MarkdownTableReader()).read(path)
    assert info.title == "empty/" and info.folders == {} and info.files == {}
