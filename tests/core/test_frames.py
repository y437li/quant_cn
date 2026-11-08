from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core import frames
from quant_cn.core.exceptions import SchemaError
from quant_cn.core.frames import (
    FUNDAMENTALS_PIT,
    FUTURES_POSITIONING,
    GEX_PANEL,
    MARGIN_LADDER,
    MARGIN_VINTAGES,
    PRICE_PANEL,
    VIX_PANEL,
)
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


# TC-FR-004
@pytest.mark.parametrize("frame", [GEX_PANEL, FUTURES_POSITIONING, MARGIN_VINTAGES, MARGIN_LADDER])
def test_tc_fr_004_plan09_frames(frame: Schema) -> None:
    assert set(frame.primary_key) <= set(frame.columns)
    frame.validate(frame.build_empty())


# TC-FR-005
def test_tc_fr_005_plan04_frames() -> None:
    sample = {
        "trade_date": "20260924",
        "ts_code": "600000.SH",
        "factor": "ep_ttm",
        "reason": "",
        "metric": "ic_mean",
        "window": "2019-2026",
        "campaign": "c01",
        "trial_id": "t1",
        "params": "{}",
        "l1_code": "801010.SI",
    }
    schemas = [
        frames.UNIVERSE_PANEL,
        frames.FACTOR_PANEL,
        frames.IC_SERIES,
        frames.IC_TEST,
        frames.TRIAL_LOG,
        frames.FORWARD_RETURN,
        frames.QUANTILE_RETURNS,
        frames.EXPOSURE_PANEL,
    ]
    for schema in schemas:
        row = {c: sample.get(c, 1.0) for c in schema.columns}
        out = schema.validate(schema.normalize(pd.DataFrame([row]), strict=True))
        assert list(out.columns) == schema.columns and len(out) == 1
