# ruff: noqa: E501  (taxonomy YAML fixtures keep one node per line)
from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.industry_graph.product_matcher import ProductMatch, ProductMatcher
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy
from quant_cn.industry_graph.taxonomy_change_set import TaxonomyChangeSet

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
    assert matcher.find_matches("聚氯乙", ["220101"]) != []  # 3 of 4 chars, in context
    assert matcher.find_matches("煤炭开采服务业", ["220101"]) != []  # contains, any context
    assert matcher.find_matches("开采动力", ["220101"]) == []  # bigram overlap outside context
    assert matcher.find_matches("开采动力", ["740101"])[0].how != "overlap"  # too weak in context


# TC-PM-006
def test_tc_pm_006_outside_context_and_latin(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    assert matcher.find_matches("焦炭化工贸易服务", ["220101"]) == []  # 焦炭 short, out of context
    assert matcher.find_matches("焦炭化工贸易服务", ["740101"])[0].node_id == "PROD_COAL_COKE"
    assert matcher.find_matches("XPVC复合板", ["220101"]) == []  # PVC not a whole word
    assert matcher.find_matches("PVC管材", ["220101"])[0].node_id == "PROD_CHEM_PVC"


# TC-PT-004
def test_tc_pt_004_change_sets(tmp_path: Path) -> None:
    build(tmp_path)
    changes = TaxonomyChangeSet.model_validate({
        "version": "v1-test", "effective_period": "20251231",
        "changes": [
            {"op": "upsert", "kind": "new", "sector": "740000",
             "node": {"id": "PROD_COAL_COKING", "type": "product", "name": "炼焦煤",
                      "segment": "SEG_COAL_MINING", "aliases": ["主焦煤"]}},
            {"op": "upsert", "kind": "alias", "drop_aliases": ["电煤"],
             "node": {"id": "PROD_COAL_THERMAL", "type": "product", "name": "动力煤",
                      "aliases": ["发电用煤"]}},
            {"op": "retire", "kind": "merge", "id": "SEG_COAL_THERMAL",
             "successor": "SEG_COAL_MINING"},
        ],
    })  # fmt: skip
    taxonomy = ProductTaxonomy(tmp_path, [changes])
    assert taxonomy.version == "v1-test"
    coking = taxonomy.get_node("PROD_COAL_COKING")
    assert coking is not None and (coking.sector, coking.aliases) == ("740000", ("主焦煤",))
    thermal = taxonomy.get_node("PROD_COAL_THERMAL")
    assert thermal is not None and thermal.aliases == ("发电用煤",)
    assert thermal.segment == "SEG_COAL_MINING" and thermal.sector == "740000"
    retired = taxonomy.get_node("SEG_COAL_THERMAL")  # resolves to the successor
    assert retired is not None and retired.id == "SEG_COAL_MINING"
    assert taxonomy.get_surviving_id("SEG_COAL_THERMAL") == "SEG_COAL_MINING"
    assert ProductTaxonomy(tmp_path).version == "v0"


# TC-PM-007
def test_tc_pm_007_broad_parts_words(tmp_path: Path) -> None:
    (tmp_path / "x.yaml").write_text(
        "sector: {sw_l1: '270000', name: 电子}\nnodes:\n"
        "  - {id: PROD_SI_PARTS, type: product, name: 硅零部件, name_en: S}\n",
        encoding="utf-8",
    )
    matcher = ProductMatcher(ProductTaxonomy(tmp_path))
    assert matcher.find_matches("零部件业务", []) == []  # a broad word inside a longer label


# TC-PM-008
def test_tc_pm_008_line_inside_label_and_latin_digits(tmp_path: Path) -> None:
    matcher = ProductMatcher(build(tmp_path))
    assert matcher.find_matches("聚氯乙", []) == []  # a line inside a label, out of context
    assert matcher.find_matches("聚氯乙", ["220101"])[0].node_id == "PROD_CHEM_PVC"
    assert matcher.find_matches("PVC2000系列", ["220101"])[0].node_id == "PROD_CHEM_PVC"


SHORT = """
sector: {sw_l1: "230000", name: 钢铁}
nodes:
  - {id: SEG_STL_FLAT, type: segment, name: 板材产业, name_en: F, context_aliases: [板材]}
sw_l3_map:
  "230301": [SEG_STL_FLAT]
"""


# TC-PM-009
def test_tc_pm_009_context_aliases(tmp_path: Path) -> None:
    (tmp_path / "230000_steel.yaml").write_text(SHORT, encoding="utf-8")
    matcher = ProductMatcher(ProductTaxonomy(tmp_path))
    assert matcher.find_matches("板材", ["230301"])[0].how == "context_exact"
    assert matcher.find_matches("板材", []) == []  # outside the context
    assert matcher.find_matches("板材加工", ["230301"])[0].how == "sector"  # not exact
    assert matcher.find_matches("主营-板材", ["230301"])[0].how == "context_exact"
    assert matcher.find_sector_segment(["230301"]) == "SEG_STL_FLAT"
    assert matcher.find_sector_segment([]) is None


# TC-PT-005
def test_tc_pt_005_context_aliases(tmp_path: Path) -> None:
    (tmp_path / "230000_steel.yaml").write_text(SHORT, encoding="utf-8")
    change = TaxonomyChangeSet.model_validate({
        "version": "v9", "effective_period": "20251231",
        "changes": [{"op": "upsert", "node": {"id": "SEG_STL_FLAT", "type": "segment",
                     "name": "板材产业", "context_aliases": ["中板"]}}],
    })  # fmt: skip
    node = ProductTaxonomy(tmp_path, [change]).get_node("SEG_STL_FLAT")
    assert node is not None and node.context_aliases == ("板材", "中板")


BANK = """
sector: {sw_l1: "480000", name: 银行}
nodes:
  - {id: SEG_BANK, type: segment, name: 商业银行}
  - {id: PROD_BANK_PAY, type: product, name: 支付结算, segment: SEG_BANK, aliases: [代理业务]}
sw_l3_map:
  "480301": [SEG_BANK]
"""


# TC-PM-010
def test_tc_pm_010_short_label_exact_in_context_only(tmp_path: Path) -> None:
    (tmp_path / "480000_banks.yaml").write_text(BANK, encoding="utf-8")
    matcher = ProductMatcher(ProductTaxonomy(tmp_path))
    assert matcher.find_matches("代理业务", ["480301"])[0].node_id == "PROD_BANK_PAY"
    assert matcher.find_matches("代理产品", []) == []  # 代理产品 -> 代理, not a bank fee
    assert matcher.find_matches("代理业务", []) == []


EDGES = """
sector: {sw_l1: "630000", name: 电力设备}
nodes:
  - {id: SEG_CELL, type: segment, name: 电池}
  - {id: SEG_OLD, type: segment, name: 旧电池}
  - {id: SEG_CAR, type: segment, name: 整车}
  - {id: PROD_CELL, type: product, name: 电芯, segment: SEG_CELL}
  - {id: PROD_EV, type: product, name: 电动车, segment: SEG_CAR}
  - {id: MAT_LI, type: material, name: 锂}
edges:
  - [PROD_CELL, component_of, PROD_EV]
  - [PROD_EV, uses_material, MAT_LI]
  - [SEG_OLD, upstream_of, SEG_CAR]
  - [SEG_CELL, upstream_of, SEG_CAR]
  - [PROD_CELL, upstream_of, PROD_GONE]
  - [SEG_CELL, part_of, SEG_CAR]
"""


# TC-PT-006
def test_tc_pt_006_edges_and_segments(tmp_path: Path) -> None:
    (tmp_path / "630000_power.yaml").write_text(EDGES, encoding="utf-8")
    retire = TaxonomyChangeSet.model_validate({
        "version": "v1", "effective_period": "20251231",
        "changes": [{"op": "retire", "id": "SEG_OLD", "successor": "SEG_CELL"}],
    })  # fmt: skip
    taxonomy = ProductTaxonomy(tmp_path, [retire])
    assert taxonomy.list_edges(("component_of", "upstream_of", "uses_material")) == [
        ("PROD_CELL", "component_of", "PROD_EV"),
        ("PROD_EV", "uses_material", "MAT_LI"),
        ("SEG_CELL", "upstream_of", "SEG_CAR"),
    ]
    assert taxonomy.list_edges(("part_of",)) == [("SEG_CELL", "part_of", "SEG_CAR")]
    assert taxonomy.get_segment_id("PROD_EV") == "SEG_CAR"
    assert taxonomy.get_segment_id("SEG_OLD") == "SEG_CELL"
    assert taxonomy.get_segment_id("MAT_LI") is None
    assert taxonomy.get_segment_id("PROD_GONE") is None
