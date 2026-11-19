"""Contract tests for portfolio.OpportunityDocument (plan 21 ph5)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.exceptions import LakeError
from quant_cn.core.opportunity_settings import OpportunitySettings
from quant_cn.portfolio.opportunity_document import OpportunityDocument
from quant_cn.portfolio.opportunity_screen import OUTPUT_COLUMNS

DAY, PREV = "20261118", "20261117"


def _build_frame(rows: list[dict[str, object]], as_of: str) -> pd.DataFrame:
    return pd.DataFrame(rows).assign(as_of=as_of).reindex(columns=OUTPUT_COLUMNS)


TODAY = _build_frame(
    [
        {"ts_code": "A", "name": "a", "rank": 1, "status": "listed", "is_new": False,
         "rules_hit": "retail_leaving,inflow", "missing": "", "pct": 0.05, "np_yoy": float("nan")},
        {"ts_code": "B", "name": "b", "rank": 2, "status": "listed", "is_new": True,
         "rules_hit": "retail_leaving", "missing": "", "pct": 0.1, "lo_streak": 3.0},
        {"ts_code": "C", "name": "c", "rank": 3, "status": "near", "is_new": True,
         "rules_hit": "retail_leaving", "missing": "earnings", "pct": 0.02},
    ],
    DAY,
)  # fmt: skip
PREVIOUS = _build_frame(
    [
        {"ts_code": "A", "name": "a", "status": "listed"},
        {"ts_code": "Z", "name": "z", "status": "near"},
    ],
    PREV,
)


# TC-OPD-001
def test_tc_opd_001_build() -> None:
    doc = OpportunityDocument(OpportunitySettings()).build(TODAY, PREVIOUS, DAY)
    assert [r["code"] for r in doc["rows"]] == ["B", "A", "C"]  # new listed, stayed, near
    a = next(r for r in doc["rows"] if r["code"] == "A")
    assert a["rules_hit"] == ["retail_leaving", "inflow"] and a["missing"] == []
    assert a["np_yoy"] is None and a["pct"] == 0.05
    assert doc["rows"][0]["lo_streak"] == 3 and doc["rows"][2]["missing"] == ["earnings"]
    assert doc["dropped"] == [{"code": "Z", "name": "z", "status": "near"}]
    assert doc["as_of"] == DAY and doc["previous_as_of"] == PREV and doc["rules"]["top_n"] == 10
    empty = OpportunityDocument(OpportunitySettings()).build(
        pd.DataFrame(columns=OUTPUT_COLUMNS), pd.DataFrame(columns=OUTPUT_COLUMNS), DAY
    )
    assert empty["rows"] == [] and empty["as_of"] == DAY and empty["previous_as_of"] is None


# TC-OPD-002
def test_tc_opd_002_write(tmp_path: Path) -> None:
    builder = OpportunityDocument(OpportunitySettings())
    doc = builder.build(TODAY, PREVIOUS, DAY)
    path = builder.write(doc, tmp_path)
    assert path.name == "opportunities.json"
    assert json.loads(path.read_text(encoding="utf-8"))["rows"][0]["code"] == "B"
    with pytest.raises(LakeError):
        builder.write(doc, tmp_path / "missing")
