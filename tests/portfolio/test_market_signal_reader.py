"""Contract tests for portfolio.MarketSignalReader (plan 33)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.portfolio.market_signal_reader import MarketSignalReader
from tests.support import MiniLake, SampleFactorLake

REPO = Path(__file__).resolve().parents[2]
NAMES = {"002558.SZ": "巨人网络"}
INDEX = ("801764.SI", "游戏")
DAYS = [f"202611{d:02d}" for d in range(2, 7)]


def build_reader(lake: MiniLake) -> MarketSignalReader:
    settings = SectorMonitorSettings.load(REPO).model_copy(update={"history_months": 3})
    return MarketSignalReader(settings, lake.query, RealizedVolCalculator(5, 2), DateCodec())


def get_values(frame: pd.DataFrame, label: str) -> list[float]:
    rows = frame[frame["label"] == label]
    return [float(v) for v in rows["value"]]


# TC-MKS-001
def test_tc_mks_001_valuation(lake: MiniLake, config: Config) -> None:
    pct, levels = build_reader(lake).read_valuation(NAMES, INDEX, "pe_ttm", DAYS[-1])
    assert pct.empty and levels.empty
    pes = [20.0, 30.0, -5.0, 10.0, 25.0]  # the loss day is dropped
    SampleFactorLake.write(lake, config, "daily_basic", [
        {"ts_code": "002558.SZ", "trade_date": d, "pe_ttm": v}
        for d, v in zip(DAYS, pes, strict=True)
    ])  # fmt: skip
    SampleFactorLake.write(lake, config, "sw_daily", [
        {"ts_code": "801764.SI", "trade_date": d, "pe": 40.0 + i} for i, d in enumerate(DAYS)
    ])  # fmt: skip
    pct, levels = build_reader(lake).read_valuation(NAMES, INDEX, "pe_ttm", DAYS[-1])
    # 巨人: 20, 30, 10, 25 -> from the 2nd value: 30 is the max (100%), 10 the min (33%), 25 (75%)
    assert get_values(pct, "巨人网络") == pytest.approx([100.0, 100 / 3, 75.0])
    assert get_values(pct, "游戏")[-1] == pytest.approx(100.0)
    assert sorted(levels.values.tolist()) == [
        ["巨人网络", DAYS[-1], 25.0],
        ["游戏", DAYS[-1], 44.0],
    ]


# TC-MKS-002
def test_tc_mks_002_revisions(lake: MiniLake, config: Config) -> None:
    assert build_reader(lake).read_revisions(NAMES, "20261116").empty
    reports = [("20260801", "A", "2026Q4", 100.0), ("20260901", "B", "2026Q4", 120.0),
               ("20260905", "E", "2026Q4", 60.0), ("20261101", "C", "2026Q4", 150.0),
               ("20261110", "D", "2026Q4", 130.0), ("20261112", "E", "2026Q4", 140.0),
               ("20261110", "B", "2027Q2", 999.0),  # not a fiscal-year forecast
               ("20270201", "A", "2026Q4", 100.0), ("20270510", "A", "2027Q4", 200.0)]  # fmt: skip
    SampleFactorLake.write(lake, config, "report_rc", [
        {"ts_code": "002558.SZ", "report_date": d, "org_name": org, "report_title": f"t{d}",
         "quarter": q, "np": v} for d, org, q, v in reports
    ])  # fmt: skip
    out = build_reader(lake).read_revisions(NAMES, "20261116")
    # 09-30: no window before. 10-31: median(B 120, E 60) = 90 vs A 100 -> -10%.
    # 11-16 (as_of): broker E counts once, at its latest 140: median(120, 150, 130, 140) = 135
    # vs 100 -> +35% (counting E's stale 60 as well would give a median of 130)
    assert out["period"].tolist() == ["2026-10", "2026-11"]
    assert out["value"].tolist() == pytest.approx([-10.0, 35.0])
    # 2027-05-20 forecasts FY2027, the window before still FY2026: no revision
    assert "2027-05" not in build_reader(lake).read_revisions(NAMES, "20270520")["period"].tolist()
    # a loss in either window gives no value: 甲 forecast a loss before, profit now
    SampleFactorLake.write(lake, config, "report_rc", [
        {"ts_code": "002558.SZ", "report_date": d, "org_name": "A", "report_title": f"t{d}",
         "quarter": "2026Q4", "np": v} for d, v in (("20260801", -50.0), ("20261110", 80.0))
    ])  # fmt: skip
    assert build_reader(lake).read_revisions(NAMES, "20261116").empty


# TC-MKS-003
def test_tc_mks_003_surveys(lake: MiniLake, config: Config) -> None:
    lines, recent = build_reader(lake).read_surveys(NAMES, "20261116")
    assert lines.empty and recent.empty
    SampleFactorLake.write(lake, config, "stk_surv", [
        {"ts_code": "002558.SZ", "surv_date": d, "rece_org": org, "fund_visitors": "x"}
        for d, org in (("20261105", "A"), ("20261105", "B"), ("20261110", "A"), ("20260915", "C"),
                       ("20260601", "D"))
    ])  # fmt: skip
    lines, recent = build_reader(lake).read_surveys(NAMES, "20261116")
    assert lines.values.tolist() == [["巨人网络", "2026-06", 1.0], ["巨人网络", "2026-09", 1.0],
                                     ["巨人网络", "2026-11", 2.0]]  # fmt: skip
    assert recent.values.tolist() == [["巨人网络", "20261116", 3.0]]  # 06-01 is outside 90 days
