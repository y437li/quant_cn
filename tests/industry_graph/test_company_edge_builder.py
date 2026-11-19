from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_cn.industry_graph.company_edge_builder import EDGE_COLUMNS, CompanyEdgeBuilder
from quant_cn.industry_graph.counterparty_edge_reader import CounterpartyEdgeReader
from quant_cn.industry_graph.entity_resolver import EntityResolver

RESOLVER = EntityResolver(
    [("300750.SZ", "宁德时代新能源科技股份有限公司"), ("603906.SH", "江苏龙蟠科技股份有限公司")],
    [("300750.SZ", "宁德时代"), ("603906.SH", "龙蟠科技")],
    {"LGES": "x:LG新能源"},
)


def build() -> CompanyEdgeBuilder:
    return CompanyEdgeBuilder(RESOLVER, {"ir": CounterpartyEdgeReader()}, skip_names={"头部客户群"})


def build_rows(items: list[dict[str, object]], **extra: object) -> pd.DataFrame:
    payload = json.dumps({"items": items, **extra}, ensure_ascii=False)
    row = {"ts_code": "603906.SH", "doc_key": "d1", "doc_type": "irm_qa",
           "period": "20251231", "known_on": "20260301", "payload": payload}  # fmt: skip
    return pd.DataFrame([row])


def build_item(name: str, role: str, **kw: object) -> dict[str, object]:
    return {"name": name, "role": role, "evidence": {"quote": "q", "page": 1}, **kw}


# TC-CEB-001
def test_tc_ceb_001_orientation() -> None:
    edges = build().build_edges("ir", build_rows([
        build_item("宁德时代", "customer"), build_item("LGES", "supplier"),
        build_item("华为", "partner"), build_item("龙蟠科技", "customer"),
        build_item("客户一", "customer"), build_item("头部客户群", "customer"),
    ]))  # fmt: skip
    got = list(zip(edges["src"], edges["dst"], edges["relation"], strict=True))
    assert got == [
        ("a:603906.SH", "a:300750.SZ", "customer"),
        ("x:LG新能源", "a:603906.SH", "supplier"),
        ("a:603906.SH", "x:华为", "partner"),
    ]


# TC-CEB-002
def test_tc_ceb_002_period_known_on_and_flow() -> None:
    edges = build().build_edges("ir", build_rows([
        build_item("宁德时代", "customer", period="2024", amount=5, share=10,
                   share_base="营业收入"),
        build_item("LGES", "customer", amount=7, share=30, share_base="应收账款余额"),
    ], dates=["20260115"]))  # fmt: skip
    assert list(edges.columns) == EDGE_COLUMNS
    assert edges["period"].tolist() == ["20241231", "20260115"]
    assert edges["known_on"].tolist() == ["20260115", "20260115"]
    assert edges["share"].iloc[0] == pytest.approx(10)
    assert edges["share"].isna().iloc[1] and edges["amount"].isna().iloc[1]


# TC-CEB-003
def test_tc_ceb_003_bad_rows() -> None:
    frame = build_rows([])
    frame.loc[0, "payload"] = "{bad"
    assert build().build_edges("ir", frame).empty
    with pytest.raises(KeyError):
        build().build_edges("deals", frame)
