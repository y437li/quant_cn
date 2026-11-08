# ruff: noqa: E501  (taxonomy YAML fixtures keep one node per line)
from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.industry_graph.product_matcher import ProductMatch, ProductMatcher
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy

COAL = """
sector: {sw_l1: "740000", name: 煤炭}
nodes:
  - {id: SEG_COAL_MINING, type: segment, name: 煤炭开采, name_en: Coal Mining}
  - {id: SEG_COAL_THERMAL, type: segment, name: 动力煤开采, name_en: T,
     parent: SEG_COAL_MINING}
  - {id: PROD_COAL_THERMAL, type: product, name: 动力煤, name_en: Thermal Coal, segment: SEG_COAL_THERMAL, aliases: [电煤]}
  - {id: PROD_COAL_COKE, type: product, name: 焦炭, name_en: Coke, segment: SEG_COAL_MINING}
sw_l3_map:
  "740101": [SEG_COAL_MINING]
"""
CHEM = """
sector: {sw_l1: "220000", name: 基础化工}
nodes:
  - {id: SEG_CHEM_RAW, type: segment, name: 化学原料, name_en: Raw}
  - {id: SEG_CHEM_FILM, type: segment, name: 膜材料, name_en: Film}
  - {id: PROD_CHEM_BDO, type: product, name: 1,4-丁二醇, name_en: BDO, segment: SEG_CHEM_RAW, aliases: [BDO]}
  - {id: PROD_CHEM_PVC, type: product, name: 聚氯乙烯, name_en: PVC, segment: SEG_CHEM_RAW, aliases: [PVC]}
  - {id: PROD_ELEC_POLARIZER, type: product, name: 偏光片, name_en: Polarizer, segment: SEG_CHEM_FILM}
  - {id: PROD_OLD_COKE, type: product, name: 冶金焦炭, name_en: Met Coke, segment: SEG_CHEM_RAW}
  - {id: PROD_NUC_SERVICE, type: product, name: 核电技术服务, name_en: Nuclear Services, segment: SEG_CHEM_RAW}
sw_l3_map:
  "220101": [SEG_CHEM_RAW, SEG_CHEM_FILM]
"""


def build(tmp_path: Path) -> ProductTaxonomy:
    (tmp_path / "740000_coal.yaml").write_text(COAL)
    (tmp_path / "220000_chem.yaml").write_text(CHEM)
    (tmp_path / "_merged_ids.yaml").write_text("PROD_COAL_OLD: PROD_COAL_THERMAL\n")
    return ProductTaxonomy(tmp_path)


# TC-PT-001
def test_tc_pt_001_load(tmp_path: Path) -> None:
    taxonomy = build(tmp_path)
    node = taxonomy.get_node("PROD_CHEM_BDO")
    assert node is not None and isinstance(node.name, str) and node.sector == "220000"
    assert taxonomy.get_node("PROD_COAL_OLD").id == "PROD_COAL_THERMAL"  # type: ignore[union-attr]
    assert taxonomy.get_surviving_id("X") == "X"


# TC-PT-002
def test_tc_pt_002_context(tmp_path: Path) -> None:
    taxonomy = build(tmp_path)
    ids = taxonomy.list_context_ids(["740100", "740101"])
    assert {"SEG_COAL_MINING", "SEG_COAL_THERMAL", "PROD_COAL_THERMAL", "PROD_COAL_COKE"} == ids
    assert taxonomy.list_context_ids(["999999"]) == set()


# TC-PT-003
def test_tc_pt_003_errors(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        ProductTaxonomy(tmp_path / "missing")
    (tmp_path / "a.yaml").write_text("nodes:\n  - {id: P, type: product, name: x}\n")
    (tmp_path / "b.yaml").write_text("nodes:\n  - {id: P, type: product, name: y}\n")
    with pytest.raises(ConfigError):
        ProductTaxonomy(tmp_path)


# TC-PM-001
def test_tc_pm_001_exact_and_alias(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    assert matcher.find_matches("动力煤", []) == [ProductMatch("PROD_COAL_THERMAL", 1.0, "exact")]
    assert matcher.find_matches("电煤销售收入", [])[0].node_id == "PROD_COAL_THERMAL"
    assert matcher.find_matches("PVC（含糊树脂）", [])[0].node_id == "PROD_CHEM_PVC"


# TC-PM-002
def test_tc_pm_002_context_and_generic(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    assert matcher.find_matches("焦炭", ["740101"])[0].node_id == "PROD_COAL_COKE"
    assert matcher.find_matches("冶金焦", ["220101"])[0].node_id == "PROD_OLD_COKE"
    assert matcher.find_matches("其他", ["740101"]) == [] and matcher.is_generic("投资收益")


# TC-PM-003
def test_tc_pm_003_split_and_hierarchy(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    ids = {m.node_id for m in matcher.find_matches("聚氯乙烯、偏光片及其他", [])}
    assert ids == {"PROD_CHEM_PVC", "PROD_ELEC_POLARIZER"}
    assert matcher.find_matches("化工板块：BDO", [])[0].node_id == "PROD_CHEM_BDO"
    assert matcher.find_matches("动力煤：其他", [])[0].node_id == "PROD_COAL_THERMAL"


# TC-PM-004
def test_tc_pm_004_sector_fallback(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    assert matcher.find_matches("煤矿运营", ["740101"]) == [
        ProductMatch("SEG_COAL_MINING", 0.3, "sector")
    ]
    assert matcher.find_matches("煤矿运营", ["220101"]) == []  # two root segments: no fallback


# TC-PM-005
def test_tc_pm_005_weak_matches_rejected(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    assert matcher.find_matches("偏光", []) == []  # 2 chars inside 偏光片: too short
    assert matcher.find_matches("技术服务", []) == []  # broad word inside 核电技术服务
    assert matcher.find_matches("聚氯乙", []) != []  # 3 of 4 chars
    assert matcher.find_matches("煤炭开采服务业", ["220101"]) != []  # contains, any context
    assert matcher.find_matches("开采动力", ["220101"]) == []  # bigram overlap outside context
    assert matcher.find_matches("开采动力", ["740101"])[0].how != "overlap"  # too weak in context
