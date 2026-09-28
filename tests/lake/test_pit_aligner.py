from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import FUNDAMENTALS_PIT
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.pit_aligner import PitAligner
from tests.support import MiniLake, SampleLake

# (end_date, f_ann_date, report_type, total_profit)
ROWS = [
    ("20251231", "20260320", "1", 1.0),  # FY2025 announced Fri 0320 -> visible Mon 0323
    ("20251231", "20260320", "2", 99.0),  # parent-only statement: never visible
    ("20251231", "20260410", "1", 2.0),  # FY2025 restated 0410 -> visible 0413
    ("20250930", "20260415", "1", 9.0),  # older period restated later: never visible
    ("20260331", "20260424", "1", 3.0),  # Q1 2026 announced 0424 -> visible 0427
]


@pytest.fixture
def aligner(lake: MiniLake, config: Config) -> PitAligner:
    SampleLake.write_calendar(lake, config.get_dataset("trade_cal"))
    SampleLake.write_income(lake, config.get_dataset("income_vip"), ROWS)
    compactor = Compactor(lake.catalog, lake.query, lake.writer, lake.clock)
    for name in ("trade_cal", "income_vip"):
        compactor.rebuild(config.get_dataset(name))
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    pit = PitAligner(lake.catalog, lake.query, DateCodec())
    pit.refresh()
    return pit


def build_profit_by_day(aligner: PitAligner) -> dict[str, float]:
    df = aligner.read_aligned("20260101", "20260430", fields=["total_profit"])
    return dict(zip(df["trade_date"], df["value"], strict=True))


# TC-PA-001
def test_tc_pa_001_not_visible_before_next_session(aligner: PitAligner) -> None:
    seen = build_profit_by_day(aligner)
    assert "20260320" not in seen and min(seen) == "20260323"
    assert seen["20260323"] == pytest.approx(1.0)


# TC-PA-002
def test_tc_pa_002_restatement(aligner: PitAligner) -> None:
    seen = build_profit_by_day(aligner)
    assert seen["20260410"] == pytest.approx(1.0)
    assert seen["20260413"] == pytest.approx(2.0)
    assert seen["20260427"] == pytest.approx(3.0)


# TC-PA-003
def test_tc_pa_003_old_period_restatement_ignored(aligner: PitAligner) -> None:
    seen = build_profit_by_day(aligner)
    assert seen["20260416"] == pytest.approx(2.0)
    assert 9.0 not in seen.values() and 99.0 not in seen.values()


# TC-PA-004
def test_tc_pa_004_schema_and_filters(aligner: PitAligner) -> None:
    df = aligner.read_aligned(
        "20260423", "20260428", tickers=["000001.SZ"], fields=["total_profit"]
    )
    FUNDAMENTALS_PIT.validate(df)
    assert df["end_date"].tolist() == ["20251231", "20260331", "20260331"]
    assert aligner.read_aligned("20260423", "20260428", tickers=["600000.SH"]).empty


# TC-PA-005
def test_tc_pa_005_errors(lake: MiniLake, aligner: PitAligner) -> None:
    with pytest.raises(ValueError):
        aligner.read_aligned("20260430", "20260101")
    lake.catalog.connection.execute("DROP VIEW derived.fundamentals_states")
    with pytest.raises(LakeError):
        aligner.read_aligned("20260101", "20260430")
    lake.catalog.connection.execute("DROP VIEW derived.fundamentals_long")
    with pytest.raises(LakeError):
        aligner.refresh()
