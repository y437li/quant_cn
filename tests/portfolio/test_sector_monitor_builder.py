"""Contract tests for portfolio.SectorMonitorBuilder (plan 31 ph4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.exceptions import LakeError
from quant_cn.core.sector_monitor_settings import MonitoredSecurity, SectorMonitorSettings
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.portfolio.app_rank_reader import AppRankReader
from quant_cn.portfolio.developer_sales_reader import DeveloperSalesReader
from quant_cn.portfolio.market_signal_reader import MarketSignalReader
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS, SectorMetricReader
from quant_cn.portfolio.sector_monitor_builder import FILE_NAME, SectorMonitorBuilder

DAYS = [f"202611{d:02d}" for d in range(1, 11)]


def build_settings() -> SectorMonitorSettings:
    return SectorMonitorSettings(**{
        "tiers": {"一线": ["北京"]}, "vol_windows": [3], "pct_window": 5, "pct_min_obs": 2,
        "history_sessions": 5, "history_quarters": 4, "history_months": 6,
        "sectors": [{"key": "games", "name": "游戏", "index": {"code": "IDX", "name": "指数"},
                     "companies": [{"code": "A.SZ", "name": "甲"}],
                     "metrics": ["revenue_q", "dividend", "realized_vol"]}],
    })  # fmt: skip


class FakeMetrics(SectorMetricReader):
    """Fixed lines: revenue for 甲, no dividends, two closes series."""

    def __init__(self) -> None:
        pass

    def read_quarterly(self, names: dict[str, str], metric: str) -> pd.DataFrame:
        return pd.DataFrame([["甲", "20260630", 10.0], ["甲", "20260930", np.nan]],
                            columns=LINE_COLUMNS)  # fmt: skip

    def read_dividends(self, names: dict[str, str]) -> pd.DataFrame:
        return pd.DataFrame(columns=LINE_COLUMNS)

    def read_closes(self, codes: list[str], index_code: str) -> pd.DataFrame:
        rng = np.random.default_rng(1)
        return pd.DataFrame({"A.SZ": 10 * np.exp(np.cumsum(rng.normal(0, 0.02, 10))),
                             "IDX": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 10)))},
                            index=DAYS)  # fmt: skip


class FakeChips(ChipStructureReader):
    """RetailGauge 0.3 for every code."""

    def __init__(self) -> None:
        pass

    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame({"retail_gauge": [0.3] * len(codes)}, index=codes)


class FakeApps(AppRankReader):
    """巨人-like company 甲 ranked 30 then 25; one leaderboard row."""

    def __init__(self) -> None:
        pass

    def read_rank_lines(self, names: dict[str, str]) -> pd.DataFrame:
        names = list(names.values())
        rows = [[names[0], DAYS[-2], 30.0], [names[0], DAYS[-1], 25.0]]
        if len(names) > 1:  # the second company dropped off the chart before the latest day
            rows.append([names[1], DAYS[-2], 100.0])
        return pd.DataFrame(rows, columns=LINE_COLUMNS)

    def read_rankings(self, names: dict[str, str]) -> dict[str, Any]:
        return {"as_of": DAYS[-1], "apps": [{"name": "游戏", "rank": 25}], "top": []}


class FakeSales(DeveloperSalesReader):
    """Rolling yoy for 甲 (current) and 乙 (stale since 2025-01); YTD yoy for 甲."""

    def __init__(self) -> None:
        pass

    def read_sales_yoy(self, names: dict[str, str]) -> pd.DataFrame:
        rows = [["甲", "2026-09", -5.0], ["甲", "2026-10", -3.0], ["乙", "2025-01", -50.0]]
        return pd.DataFrame(rows, columns=LINE_COLUMNS)

    def read_ytd_yoy(self, names: dict[str, str]) -> pd.DataFrame:
        return pd.DataFrame([["甲", "2026-10", -10.0]], columns=LINE_COLUMNS)


class FakeSignals(MarketSignalReader):
    """Valuation percentile and level, one revision, survey counts for 甲."""

    def __init__(self) -> None:
        pass

    def read_valuation(
        self, names: dict[str, str], index: tuple[str, str], field: str, as_of: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        pct = pd.DataFrame([[label, d, 50.0] for label in ("甲", index[1]) for d in DAYS],
                           columns=LINE_COLUMNS)  # fmt: skip
        levels = pd.DataFrame([["甲", as_of, 12.5], [index[1], as_of, 30.0]], columns=LINE_COLUMNS)
        return pct, levels

    def read_revisions(self, names: dict[str, str], as_of: str) -> pd.DataFrame:
        return pd.DataFrame([["甲", "2026-11", 2.0]], columns=LINE_COLUMNS)

    def read_surveys(self, names: dict[str, str], as_of: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        lines = pd.DataFrame([["甲", "2026-10", 1.0]], columns=LINE_COLUMNS)
        return lines, pd.DataFrame([["甲", as_of, 3.0]], columns=LINE_COLUMNS)


def build_builder(metrics: list[str] | None = None) -> SectorMonitorBuilder:
    settings = build_settings()
    if metrics:
        companies = [*settings.sectors[0].companies, MonitoredSecurity(code="B.SZ", name="乙")]
        sector = settings.sectors[0].model_copy(
            update={"metrics": metrics, "companies": companies, "valuation": "pe_ttm"}
        )
        settings = settings.model_copy(update={"sectors": [sector]})
    sales = FakeSales()
    vols = RealizedVolCalculator(settings.pct_window, settings.pct_min_obs)
    return SectorMonitorBuilder(
        settings, FakeMetrics(), sales, vols, FakeChips(), FakeApps(), FakeSignals()
    )


# TC-SMB-001
def test_tc_smb_001_charts_and_table() -> None:
    doc = build_builder().build()
    sector: dict[str, Any] = doc["sectors"][0]
    assert doc["as_of"] == DAYS[-1] and sector["as_of"] == DAYS[-1]
    assert [c["key"] for c in sector["charts"]] == ["revenue_q", "dividend", "realized_vol"]
    index_row, company = sector["table"]
    assert index_row["kind"] == "index" and "vol_3" in index_row
    assert company["revenue_q"] is None  # latest point is NaN
    assert company["retail_gauge"] == pytest.approx(0.3) and "vol_3_pct" in company


# TC-SMB-002
def test_tc_smb_002_vol_chart_and_empty() -> None:
    charts = {c["key"]: c for c in build_builder().build()["sectors"][0]["charts"]}
    assert {line["label"] for line in charts["realized_vol"]["lines"]} == {"甲", "指数"}
    # 8 vol values in the last 5 sessions → weekly sampling keeps the latest only (5-day step)
    assert all(len(line["points"]) == 1 for line in charts["realized_vol"]["lines"])
    assert charts["revenue_q"]["lines"][0]["points"] == [["20260630", 10.0]]  # NaN dropped
    assert charts["dividend"]["lines"] == []


# TC-SMB-003
def test_tc_smb_003_write(tmp_path: Path) -> None:
    builder = build_builder()
    path = builder.write(tmp_path)
    assert path == tmp_path / FILE_NAME
    assert json.loads(path.read_text(encoding="utf-8"))["sectors"][0]["key"] == "games"
    with pytest.raises(LakeError):
        builder.write(tmp_path / "missing")


# TC-SMB-004
def test_tc_smb_004_app_rank() -> None:
    assert "rankings" not in build_builder().build()["sectors"][0]
    sector = build_builder(["app_rank", "realized_vol"]).build()["sectors"][0]
    chart = sector["charts"][0]
    assert chart["key"] == "app_rank" and chart["invert"] is True
    assert sector["charts"][1]["invert"] is False
    assert sector["table"][1]["app_rank"] == pytest.approx(25.0)
    assert "app_rank" not in sector["table"][2]  # 乙 is off the chart at the latest capture
    assert sector["rankings"]["apps"][0]["rank"] == 25


# TC-SMB-005
def test_tc_smb_005_plan33_metrics() -> None:
    sector = build_builder(["sales_yoy", "valuation", "revision", "surveys"]).build()["sectors"][0]
    charts = {c["key"]: c for c in sector["charts"]}
    assert charts["valuation"]["title"] == "PE(TTM) 5 年分位"
    assert charts["valuation"]["extra"] == {
        "key": "valuation_level",
        "label": "PE(TTM)",
        "unit": "",
    }
    assert [charts[k]["in_table"] for k in ("sales_yoy", "valuation", "surveys")] == [
        False,
        True,
        False,
    ]
    index_row, jia, yi = sector["table"]
    assert index_row["valuation_level"] == pytest.approx(30.0)
    assert jia["sales_yoy_ytd"] == pytest.approx(-10.0) and jia["valuation_level"] == pytest.approx(
        12.5
    )
    assert jia["revision"] == pytest.approx(2.0) and jia["surveys_recent"] == pytest.approx(3.0)
    assert jia["sales_yoy"] == pytest.approx(-3.0) and "sales_yoy" not in yi  # 乙 is stale
