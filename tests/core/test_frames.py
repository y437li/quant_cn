from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.exceptions import SchemaError
from quant_cn.core.frames import FUNDAMENTALS_PIT, PRICE_PANEL, VIX_PANEL
from quant_cn.core.schema import Schema


# TC-FR-001
@pytest.mark.parametrize("frame", [PRICE_PANEL, FUNDAMENTALS_PIT])
def test_tc_fr_001_declared_and_empty_validates(frame: Schema) -> None:
    assert set(frame.primary_key) <= set(frame.columns)
    assert frame.text_columns <= set(frame.columns)
    frame.validate(frame.build_empty())


# TC-FR-002
def test_tc_fr_002_duplicate_key_fails() -> None:
    row = {c: ("x" if c in PRICE_PANEL.text_columns else 1.0) for c in PRICE_PANEL.columns}
    frame = PRICE_PANEL.normalize(pd.DataFrame([row, row]), strict=True)
    with pytest.raises(SchemaError):
        PRICE_PANEL.validate(frame)


# TC-FR-003
def test_tc_fr_003_vix_panel() -> None:
    assert set(VIX_PANEL.primary_key) == {"trade_date", "underlying"}
    assert VIX_PANEL.text_columns == {"trade_date", "underlying", "clock", "quality_flag"}
    VIX_PANEL.validate(VIX_PANEL.build_empty())
