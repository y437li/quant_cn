from __future__ import annotations

import pytest

from quant_cn.industry_graph.lenient_item import LenientItem


class NumberItem(LenientItem):
    value: float | None = None
    amount: float = 0.0
    label: str = ""


# TC-LI-001
def test_tc_li_001_numeric_text() -> None:
    assert NumberItem(value="30%").value == pytest.approx(30.0)
    assert NumberItem(value="1,234.5万元").value == pytest.approx(1234.5)
    assert NumberItem(value=12, amount="约50").amount == pytest.approx(50.0)
    assert NumberItem(value=None).value is None
    assert NumberItem(value="不适用").value is None
    assert NumberItem(label="2026年").label == "2026年"
