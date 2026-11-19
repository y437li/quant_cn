"""Contract tests for core.Condition (plan 15 ph7f)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_cn.core.condition import METRICS, Condition


def _build(kind: str, metric: str, **extra: object) -> Condition:
    return Condition(label="x", kind=kind, metric=metric, op=">=", value=1.0, **extra)  # type: ignore[arg-type]


def test_tc_cnd_001_metrics_by_kind() -> None:
    """TC-CND-001"""
    for kind, metrics in METRICS.items():
        for metric in metrics:
            assert _build(kind, metric).metric_key == metric
    with pytest.raises(ValidationError):
        _build("flow", "close")
    with pytest.raises(ValidationError):
        _build("colour", "close")


def test_tc_cnd_002_series_and_extra_keys() -> None:
    """TC-CND-002"""
    assert _build("series", "tio2_spot").metric_key == "series:tio2_spot"
    with pytest.raises(ValidationError):
        _build("price", "close", note="no")


def test_tc_cnd_003_required() -> None:
    """TC-CND-003"""
    assert _build("chip", "holder_sell_90d_pct").required is False
    assert _build("statement", "gm_q", required=True).required is True
