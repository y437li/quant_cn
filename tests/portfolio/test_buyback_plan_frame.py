"""Contract tests for portfolio.BuybackPlanFrame (plan 32 ph3)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from quant_cn.lake.buyback_ledger import PROGRAMME_COLUMNS
from quant_cn.portfolio.buyback_plan_frame import BuybackPlanFrame


def _build_item(kind: str, **kw: Any) -> dict[str, Any]:
    base = {"kind": kind, "purpose": [], "holder_type": [], "holders": [], "funding": ["自有"],
            "loan_bank": None, "loan_amount": None, "amount_low": 1e8, "amount_high": 2e8,
            "shares_low": None, "shares_high": None, "price_cap": 10.0,
            "period_months": 12.0}  # fmt: skip
    return base | kw


def build_labels(rows: list[tuple[str, str, str, list[dict[str, Any]]]]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"ts_code": c, "doc_key": k, "known_on": d, "payload": json.dumps({"items": items})}
         for c, k, d, items in rows]
    )  # fmt: skip


TRADE_COLUMNS = ["ts_code", "ann_date", "holder_name", "change_vol", "avg_price", "close"]


def _build_prog(code: str, n: int, plan: str, executed: float, **kw: Any) -> dict[str, Any]:
    base = {"ts_code": code, "programme": n, "plan_date": plan, "planned_amount": 2e8,
            "high_limit": 10.0, "exp_date": "20271231", "state": "open", "last_date": plan,
            "executed_amount": executed, "executed_vol": 0.0, "seeded": False}  # fmt: skip
    return base | kw


def build_progs(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=PROGRAMME_COLUMNS)


# TC-BPF-001
def test_tc_bpf_001_items() -> None:
    labels = build_labels([
        ("A.SZ", "d1", "20260105", [_build_item("回购"), _build_item("增持")]),
        ("A.SZ", "d2", "20260301", [_build_item("回购")]),
    ])  # fmt: skip
    items = BuybackPlanFrame().build_items(labels, "20260201")
    assert list(items["kind"]) == ["回购", "增持"]
    assert set(items["doc_key"]) == {"d1"}


# TC-BPF-002
def test_tc_bpf_002_buybacks() -> None:
    f = BuybackPlanFrame()
    labels = build_labels([
        ("A.SZ", "plan", "20260105", [_build_item("回购", purpose=["注销"])]),
        ("A.SZ", "report", "20260120", [_build_item("回购", funding=["专项贷款"],
                                                    loan_bank="某银行", loan_amount=1.5e8)]),
        ("A.SZ", "plan2", "20260601", [_build_item("回购", purpose=["维护价值"])]),
    ])  # fmt: skip
    items = f.build_items(labels, "20261231")
    progs = build_progs([
        _build_prog("A.SZ", 1, "20260105", 1.2e8),
        _build_prog("A.SZ", 2, "20260601", 0.0),
        _build_prog("000002.SZ", 1, "20260110", 0.0),  # restricted-stock title nearby
        _build_prog("C.SZ", 1, "20260110", 0.0, high_limit=0.0),  # no cap, no label
        _build_prog("D.SZ", 1, "20260110", 0.0),  # no label but a cap: kept
        _build_prog("E.SZ", 1, "20231201", 0.0),  # before START
    ])  # fmt: skip
    before = build_progs([_build_prog("A.SZ", 1, "20260105", 0.5e8)])
    restricted = pd.DataFrame({"sec_code": ["000002"], "ann_date": ["20260112"]})
    rows = f.build_buybacks(progs, before, items, restricted)
    assert list(rows["code"]) == ["A.SZ", "A.SZ", "D.SZ"]
    first = rows.iloc[0]
    assert first["tags"] == ["注销"]
    assert first["funding"] == ["自有", "专项贷款"]
    assert first["loan_bank"] == "某银行" and first["loan_amount"] == 1.5e8
    assert first["executed"] == 1.2e8 and first["executed_before"] == 0.5e8
    assert rows.iloc[1]["tags"] == ["维护价值"]
    d = rows.iloc[2]
    assert not d["labelled"] and d["high"] == 2e8 and d["price_cap"] == 10.0


# TC-BPF-003
def test_tc_bpf_003_increases() -> None:
    f = BuybackPlanFrame()
    item = _build_item("增持", holders=["甲公司"], holder_type=["控股股东"], period_months=3.0)
    labels = build_labels([
        ("A.SZ", "plan", "20260105", [item]),
        ("A.SZ", "repeat", "20260106", [item]),
        ("B.SZ", "any", "20261101", [_build_item("增持", period_months=None)]),
    ])  # fmt: skip
    items = f.build_items(labels, "20261117")
    trades = pd.DataFrame([
        ("A.SZ", "20260110", "甲公司", 1e6, 10.0, 11.0),
        ("A.SZ", "20260111", "乙", 1e6, 10.0, 11.0),  # not a named holder
        ("A.SZ", "20260112", "甲公司", 1e6, None, 12.0),  # close when no avg_price
        ("A.SZ", "20260601", "甲公司", 1e6, 10.0, 11.0),  # after the period
        ("B.SZ", "20261110", "丙", 1e6, 5.0, 5.0),
        ("B.SZ", "20261120", "丙", 1e6, 5.0, 5.0),  # after as_of
    ], columns=TRADE_COLUMNS)  # fmt: skip
    rows = f.build_increases(items, trades, "20261117", "20261110")
    assert list(rows["code"]) == ["A.SZ", "B.SZ"]
    a, b = rows.iloc[0], rows.iloc[1]
    assert a["executed"] == 1e7 + 1.2e7 and a["state"] == "ended" and a["end"] == "20260405"
    assert a["tags"] == ["控股股东"]
    assert b["executed"] == 5e6 and b["state"] == "open" and b["end"] == "20270501"
    assert b["executed_before"] == 5e6
