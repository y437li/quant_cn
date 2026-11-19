"""Contract tests for lake.BuybackLedger (plan 23 phase 2, D-154)."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd

from quant_cn.lake.buyback_ledger import BuybackLedger
from quant_cn.lake.lake_query import LakeQuery

COLS = ["ts_code", "ann_date", "end_date", "proc", "exp_date", "vol", "amount", "high_limit"]


def _build_rows(rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=COLS)


def _build_ledger() -> BuybackLedger:
    return BuybackLedger(cast(LakeQuery, None))


A = "000001.SZ"
ROWS = _build_rows([
    (A, "20250110", None, "预案", "20260110", None, 1.0e8, 20.0),
    (A, "20250120", None, "股东大会通过", "20260110", None, 1.0e8, 20.0),
    (A, "20250301", "20250228", "实施", None, 1.0e6, 1.5e7, 16.0),
    (A, "20250601", "20250531", "实施", None, 3.0e6, 4.5e7, 16.0),  # cumulative, not +4.5e7
    (A, "20250901", "20250830", "完成", None, 4.0e6, 6.0e7, 16.0),
    (A, "20250910", "20250909", "完成", None, 4.2e6, 6.3e7, 16.0),  # vendor: progress as 完成
])  # fmt: skip


def test_tc_bbl_001_cumulative_and_done() -> None:
    """TC-BBL-001"""
    p = _build_ledger().build_programmes(ROWS, "20251231")
    assert len(p) == 1 and p.loc[0, "executed_amount"] == 6.3e7 and p.loc[0, "state"] == "open"
    assert p.loc[0, "planned_amount"] == 1.0e8 and p.loc[0, "executed_vol"] == 4.2e6
    small = _build_rows([(A, "20250801", None, "预案", "20260801", None, 2e5, 9.0)])  # 限制性股票
    rows = pd.concat([ROWS, small]).sort_values("ann_date")
    q = _build_ledger().build_programmes(rows, "20251231").set_index("plan_date")
    assert (
        q.loc["20250110", "executed_amount"] == 6.3e7 and q.loc["20250801", "executed_amount"] == 0
    )


def test_tc_bbl_002_stop_and_expiry() -> None:
    """TC-BBL-002"""
    rows = _build_rows([
        ("B", "20240105", None, "预案", "20250105", None, 5.0e7, 10.0),
        ("B", "20240601", None, "停止", None, None, None, None),
        ("C", "20240105", None, "预案", "20250105", None, 5.0e7, 10.0),
    ])  # fmt: skip
    p = _build_ledger().build_programmes(rows, "20251231").set_index("ts_code")
    assert p.loc["B", "state"] == "stopped" and p.loc["C", "state"] == "expired"
    assert p.loc["C", "executed_amount"] == 0.0


def test_tc_bbl_003_point_in_time_window() -> None:
    """TC-BBL-003"""
    ledger = _build_ledger()
    p = ledger.build_programmes(ROWS, "20250415")
    assert p.loc[0, "executed_amount"] == 1.5e7 and p.loc[0, "state"] == "open"
    # window 20250614..20251231: cumulative 4.5e7 at the start, 6.0e7 at the end
    assert ledger.compute_executed(ROWS, "20251231", days=200).to_dict() == {A: 6.3e7 - 4.5e7}
    assert ledger.compute_executed(ROWS, "20251231").to_dict() == {A: 6.3e7}
    assert ledger.compute_executed(ROWS, "20250115").empty


def test_tc_bbl_004_seeded() -> None:
    """TC-BBL-004"""
    rows = _build_rows([("D", "20180301", "20180228", "实施", None, 1.0e5, 2.0e6, 30.0)])
    p = _build_ledger().build_programmes(rows, "20181231")
    assert bool(p.loc[0, "seeded"]) and p.loc[0, "planned_amount"] is None
    assert p.loc[0, "executed_amount"] == 2.0e6


def test_tc_bbl_005_same_day_order() -> None:
    """TC-BBL-005"""
    rows = _build_rows([
        (A, "20250110", None, "预案", "20260110", None, 1.0e8, 20.0),
        (A, "20250601", "20250531", "实施", None, 3.0e6, 4.5e7, 16.0),
        (A, "20260101", None, "预案", "20270101", None, 2.0e8, 25.0),
        (A, "20260101", "20251231", "完成", None, 6.0e6, 9.0e7, 16.0),  # the old one's end
        (A, "20260101", None, "预案", "20270101", None, 5.0e7, 25.0),
    ])  # fmt: skip
    ledger = _build_ledger()
    p = ledger.build_programmes(rows, "20260102")
    assert list(p["executed_amount"]) == [9.0e7, 0.0, 0.0]
    assert list(p["planned_amount"]) == [1.0e8, 2.0e8, 5.0e7]
    for seed in range(5):
        shuffled = rows.sample(frac=1.0, random_state=seed)
        pd.testing.assert_frame_equal(ledger.build_programmes(shuffled, "20260102"), p)
