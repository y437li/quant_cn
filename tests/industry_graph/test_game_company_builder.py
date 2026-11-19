"""Contract tests for industry_graph.GameCompanyBuilder (plan 31 ph2)."""

from __future__ import annotations

import pandas as pd

from quant_cn.industry_graph.entity_resolver import EntityResolver
from quant_cn.industry_graph.game_company_builder import (
    GAME_COMPANY_COLUMNS,
    UNRESOLVED_COLUMNS,
    GameCompanyBuilder,
)

FULL = [("002558.SZ", "巨人网络集团股份有限公司"), ("002624.SZ", "完美世界股份有限公司"),
        ("603444.SH", "厦门吉比特网络技术股份有限公司")]  # fmt: skip
SHORT = [("002558.SZ", "巨人网络"), ("002624.SZ", "完美世界"), ("603444.SH", "吉比特")]
ALIASES = {
    "上海巨人网络科技有限公司": {"canonical": "巨人网络", "is_member": True,
                                 "parent": "巨人网络", "listed": "002558.SZ"},
    "完美世界游戏（某地）有限公司": {"canonical": "某游戏", "is_member": False,
                                     "parent": float("nan"), "listed": None},  # parquet NaN
}  # fmt: skip


def build_licenses(*rows: tuple[str, str, str]) -> pd.DataFrame:
    return pd.DataFrame([
        {"approval_no": f"N{i}", "name": game, "category": "移动", "publisher": pub,
         "operator": op, "approved_on": "20260929", "published": "20260930",
         "origin": "domestic"}
        for i, (game, pub, op) in enumerate(rows)
    ])  # fmt: skip


def build_builder() -> GameCompanyBuilder:
    return GameCompanyBuilder(EntityResolver(FULL, SHORT), ALIASES)


# TC-GCB-001
def test_tc_gcb_001_resolution() -> None:
    licenses = build_licenses(
        ("超自然行动组", "江苏凤凰电子音像出版社有限公司", "上海巨人网络科技有限公司"),
        ("问道", "厦门吉比特网络技术股份有限公司", "吉比特"),
    )
    links = build_builder().build_links(licenses)
    assert list(links.columns) == GAME_COMPANY_COLUMNS and len(links) == 4
    by = {(r.game, r.role): r for r in links.itertuples()}
    giant = by[("超自然行动组", "operator")]
    assert (giant.ts_code, giant.method, giant.is_member) == ("002558.SZ", "alias_short", True)
    assert by[("超自然行动组", "publisher")].method == "publishing_house"
    assert by[("问道", "publisher")].method == "full"
    assert by[("问道", "operator")].ts_code == "603444.SH"
    assert giant.known_on == "20260930"


# TC-GCB-002
def test_tc_gcb_002_rejected_and_unresolved() -> None:
    builder = build_builder()
    licenses = build_licenses(
        ("甲", "某出版社", "完美世界游戏（某地）有限公司"),  # prefix, proposal says otherwise
        ("乙", "某出版社", "无名工作室"),
        ("丙", "某出版社", "无名工作室"),
    )
    links = builder.build_links(licenses)
    perfect = links[links["holder"] == "完美世界游戏（某地）有限公司"].iloc[0]
    assert perfect["ts_code"] is None and perfect["method"] == "unresolved"
    lost = builder.list_unresolved(links)
    assert list(lost.columns) == UNRESOLVED_COLUMNS
    assert lost.iloc[0].tolist() == ["无名工作室", 2, "operator"]
    empty = builder.build_links(build_licenses())
    assert empty.empty and list(empty.columns) == GAME_COMPANY_COLUMNS
    assert builder.list_unresolved(empty).empty
