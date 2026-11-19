from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.phase_status_parser import PhaseStatusParser
from quant_cn.core.docs.plan_reader import PlanReader
from quant_cn.core.docs.plan_status_checker import PlanStatusChecker

PLAN = """# 03 — Sample

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | a | b | c | — | done (f40cea8) |
| 2 | d | e | f | 1 | approved, waiting |
"""


# TC-PSC-001
def test_tc_psc_001_invalid_status(tmp_path: Path) -> None:
    folder = tmp_path / "plans" / "execution"
    folder.mkdir(parents=True)
    (folder / "03_sample.md").write_text(PLAN)
    (folder / "ROADMAP.md").write_text("| a | approved |\n")
    checker = PlanStatusChecker(tmp_path, PlanReader(MarkdownTableReader(), PhaseStatusParser()))
    findings = checker.run()
    assert len(findings) == 1
    finding = findings[0]
    assert (finding.path, finding.rule) == ("plans/execution/03_sample.md", "plans")
    assert finding.message.startswith("phase 2:")
    reader = PlanReader(MarkdownTableReader(), PhaseStatusParser())
    assert PlanStatusChecker(tmp_path / "missing", reader).run() == []
