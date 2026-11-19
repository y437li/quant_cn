from __future__ import annotations

from quant_cn.industry_graph.counterparty_name import CounterpartyName


# TC-CPN-001
def test_tc_cpn_001_is_named() -> None:
    unnamed = ["客户一", "供应商A", "客商9", "第一名", "供应商B及其关联方", "H公司",
               "西安某科技有限公司", "头部车企", "国内无人机厂商", " "]  # fmt: skip
    named = ["宁德时代", "GE", "LG Energy Solution", "宁德时代新能源科技股份有限公司"]
    assert not any(CounterpartyName.is_named(n) for n in unnamed)
    assert all(CounterpartyName.is_named(n) for n in named)


# TC-CPN-002
def test_tc_cpn_002_is_in_text() -> None:
    full = "宁德时代新能源科技股份有限公司"
    assert CounterpartyName.is_in_text(full, None, "公司向宁德时代新能源科技股份 有限公司供货")
    assert CounterpartyName.is_in_text(full, "客户一", "客户一的销售额为3.5亿元")
    assert CounterpartyName.is_in_text(full, None, "宁德时代是公司重要客户")
    assert CounterpartyName.is_in_text("Tesla, Inc.", None, "向TESLA批量供货")
    assert not CounterpartyName.is_in_text("比亚迪", None, "公司和主要客户保持合作")
    assert not CounterpartyName.is_in_text("", None, "公司和主要客户保持合作")


# TC-CPN-003
def test_tc_cpn_003_numbered_and_placeholders() -> None:
    unnamed = ["应付账款-供应商7", "内销客户8", "客户（一）", "2019年第1大客户", "第四名供应商",
               "法人一", "客户1 子公司3", "无", "客户", "100905", "香港公司", "排名第一的供应商",
               "天津**有限公司**分公司", "P"]  # fmt: skip
    named = ["华为公司", "第一创业", "客户关系管理软件公司", "360", "1688", "7-11"]
    assert [n for n in unnamed if CounterpartyName.is_named(n)] == []
    assert all(CounterpartyName.is_named(n) for n in named)
