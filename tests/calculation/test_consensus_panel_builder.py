"""Contract tests for calculation.ConsensusPanelBuilder (plan 36, D-173)."""

from __future__ import annotations

import pytest

from quant_cn.calculation.consensus_panel_builder import CONSENSUS_COLUMNS, ConsensusPanelBuilder
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from tests.support import MiniLake, SampleFactorLake

CODE = "000001.SZ"


def write_notes(lake: MiniLake, config: Config, notes: list[tuple[str, str, str, float]]) -> None:
    rows = [
        {"ts_code": CODE, "report_date": d, "org_name": org, "report_title": f"{org}{d}",
         "quarter": q, "np": v}
        for d, org, q, v in notes
    ]  # fmt: skip
    SampleFactorLake.write(lake, config, "report_rc", rows)


# TC-CNS-001
def test_tc_cns_001_window_and_pit(lake: MiniLake, config: Config) -> None:
    write_notes(lake, config, [
        ("20260801", "A", "2026Q4", 100.0), ("20260901", "A", "2026Q4", 120.0),  # A's latest: 120
        ("20260910", "B", "2026Q4", 140.0), ("20260910", "B", "2027Q4", 200.0),
        ("20260920", "C", "2026Q4", 999.0),  # on the date: visible only the next session
        ("20260601", "D", "2026Q4", 1.0),  # outside the 90-day window
        ("20260915", "E", "2026Q2", 5.0),  # not a fiscal-year forecast
    ])  # fmt: skip
    out = ConsensusPanelBuilder(lake.query, DateCodec()).build(["20260920"], 90)
    assert list(out.columns) == list(CONSENSUS_COLUMNS)
    row = out.iloc[0]
    assert (row["fy1"], row["n_brokers"]) == (2026, 2)
    assert (row["np1"], row["np2"]) == pytest.approx((130.0, 200.0))
    assert row[["np3"]].isna().all()
    later = ConsensusPanelBuilder(lake.query, DateCodec()).build(["20260921"], 90)
    assert later.iloc[0]["np1"] == pytest.approx(140.0)  # median of 120, 140, 999


# TC-CNS-002
def test_tc_cns_002_fy_roll(lake: MiniLake, config: Config) -> None:
    write_notes(lake, config, [
        ("20260401", "A", "2025Q4", 50.0), ("20260401", "A", "2026Q4", 60.0),
        ("20260401", "A", "2027Q4", 70.0), ("20260401", "A", "2028Q4", 80.0),
    ])  # fmt: skip
    out = ConsensusPanelBuilder(lake.query, DateCodec()).build(["20260430", "20260505"], 90)
    april, may = out.iloc[0], out.iloc[1]
    assert (april["fy1"], april["np1"], april["np3"]) == (2025, 50.0, 70.0)
    assert (may["fy1"], may["np1"], may["np3"]) == (2026, 60.0, 80.0)
    assert ConsensusPanelBuilder.get_fy1("20260430") == 2025


# TC-CNS-003
def test_tc_cns_003_empty(lake: MiniLake) -> None:
    builder = ConsensusPanelBuilder(lake.query, DateCodec())
    assert builder.build(["20260920"], 90).empty
    assert list(builder.build([], 90).columns) == list(CONSENSUS_COLUMNS)
