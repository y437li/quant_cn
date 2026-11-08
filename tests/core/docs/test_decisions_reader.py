from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.decisions_reader import DecisionRecord, DecisionsReader
from quant_cn.core.docs.markdown_table import MarkdownTableReader

LOG = """# Decisions Log

| ID | Date | Title | Status | Where it applies |
|---|---|---|---|---|
| D-001 | 2026-09-27 | Plan first | accepted | CLAUDE.md |
| D-002 | 2026-09-27 | No block | proposed | x |

### D-001 Plan first
- Context: new repo.
- Decision (proposed): plan before code.
- Alternatives: none
"""


def read_log(tmp_path: Path) -> list[DecisionRecord]:
    path = tmp_path / "DECISIONS.md"
    path.write_text(LOG)
    return DecisionsReader(MarkdownTableReader()).read(path)


# TC-DR-001
def test_tc_dr_001_rows_and_details(tmp_path: Path) -> None:
    first = read_log(tmp_path)[0]
    assert (first.id, first.status, first.applies_to) == ("D-001", "accepted", "CLAUDE.md")
    assert first.context == "new repo." and first.decision == "plan before code."


# TC-DR-002
def test_tc_dr_002_missing_block(tmp_path: Path) -> None:
    second = read_log(tmp_path)[1]
    assert second.id == "D-002" and second.context == "" and second.decision == ""
