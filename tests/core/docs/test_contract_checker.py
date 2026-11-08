from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.code_scanner import CodeScanner
from quant_cn.core.docs.contract_checker import ContractChecker
from quant_cn.core.docs.docstring_parser import DocstringParser
from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.registry_reader import RegistryReader
from tests.support import SampleRepo


def build_doc(used_by: str = "(none yet)", tests: str = "TC-TH-001  it works") -> str:
    return (
        f'    """\n    Purpose:\n        Do it.\n\n    Contract:\n        Input:\n            x\n'
        f"        Output:\n            y\n        Raises:\n            (none)\n\n"
        f'    Used by:\n        {used_by}\n\n    Test cases:\n        {tests}\n    """\n'
    )


METHOD = (
    '    def run(self) -> None:\n        """\n        Purpose:\n            Go.\n\n'
    '        Contract:\n            Input:\n                (none)\n        """\n'
)
REGISTRY = (
    "## A. Index\n| Class | Public methods (count) |\n|---|---|\n"
    "| `Thing` | 1 |\n| `User` | 1 |\n\n"
    "## B. Class details\n### `Thing` — `quant_cn.pkg.thing` (L2)\n"
    "| Method | Purpose |\n|---|---|\n| `run` | go |\n\n"
    "### `User` — `quant_cn.pkg.user` (L2)\n| Method | Purpose |\n|---|---|\n| `run` | go |\n\n"
    "## C. Abstract\n## D. Exceptions\n## E. Schemas\n## F. Functions\n"
)


def build_files(**overrides: str) -> dict[str, str]:
    files = {
        "src/quant_cn/pkg/thing.py": "class Thing:\n" + build_doc("pkg.User  -- calls") + METHOD,
        "src/quant_cn/pkg/user.py": "class User:\n"
        + build_doc(tests="TC-US-001  ok")
        + METHOD
        + "    x: Thing\n",
        "tests/test_all.py": (
            "def test_tc_th_001_ok() -> None: ...\n\ndef test_tc_us_001_ok() -> None: ...\n"
        ),
        ".claude/CLASS_REGISTRY.md": REGISTRY,
    }
    files.update(overrides)
    return files


def run_contracts(root: Path) -> list[str]:
    checker = ContractChecker(
        root, CodeScanner(), DocstringParser(), RegistryReader(MarkdownTableReader())
    )
    return [f.message for f in checker.run()]


# TC-CC-001
def test_tc_cc_001_sections(tmp_path: Path) -> None:
    bare = (
        'class User:\n    """Purpose:\n    x\n"""\n'
        '    def run(self) -> None:\n        """No contract."""\n    x: Thing\n'
    )
    root = SampleRepo.build_repo(tmp_path / "r", build_files(**{"src/quant_cn/pkg/user.py": bare}))
    messages = run_contracts(root)
    assert any(m.startswith("class User missing") for m in messages)
    assert "User.run missing ['Purpose', 'Contract']" in messages


# TC-CC-002
def test_tc_cc_002_test_parity(tmp_path: Path) -> None:
    tests = "def test_tc_th_001_ok() -> None: ...\n\ndef test_tc_zz_001_orphan() -> None: ...\n"
    root = SampleRepo.build_repo(tmp_path / "r", build_files(**{"tests/test_all.py": tests}))
    messages = run_contracts(root)
    assert "TC-US-001 has no test function" in messages
    assert "TC-ZZ-001 test is not in any docstring" in messages


# TC-CC-003
def test_tc_cc_003_used_by(tmp_path: Path) -> None:
    root = SampleRepo.build_repo(tmp_path / "r", build_files())
    assert run_contracts(root) == []
    thing = "class Thing:\n" + build_doc("pkg.Ghost  -- nope") + METHOD
    user = (
        "class User:\n"
        + build_doc("pkg.Thing.missing  -- nope", tests="TC-US-001  ok")
        + METHOD
        + "    x: Thing\n"
    )
    root = SampleRepo.build_repo(
        tmp_path / "s",
        build_files(**{"src/quant_cn/pkg/thing.py": thing, "src/quant_cn/pkg/user.py": user}),
    )
    messages = run_contracts(root)
    assert "Thing Used by misses User" in messages
    assert "Thing Used by names unknown class pkg.Ghost" in messages
    assert "User Used by names unknown method pkg.Thing.missing" in messages


# TC-CC-004
def test_tc_cc_004_registry(tmp_path: Path) -> None:
    registry = REGISTRY.replace("| `User` | 1 |\n", "| `Gone` | 1 |\n").replace(
        "| `run` | go |\n\n## C.", "| `walk` | go |\n\n## C."
    )
    root = SampleRepo.build_repo(
        tmp_path / "r", build_files(**{".claude/CLASS_REGISTRY.md": registry})
    )
    messages = run_contracts(root)
    assert "User missing from section A" in messages
    assert "registry lists Gone, not found in src" in messages
    assert (
        "User.run method table differs from code" in messages
        and "User.walk method table differs from code" in messages
    )


# TC-CC-005
def test_tc_cc_005_structure(tmp_path: Path) -> None:
    extra = {
        "src/quant_cn/other/thing.py": "class Thing:\n"
        + build_doc(tests="TC-TH-001  dup")
        + METHOD,
        "src/quant_cn/pkg/tools.py": "def helper() -> None: ...\n",
    }
    root = SampleRepo.build_repo(tmp_path / "r", build_files(**extra))
    messages = run_contracts(root)
    assert any(m.startswith("class Thing also defined in") for m in messages)
    assert "loose function helper outside core/utils" in messages
