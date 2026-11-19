from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.industry_graph.node_member_builder import MEMBER_COLUMNS, NodeMemberBuilder
from quant_cn.industry_graph.product_matcher import ProductMatcher
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy

COAL = """
sector: {sw_l1: "740000", name: 煤炭}
nodes:
  - {id: SEG_COAL_MINING, type: segment, name: 煤炭开采, name_en: Coal Mining}
  - {id: PROD_COAL_THERMAL, type: product, name: 动力煤, name_en: Thermal Coal, segment: SEG_COAL_MINING}
  - {id: PROD_COAL_COKE, type: product, name: 焦炭, name_en: Coke, segment: SEG_COAL_MINING}
sw_l3_map:
  "740101": [SEG_COAL_MINING]
"""  # noqa: E501


def build_builder(tmp_path: Path) -> NodeMemberBuilder:
    (tmp_path / "740000_coal.yaml").write_text(COAL, encoding="utf-8")
    taxonomy = ProductTaxonomy(tmp_path)
    return NodeMemberBuilder(ProductMatcher(taxonomy), taxonomy, DateCodec())


def build_revenue(*rows: tuple[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        [("601088.SH", "20251231", item, sales) for item, sales in rows],
        columns=["ts_code", "end_date", "bz_item", "bz_sales"],
    )


SW = {"601088.SH": ["740101"]}


# TC-NMB-001
def test_tc_nmb_001_kept_lines(tmp_path: Path) -> None:
    revenue = build_revenue(("产品", 100.0), ("动力煤", 60.0), ("焦炭", 30.0),
                            ("合并抵消", -5.0), ("焦炭：外销", 10.0))  # fmt: skip
    members = build_builder(tmp_path).build_members(revenue, SW)
    assert list(members.columns) == MEMBER_COLUMNS
    got = members[["item", "node_id", "segment", "sector"]].values.tolist()
    assert got == [
        ["动力煤", "PROD_COAL_THERMAL", "SEG_COAL_MINING", "740000"],
        ["焦炭", "PROD_COAL_COKE", "SEG_COAL_MINING", "740000"],
    ]
    assert members["weight"].tolist() == pytest.approx([2 / 3, 1 / 3])


# TC-NMB-002
def test_tc_nmb_002_compound_and_unmatched(tmp_path: Path) -> None:
    revenue = build_revenue(("动力煤及焦炭", 50.0), ("物流服务", 30.0), ("其他", 25.0))
    members = build_builder(tmp_path).build_members(revenue, SW)
    split = members[members["item"] == "动力煤及焦炭"]
    assert sorted(split["node_id"]) == ["PROD_COAL_COKE", "PROD_COAL_THERMAL"]
    assert split["weight"].tolist() == pytest.approx([50 / 210, 50 / 210])
    how = members.set_index("item")["how"].to_dict()
    assert how["物流服务"] == "sector" and how["其他"] == "generic"
    sector = members[members["item"] == "物流服务"].iloc[0]
    assert sector["segment"] == "SEG_COAL_MINING"
    none = build_builder(tmp_path).build_members(revenue, {})
    assert none.set_index("item").loc["物流服务", "how"] == "none"


# TC-NMB-003
def test_tc_nmb_003_known_on_and_empty(tmp_path: Path) -> None:
    builder = build_builder(tmp_path)
    revenue = build_revenue(("动力煤", 60.0), ("焦炭", 30.0))
    dated = builder.build_members(revenue, SW, {("601088.SH", "20251231"): "20260328"})
    assert set(dated["known_on"]) == {"20260328"}
    assert set(builder.build_members(revenue, SW)["known_on"]) == {"20260430"}
    empty = builder.build_members(revenue.iloc[0:0], SW)
    assert empty.empty and list(empty.columns) == MEMBER_COLUMNS


# TC-NMB-004
def test_tc_nmb_004_wrapper_parent(tmp_path: Path) -> None:
    revenue = build_revenue(("持续经营业务", 100.0), ("持续经营业务：动力煤", 70.0),
                            ("持续经营业务：焦炭", 30.0))  # fmt: skip
    members = build_builder(tmp_path).build_members(revenue, SW)
    assert members["node_id"].tolist() == ["PROD_COAL_THERMAL", "PROD_COAL_COKE"]
    assert members["weight"].tolist() == pytest.approx([0.7, 0.3])


# TC-NMB-005
def test_tc_nmb_005_material_takes_sector_segment(tmp_path: Path) -> None:
    (tmp_path / "_common.yaml").write_text(
        "nodes:\n  - {id: MAT_LIVE_HOGS, type: material, name: 生猪, name_en: H}\n",
        encoding="utf-8",
    )
    members = build_builder(tmp_path).build_members(build_revenue(("生猪", 10.0)), SW)
    row = members.iloc[0]
    assert (row["node_id"], row["segment"]) == ("MAT_LIVE_HOGS", "SEG_COAL_MINING")
