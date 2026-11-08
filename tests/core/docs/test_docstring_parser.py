from __future__ import annotations

import pytest

from quant_cn.core.docs.docstring_parser import DocstringParser

FULL = """
Purpose:
    Load bars
    from the lake.

Contract:
    Input:
        start: str  -- inclusive
    Output:
        DataFrame
    Raises:
        LakeError  -- missing

Used by:
    pipeline.LocalRunner.run   -- runs it
    lake.Compactor             -- compacts
    Makefile target download

Test cases:
    TC-AB-001  happy
    TC-AB-002  failure
"""


@pytest.fixture
def parser() -> DocstringParser:
    return DocstringParser()


# TC-DSP-001
def test_tc_dsp_001_full_contract(parser: DocstringParser) -> None:
    doc = parser.parse(FULL)
    assert doc.has("Purpose", "Contract", "Input", "Output", "Raises", "Used by", "Test cases")
    assert doc.purpose == "Load bars from the lake."
    assert [(e.cls, e.method) for e in doc.used_by] == [
        ("LocalRunner", "run"),
        ("Compactor", None),
        (None, None),
    ]
    assert doc.used_by[0].note == "runs it"
    assert doc.test_cases == ("TC-AB-001", "TC-AB-002")


# TC-DSP-002
def test_tc_dsp_002_none_yet_and_non_class(parser: DocstringParser) -> None:
    doc = parser.parse("Used by:\n    (none yet)\n")
    assert doc.used_by == () and doc.has("Used by")
    assert parser.parse(FULL).used_by[2].text == "Makefile target download"


# TC-DSP-003
@pytest.mark.parametrize("text", [None, "", "Just a sentence."])
def test_tc_dsp_003_missing_sections(parser: DocstringParser, text: str | None) -> None:
    doc = parser.parse(text)
    assert not doc.has("Purpose") and doc.used_by == () and doc.test_cases == ()


# TC-DSP-004
def test_tc_dsp_004_ids_outside_section_ignored(parser: DocstringParser) -> None:
    doc = parser.parse("Purpose:\n    see TC-XY-009\n\nTest cases:\n    TC-XY-001 a\n")
    assert doc.test_cases == ("TC-XY-001",)


# TC-DSP-005
def test_tc_dsp_005_blocks_and_descriptions(parser: DocstringParser) -> None:
    doc = parser.parse(FULL)
    assert doc.inputs == "start: str  -- inclusive" and doc.outputs == "DataFrame"
    assert doc.raises == "LakeError  -- missing"
    assert doc.test_descriptions == {"TC-AB-001": "happy", "TC-AB-002": "failure"}
