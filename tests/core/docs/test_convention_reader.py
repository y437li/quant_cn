from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.docs.convention_reader import ConventionReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader


# TC-CR-001
def test_tc_cr_001_verbs(tmp_path: Path) -> None:
    path = tmp_path / "N.md"
    path.write_text(
        "| Verb prefix | Meaning |\n|---|---|\n"
        "| `get_` | look up |\n| `run` / `execute` | main job |\n"
    )
    assert ConventionReader(MarkdownTableReader()).read_verbs(path) == ["get_", "run", "execute"]


# TC-CR-002
def test_tc_cr_002_no_table(tmp_path: Path) -> None:
    path = tmp_path / "N.md"
    path.write_text("# nothing\n")
    with pytest.raises(ValueError):
        ConventionReader(MarkdownTableReader()).read_verbs(path)
