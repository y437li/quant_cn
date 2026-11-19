from __future__ import annotations

import pytest

from quant_cn.core.docs.phase_status_parser import PhaseStatus, PhaseStatusParser

CASES = [
    ("todo", ("todo", "", "", "")),
    ("doing: datasets done; `X` open", ("doing", "", "", "datasets done; X open")),
    ("blocked: FRED_API_KEY missing", ("blocked", "", "", "FRED_API_KEY missing")),
    (
        "done (cd174ec, 4d4dfae); resample deferred",
        ("done", "", "cd174ec, 4d4dfae", "(cd174ec, 4d4dfae); resample deferred"),
    ),
    ("done 2026-11-12 (uncommitted)", ("done", "2026-11-12", "", "2026-11-12 (uncommitted)")),
    (
        "todo (approved 2026-11-13; build after 7f)",
        ("todo", "2026-11-13", "", "(approved 2026-11-13; build after 7f)"),
    ),
    (
        "**done** 2026-09-27 — all six phases",
        ("done", "2026-09-27", "", "2026-09-27 — all six phases"),
    ),
    ("Done (17c50b2)", ("done", "", "17c50b2", "(17c50b2)")),
]


# TC-PSP-001
@pytest.mark.parametrize(("text", "expected"), CASES)
def test_tc_psp_001_split(text: str, expected: tuple[str, str, str, str]) -> None:
    status = PhaseStatusParser().parse(text)
    assert (status.state, status.state_date, status.commit, status.note) == expected
    assert status.is_valid


# TC-PSP-002
@pytest.mark.parametrize("text", ["approved 2026-11-13", "", "doner", "in progress"])
def test_tc_psp_002_invalid(text: str) -> None:
    status = PhaseStatusParser().parse(text)
    assert status.state == "" and not status.is_valid
    assert PhaseStatus("", "", "", "").is_valid is False


# TC-PSP-003
def test_tc_psp_003_commit_tokens() -> None:
    status = PhaseStatusParser().parse("done 20261113 (deadbeef) abcdefg 1234567 f40cea8")
    assert status.commit == "f40cea8"
