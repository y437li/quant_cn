"""Contract tests for lake.FundamentalSignalReader (plan 15 ph7f)."""

from __future__ import annotations

import math
from typing import cast

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.fundamental_signal_reader import COLUMNS, FundamentalSignalReader
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.statement_version_reader import StatementVersionReader
from tests.support import MiniLake, SampleFactorLake

A, B, C = "000001.SZ", "600000.SH", "000002.SZ"
YTD = {  # (code, end_date) -> revenue, oper_cost, profit_dedt  (year-to-date)
    (A, "20250630"): (100.0, 80.0, 10.0),
    (A, "20250930"): (150.0, 120.0, 12.0),  # Q3 2025: rev 50, dedt 2
    (A, "20260630"): (120.0, 90.0, 11.0),
    (A, "20260930"): (200.0, 150.0, 16.0),  # Q3 2026: rev 80, cost 60 -> GM 0.25; dedt 5
    (B, "20250331"): (40.0, 30.0, -4.0),
    (B, "20260331"): (50.0, 35.0, 2.0),  # Q1 is its own quarter; base -4 -> (2+4)/4
}
TTM = {(A, "20260930"): (90.0, 60.0)}  # n_cashflow_act_ttm, n_income_attr_p_ttm


class FakeVersions:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str, str]] = []

    def read_versions(self, fields: list[str], as_of: str, start: str) -> pd.DataFrame:
        self.calls.append((list(fields), as_of, start))
        rows = []
        for (code, end), values in YTD.items():
            rows += [
                (code, end, f, v)
                for f, v in zip(("revenue", "oper_cost", "profit_dedt"), values, strict=True)
            ]
        for (code, end), values in TTM.items():
            rows += [
                (code, end, f, v)
                for f, v in zip(("n_cashflow_act_ttm", "n_income_attr_p_ttm"), values, strict=True)
            ]
        return pd.DataFrame(rows, columns=["ts_code", "end_date", "field", "value"])


def _build(query: LakeQuery) -> tuple[FundamentalSignalReader, FakeVersions]:
    fake = FakeVersions()
    return FundamentalSignalReader(cast(StatementVersionReader, fake), query), fake


def test_tc_fsr_001_single_quarter(lake: MiniLake) -> None:
    """TC-FSR-001"""
    reader, fake = _build(lake.query)
    out = reader.read([A, B, C], "20261112")
    assert list(out.columns) == COLUMNS and list(out.index) == [A, B, C]
    assert out.loc[A, "period"] == "20260930" and round(out.loc[A, "gm_q"], 9) == 0.25
    assert round(out.loc[A, "dedt_yoy_q"], 9) == 1.5  # (5 - 2) / 2
    assert fake.calls[0][1:] == ("20261112", "20241013")


def test_tc_fsr_002_q1_loss_base_missing(lake: MiniLake) -> None:
    """TC-FSR-002"""
    out = _build(lake.query)[0].read([B, C], "20261112")
    assert out.loc[B, "period"] == "20260331" and round(out.loc[B, "gm_q"], 9) == 0.3
    assert round(out.loc[B, "dedt_yoy_q"], 9) == 1.5  # (2 - (-4)) / |-4|
    assert math.isnan(out.loc[B, "ocf_to_np"]) and pd.isna(out.loc[C, "gm_q"])


def test_tc_fsr_003_ocf_and_series(lake: MiniLake, config: Config) -> None:
    """TC-FSR-003"""
    reader = _build(lake.query)[0]
    assert round(reader.read([A], "20261112").loc[A, "ocf_to_np"], 9) == 1.5
    assert reader.read_series(["tio2"], "20261112") == {}  # no manual_series view yet
    rows = [
        {"series": "tio2", "date": "20261001", "value": 14000.0, "published": "20261002"},
        {"series": "tio2", "date": "20261101", "value": 13500.0, "published": "20261102"},
        {"series": "tio2", "date": "20261110", "value": 13000.0, "published": "20261120"},
    ]
    SampleFactorLake.write(lake, config, "manual_series", rows)
    assert reader.read_series(["tio2", "bdi"], "20261112") == {"series:tio2": 13500.0}
