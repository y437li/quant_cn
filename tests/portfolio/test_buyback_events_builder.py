"""Contract tests for portfolio.BuybackEventsBuilder (plan 23 ph6)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pytest

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.buyback_events_builder import BuybackEventsBuilder

EV = pd.DataFrame(
    [
        ("A", "20261110", "预案", 3e9, 30.0, "20271110", "甲"),  # 3% of 1,000 亿
        ("B", "20261111", "预案", 5e8, 10.0, "20271111", "乙"),  # 0.5%: not large
        ("C", "20261112", "预案", 2.5e9, 20.0, "20271112", "丙"),  # 5% of 500 亿
        ("B", "20261112", "实施", 1e8, 10.0, None, "乙"),
    ],
    columns=["ts_code", "ann_date", "proc", "amount", "high_limit", "exp_date", "name"],
)
MV = pd.DataFrame(
    {"total_mv": [1e7, 1e7, 5e6], "close": [25.0, 9.0, 18.0]},
    index=pd.Index(["A", "B", "C"], name="ts_code"),
)


class TwoQuery:
    def sql(self, query: str, params: Any = None) -> pd.DataFrame:
        return EV if "repurchase" in query else MV.reset_index()


def test_tc_beb_001_compute() -> None:
    """TC-BEB-001"""
    doc = BuybackEventsBuilder(cast(LakeQuery, None)).compute(EV, MV, "20261113", ["B"])
    assert [p["code"] for p in doc["large_plans"]] == ["C", "A"] and doc["large_plans"][0][
        "pct"
    ] == 5.0
    assert doc["large_plans"][1]["high_limit"] == 30.0 and doc["large_plans"][1]["close"] == 25.0
    assert [(e["code"], e["proc"]) for e in doc["book_events"]] == [("B", "实施"), ("B", "预案")]


def test_tc_beb_002_write(tmp_path: Path) -> None:
    """TC-BEB-002"""
    b = BuybackEventsBuilder(cast(LakeQuery, TwoQuery()))
    with pytest.raises(LakeError):
        b.write(tmp_path / "nope", "20261113", [])
    path = b.write(tmp_path, "20261113", ["A"])
    assert json.loads(path.read_text(encoding="utf-8"))["book_events"][0]["code"] == "A"
