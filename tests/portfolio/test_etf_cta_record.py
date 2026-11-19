"""Contract tests for portfolio.EtfCtaRecord (plan 27)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.portfolio.etf_cta_record import EtfCtaRecord


def test_tc_ecr_001_record() -> None:
    """TC-ECR-001"""
    idx = pd.bdate_range("2025-01-01", periods=300)
    daily = pd.Series(np.where(np.arange(300) % 2 == 0, 0.004, -0.002), index=idx)
    nav = (1 + daily).cumprod()
    cash = pd.Series(0.0, index=idx)
    r = EtfCtaRecord(DateCodec()).build(nav, cash)
    assert r["start"] == "20250101" and r["nav"] == pytest.approx(round(nav.iloc[-1], 4))
    assert r["sharpe"] is not None and r["sharpe"] > 0 and r["max_dd"] == pytest.approx(-0.002)
    assert [y["year"] for y in r["years"]] == [2025, 2026] and r["points"][-1]["d"] == "20260224"
    short = EtfCtaRecord(DateCodec()).build(nav.iloc[:50], cash)
    assert short["ann"] is None and short["sharpe"] is None
