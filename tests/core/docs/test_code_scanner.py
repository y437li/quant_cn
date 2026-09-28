from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.docs.code_scanner import CodeScanner

SOURCE = '''"""Module doc."""
from abc import abstractmethod

LIMIT = 3


class Foo(Base):
    """Mentions Ghost in a docstring only."""

    @property
    def size(self) -> int:
        return LIMIT

    @abstractmethod
    def run(self, clock: Clock) -> Report:
        return helper()

    def _hidden(self) -> None:
        pass


def loose() -> None:
    pass
'''


# TC-CS-001
def test_tc_cs_001_structure(tmp_path: Path) -> None:
    path = tmp_path / "pkg" / "foo.py"
    path.parent.mkdir()
    path.write_text(SOURCE)
    info = CodeScanner().read_module(path, tmp_path)
    assert (
        info.module == "pkg.foo"
        and info.docstring == "Module doc."
        and info.constants == ("LIMIT",)
    )
    (cls,) = info.classes
    assert cls.name == "Foo" and cls.bases == ("Base",) and cls.n_lines == 13
    assert [m.name for m in cls.list_public_methods()] == ["size", "run"]
    assert cls.methods[0].is_property and cls.methods[1].is_abstract
    assert [f.name for f in info.functions] == ["loose"]


# TC-CS-002
def test_tc_cs_002_references(tmp_path: Path) -> None:
    path = tmp_path / "foo.py"
    path.write_text(SOURCE)
    refs = CodeScanner().read_module(path, tmp_path).classes[0].references
    assert {"Base", "Clock", "Report", "helper", "LIMIT"} <= refs
    assert "Ghost" not in refs and "Foo" not in refs


# TC-CS-003
def test_tc_cs_003_syntax_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_text("def (:\n")
    with pytest.raises(SyntaxError, match=r"bad\.py"):
        CodeScanner().read_module(path, tmp_path)
