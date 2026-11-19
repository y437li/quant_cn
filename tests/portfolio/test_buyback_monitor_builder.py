"""Contract tests for portfolio.BuybackMonitorBuilder (plan 32 ph3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from quant_cn.core.exceptions import LakeError
from quant_cn.portfolio.buyback_monitor_builder import BuybackMonitorBuilder
from quant_cn.portfolio.buyback_plan_frame import FRAME_COLUMNS, BuybackPlanFrame
from tests.portfolio.test_buyback_plan_frame import (
    _build_item,
    _build_prog,
    build_labels,
    build_progs,
)


def _build_row(code: str, date: str, **kw: Any) -> dict[str, Any]:
    base = {"kind": "回购", "code": code, "date": date, "end": "20270101", "state": "open",
            "tags": ["注销"], "holders": [], "funding": ["自有"], "loan_bank": None,
            "loan_amount": None, "low": 1e8, "high": 2e8, "executed": 0.0,
            "executed_before": 0.0, "price_cap": 10.0, "labelled": True}  # fmt: skip
    return base | kw


MV = pd.DataFrame(
    {
        "ts_code": list("ABCDE"),
        "total_mv": [1e6] * 5,
        "close": [9.0] * 5,
        "name": list("甲乙丙丁戊"),
    }
).set_index("ts_code")


class _FakeLedger:
    def __init__(self, progs: pd.DataFrame) -> None:
        self._progs = progs

    def read_rows(self, as_of: str) -> pd.DataFrame:
        return pd.DataFrame()

    def build_programmes(self, rows: pd.DataFrame, as_of: str) -> pd.DataFrame:
        return self._progs[self._progs["plan_date"] <= as_of]


class _FakeLabels:
    def __init__(self, labels: pd.DataFrame) -> None:
        self._labels = labels

    def read(self, label_set: str, codes: Any, as_of: str) -> pd.DataFrame:
        return self._labels  # unfiltered on purpose: the builder must not see later labels


class _FakeQuery:
    def sql(self, query: str, params: list[Any]) -> pd.DataFrame:
        if "cninfo_keyword_announcements" in query:
            return pd.DataFrame({"sec_code": [], "ann_date": []})
        if "stk_holdertrade" in query:
            return pd.DataFrame(columns=["ts_code", "ann_date", "holder_name", "change_vol",
                                         "avg_price", "close"])  # fmt: skip
        return MV.reset_index()


# TC-BMB-001
def test_tc_bmb_001_section() -> None:
    rows = pd.DataFrame([
        _build_row("A", "20261115", funding=["专项贷款"], loan_amount=5e7),  # new
        _build_row("B", "20260101", executed=1.5e8, executed_before=0.5e8),  # completed
        _build_row("C", "20260101", state="stopped", end="20261112"),  # stopped
        _build_row("D", "20250101", state="ended", end="20261001"),  # ended before window
        _build_row("E", "20260201", tags=["注销", "维护价值"], low=None),
    ], columns=FRAME_COLUMNS)  # fmt: skip
    s = BuybackMonitorBuilder(_FakeQuery(), None, None, BuybackPlanFrame()).compute_section(  # type: ignore[arg-type]
        rows, MV, "20261117", "20261110"
    )
    assert [r["code"] for r in s["live"]] == ["A", "B", "E"]
    assert {e["code"]: e["event"] for e in s["events"]} == {"A": "new", "B": "completed",
                                                            "C": "stopped"}  # fmt: skip
    b = next(r for r in s["live"] if r["code"] == "B")
    assert b["done_pct"] == 1.5 and b["cap_gap"] == -0.1 and b["mv_pct"] == 0.02
    e = next(r for r in s["live"] if r["code"] == "E")
    assert e["done_pct"] == 0.0 and e["low_yi"] is None  # % done against high when no low
    t = s["totals"]
    assert t["all"] == {"count": 3, "low_yi": 4.0, "high_yi": 6.0, "executed_yi": 1.5}
    assert {g["label"]: g["count"] for g in t["by_tag"]} == {"注销": 3, "维护价值": 1}
    assert t["loan"] == {"count": 1, "loan_yi": 0.5}
    assert sum(m["count"] for m in s["months"]) == 5


# TC-BMB-002
def test_tc_bmb_002_build_and_write(tmp_path: Path) -> None:
    progs = build_progs([_build_prog("A", 1, "20261112", 0.0),
                         _build_prog("B", 1, "20261120", 0.0)])  # fmt: skip
    labels = build_labels([
        ("A", "d1", "20261112", [_build_item("回购", purpose=["注销"])]),
        ("C", "d2", "20261113", [_build_item("增持", holder_type=["控股股东"])]),
        ("C", "d3", "20261120", [_build_item("增持", holder_type=["董监高"], amount_low=9e8)]),
    ])  # fmt: skip
    b = BuybackMonitorBuilder(_FakeQuery(), _FakeLedger(progs), _FakeLabels(labels),  # type: ignore[arg-type]
                              BuybackPlanFrame())  # fmt: skip
    path = b.write(tmp_path, "20261117")
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "buyback_monitor.json"
    assert [r["code"] for r in doc["buyback"]["live"]] == ["A"]
    assert doc["buyback"]["live"][0]["tags"] == ["注销"]
    assert [r["tags"] for r in doc["increase"]["live"]] == [["控股股东"]]
    with pytest.raises(LakeError):
        b.write(tmp_path / "missing", "20261117")
