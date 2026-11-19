from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.entity_alias_extractor import EntityAlias, EntityAliasExtractor

NAMES = [("华为技术有限公司", "300750 客户 光模块"), ("LGES", "603906 客户 磷酸铁锂"),
         ("国内某车企", "002594 客户")]  # fmt: skip


class FakeLlm(BaseLlmClient):
    def __init__(self, content: Any) -> None:
        self.content = content
        self.calls = 0

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        self.calls += 1
        return LlmReply(self.content, "fake", 10, 2)


# TC-EAX-001
def test_tc_eax_001_rows_checked() -> None:
    content = {"items": [
        {"name": "华为技术有限公司", "canonical": "华为", "kind": "company", "listed": None},
        {"name": "LGES", "canonical": "LG新能源", "kind": "company", "listed": "373220.ks",
         "is_member": True, "parent": " LG化学 "},
        {"name": "国内某车企", "canonical": "国内某车企", "kind": "generic"},
        {"name": "宁德时代", "canonical": "宁德时代", "kind": "company"},
        {"name": "LGES", "canonical": "", "kind": "company"},
        {"name": "华为技术有限公司", "canonical": "华为", "kind": "brand"},
        {"name": 3},
    ]}  # fmt: skip
    got = EntityAliasExtractor(FakeLlm(content), system="t").fetch_aliases(NAMES)
    assert got == [
        EntityAlias("华为技术有限公司", "华为", "company", False, None),
        EntityAlias("LGES", "LG新能源", "company", True, None, "LG化学"),
        EntityAlias("国内某车企", "国内某车企", "generic", False, None),
    ]


# TC-EAX-002
def test_tc_eax_002_bad_reply_and_empty() -> None:
    with pytest.raises(DataSourceError):
        EntityAliasExtractor(FakeLlm({"rows": []}), system="t").fetch_aliases(NAMES)
    llm = FakeLlm({"items": []})
    assert EntityAliasExtractor(llm, system="t").fetch_aliases([]) == [] and llm.calls == 0
