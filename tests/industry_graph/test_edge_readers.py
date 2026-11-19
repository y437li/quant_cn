from __future__ import annotations

import json

import pytest

from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader
from quant_cn.industry_graph.counterparty_edge_reader import CounterpartyEdgeReader
from quant_cn.industry_graph.deal_edge_reader import DealEdgeReader
from quant_cn.industry_graph.top_five_edge_reader import TopFiveEdgeReader


# TC-BER-001
@pytest.mark.parametrize(
    ("text", "want"),
    [("2025", "20251231"), ("2025年", "20251231"), ("2025H1", "20250630"),
     ("2025年上半年", "20250630"), ("2025Q3", "20250930"), ("20251231", "20251231"),
     ("2024-2025", None), (None, None), ("近年", None)],
)  # fmt: skip
def test_tc_ber_001_build_period(text: str | None, want: str | None) -> None:
    assert BaseEdgeReader.build_period(text) == want


# TC-CER-001
def test_tc_cer_001_items() -> None:
    payload = {"items": [
        {"name": "宁德时代", "role": "customer", "period": "2025", "amount": 3.5, "unit": "亿元",
         "share": 18.6, "share_base": "营业收入", "is_named": True,
         "evidence": {"quote": "客户一为宁德时代", "page": 3}},
        {"name": "客户二", "role": "customer", "is_named": False, "evidence": {}},
        {"name": "华为", "role": "mention", "evidence": {}},
        {"name": "子公司A", "role": "subsidiary", "evidence": {"quote": "q", "page": 1}},
    ]}  # fmt: skip
    items = CounterpartyEdgeReader().list_items(payload)
    assert [(i.name, i.relation) for i in items] == [("宁德时代", "customer"), ("子公司A", "holds")]
    first = items[0]
    assert (first.period, first.share_base, first.quote, first.page) == (
        "20251231",
        "营业收入",
        "客户一为宁德时代",
        3,
    )


# TC-CER-002
def test_tc_cer_002_dates() -> None:
    payload = {"dates": ["20240102", "20240305"], "items": [
        {"name": "小米", "role": "customer", "stage": "denied",
         "evidence": {"quote": "q", "page": 2}}]}  # fmt: skip
    assert CounterpartyEdgeReader().list_items(payload)[0].known_on == "20240305"
    del payload["dates"]
    assert CounterpartyEdgeReader().list_items(payload)[0].known_on is None
    apps = {"counterparties": [{"name": "华为", "role": "partner", "evidence": {}}]}
    assert CounterpartyEdgeReader("counterparties").list_items(apps)[0].relation == "partner"


# TC-TFR-001
def test_tc_tfr_001_top_five() -> None:
    payload = {
        "customers": json.dumps({"rows": [
            {"rank": 1, "name": "宁德时代", "amount": 2.7e9, "pct": 56.65, "anon": False},
            {"rank": 2, "name": "客户二", "amount": 6.2e8, "pct": 13.01, "anon": True}]}),
        "suppliers": {"rows": [{"rank": 1, "name": "江西赣锋", "amount": 1e8, "pct": 5.0}]},
    }  # fmt: skip
    items = TopFiveEdgeReader().list_items(payload)
    assert [(i.name, i.relation, i.share_base) for i in items] == [
        ("宁德时代", "customer", "营业收入"),
        ("江西赣锋", "supplier", "采购总额"),
    ]
    assert items[0].share == pytest.approx(56.65) and items[0].unit == "元"
    assert TopFiveEdgeReader().list_items({"customers": "{bad", "suppliers": None}) == []


# TC-DER-001
def test_tc_der_001_deals() -> None:
    payload = {"items": [
        {"kind": "joint_venture", "target": "瑞瓷电子材料有限公司", "stake": 45, "amount": 2025,
         "unit": "万元", "status": "approved", "evidence": {"quote": "q", "page": 1}},
        {"kind": "disposal", "target": "甲公司", "evidence": {}},
        {"kind": "project", "target": "泰国工厂", "evidence": {}},
        {"kind": "fund", "target": " ", "evidence": {}},
    ]}  # fmt: skip
    items = DealEdgeReader().list_items(payload)
    assert [(i.name, i.relation, i.stage, i.detail) for i in items] == [
        ("瑞瓷电子材料有限公司", "invests_in", "approved", "joint_venture")
    ]
    assert items[0].share == 45 and items[0].share_base == "持股比例"
