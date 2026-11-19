from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.research_log_checker import MAX_HELD, ResearchLogChecker
from quant_cn.core.docs.research_log_reader import ResearchLogReader

HEAD = (
    "| Date | Slug | Question | Scripts | Outputs | Conclusion | Follow-up |\n"
    "|---|---|---|---|---|---|---|\n"
)
RUN = "research_space/runs/20261113_good_run"


def write_repo(root: Path, rows: list[str], files: dict[str, str]) -> list[Path]:
    (root / RUN).mkdir(parents=True)
    log = root / "research_space" / "RESEARCH_LOG.md"
    log.write_text(HEAD + "\n".join(rows) + "\n", encoding="utf-8")
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8")
    return [Path(rel) for rel in files]


def build(root: Path, files: list[Path], held: list[str], secrets: list[str]) -> ResearchLogChecker:
    reader = ResearchLogReader(MarkdownTableReader())
    return ResearchLogChecker(root, reader, files, held, secrets)


# TC-RSC-001
def test_tc_rsc_001_log_rules(tmp_path: Path) -> None:
    rows = [
        f"| 2026-11-13 | 20261113_good_run | q | `{RUN}/` | o | c | none |",
        f"| 2026-11-13 | Bad-Slug | q | `{RUN}/` | o | c | none |",
        f"| 2026-11-12 | 20261113_other_run | q | `{RUN}/` | o | c | none |",
        "| 2026-11-13 | 20261113_lost_run | q | `research_space/runs/nowhere/` | o | c | none |",
        f"| 2026-11-13 | 20261113_good_run | q | `{RUN}/` | o | c | none |",
    ]
    findings = build(tmp_path, write_repo(tmp_path, rows, {}), [], []).run()
    messages = [f.message for f in findings]
    assert len(findings) == 5  # duplicate counted on both rows
    assert any("Bad-Slug" in m and "YYYYMMDD" in m for m in messages)
    assert any("does not match date 2026-11-12" in m for m in messages)
    assert any("do not exist" in m for m in messages)
    assert sum("used 2 times" in m for m in messages) == 2
    assert {f.rule for f in findings} == {"research"}


# TC-RSC-002
def test_tc_rsc_002_privacy(tmp_path: Path) -> None:
    held = [f"00000{i}.SZ" for i in range(MAX_HELD)]
    files = {
        f"{RUN}/book.py": "HELD = " + repr(held),
        f"{RUN}/cost.py": "cost = 12.345",
        f"{RUN}/clean.py": "codes = " + repr(held[:2]),
        f"{RUN}/INDEX.md": "# run",
    }
    rows = [f"| 2026-11-13 | 20261113_good_run | q | `{RUN}/` | o | c | none |"]
    rels = write_repo(tmp_path, rows, files)
    findings = build(tmp_path, rels, held, ["12.345"]).run()
    assert sorted(Path(f.path).name for f in findings) == ["book.py", "cost.py"]
    assert build(tmp_path, rels, [], ["12.345"]).run() == []
