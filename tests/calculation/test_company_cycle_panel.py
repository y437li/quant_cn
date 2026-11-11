"""Contract tests for calculation.CompanyCyclePanel (plan 16 phase 1, D-121)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from quant_cn.calculation.company_cycle_panel import COLUMNS, FLOWS, STOCKS, CompanyCyclePanel
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.discovery_settings import DiscoverySettings
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from tests.support import MiniLake, SampleFactorLake

A, B, C = "000001.SZ", "000002.SZ", "000003.SZ"
AS_OF = "20261106"
# (code, end_date, ann_date, revenue, oper_cost, n_income_attr_p) — YTD values
INCOME = [
    *[(A, f"{y}1231", f"{y + 1}0320", 100.0, 60.0, 10.0) for y in range(2016, 2025)],
    (A, "20250331", "20250420", 25.0, 15.0, 2.0),
    (A, "20250630", "20250820", 50.0, 30.0, 5.0),
    (A, "20250930", "20251020", 75.0, 45.0, 8.0),
    (A, "20251231", "20260320", 100.0, 60.0, 20.0),
    (A, "20260331", "20260420", 30.0, 18.0, 4.0),
    (A, "20260630", "20260820", 60.0, 33.0, 9.0),
    (A, "20260930", "20261020", 100.0, 50.0, 20.0),
    (B, "20260331", "20260420", 10.0, 6.0, 1.0),
    (B, "20260630", "20260825", 20.0, 12.0, 3.0),
    (B, "20260630", "20260901", 20.0, 12.0, 4.0),  # restatement
    *[(C, f"{y}1231", f"{y + 1}0320", 50.0, 40.0, 5.0) for y in range(2022, 2025)],
    (C, "20250630", "20250820", 20.0, 16.0, 2.0),
    (C, "20250930", "20251020", 30.0, 25.0, 1.0),  # Q3-25 single quarter loss (-1)
    (C, "20251231", "20260320", 40.0, 30.0, 3.0),
    (C, "20260630", "20260820", 20.0, 15.0, 1.0),
    (C, "20260930", "20261020", 32.0, 24.0, 2.0),
]
DEDUCTED = [("20250930", "20251020", 7.0), ("20251231", "20260320", 17.0)]
DEDUCTED += [("20260630", "20260820", 8.0), ("20260930", "20261020", 18.0)]


def _write_lake(lake: MiniLake, config: Config) -> None:
    w, stmt = SampleFactorLake.write, {"report_type": "1", "update_flag": "1"}
    keys = ("ts_code", "end_date", "ann_date", "revenue", "oper_cost", "n_income_attr_p")
    rows = [stmt | dict(zip(keys, r, strict=True)) | {"f_ann_date": r[2]} for r in INCOME]
    w(lake, config, "income_vip", rows)
    w(
        lake,
        config,
        "fina_indicator_vip",
        [
            {"ts_code": A, "end_date": e, "ann_date": a, "profit_dedt": v, "update_flag": "1"}
            for e, a, v in DEDUCTED
        ],
    )
    sheet = {"ts_code": A, "end_date": "20260930", "ann_date": "20261020"}
    sheet |= {"f_ann_date": "20261020", "total_hldr_eqy_exc_min_int": 160.0, "total_assets": 250.0}
    w(lake, config, "balancesheet_vip", [stmt | sheet])
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()


class PanelHarness:
    """The panel fed by the version reader, as the discovery step will wire them."""

    def __init__(self, lake: MiniLake) -> None:
        self.panel = CompanyCyclePanel(DateCodec(), DiscoverySettings())
        self.reader = StatementVersionReader(
            lake.query, TickerAliasMap(lake.catalog, lake.query), DateCodec()
        )

    def build(self, as_of: str) -> pd.DataFrame:
        start = self.panel.compute_start(as_of)
        return self.panel.build(
            self.reader.read_versions(self.panel.list_fields(), as_of, start), as_of
        )


@pytest.fixture
def panel(lake: MiniLake, config: Config) -> PanelHarness:
    _write_lake(lake, config)
    return PanelHarness(lake)


def _build_row(panel: PanelHarness, code: str, as_of: str = AS_OF) -> dict[str, Any]:
    frame = panel.build(as_of)
    return dict(frame[frame["ts_code"] == code].iloc[0])


def test_tc_ccp_001_single_quarter(panel: PanelHarness) -> None:
    """TC-CCP-001"""
    row = _build_row(panel, A)
    assert row["period"] == "20260930"
    assert (row["rev_q"], row["np_q"]) == (pytest.approx(40.0), pytest.approx(11.0))
    assert row["gm_q"] == pytest.approx(1 - 17 / 40)
    assert _build_row(panel, B, "20260430")["np_q"] == pytest.approx(1.0)  # Q1 = YTD


def test_tc_ccp_002_yoy_qoq(panel: PanelHarness) -> None:
    """TC-CCP-002"""
    row = _build_row(panel, A)
    assert row["rev_yoy"] == pytest.approx(40 / 25 - 1)
    assert row["np_yoy"] == pytest.approx(11 / 3 - 1)
    assert row["np_qoq"] == pytest.approx(11 / 5 - 1)
    assert row["dgm_yoy"] == pytest.approx((1 - 17 / 40) - (1 - 15 / 25))
    assert row["dgm_qoq"] == pytest.approx((1 - 17 / 40) - (1 - 15 / 30))
    assert pd.isna(_build_row(panel, C)["np_yoy"])  # Q3-25 base is a loss


def test_tc_ccp_003_ttm(panel: PanelHarness) -> None:
    """TC-CCP-003"""
    row = _build_row(panel, A)
    assert (row["rev_ttm"], row["np_ttm"]) == (pytest.approx(125.0), pytest.approx(32.0))
    assert row["nm_ttm"] == pytest.approx(32 / 125)
    assert row["roe_ttm"] == pytest.approx(32 / 160)
    assert row["turnover_ttm"] == pytest.approx(125 / 250)


def test_tc_ccp_004_point_in_time(panel: PanelHarness) -> None:
    """TC-CCP-004"""
    assert _build_row(panel, A, "20261015")["period"] == "20260630"
    assert _build_row(panel, B, "20260830")["np_q"] == pytest.approx(2.0)
    assert _build_row(panel, B, "20260905")["np_q"] == pytest.approx(3.0)


def test_tc_ccp_005_cycle_norm(panel: PanelHarness) -> None:
    """TC-CCP-005"""
    row = _build_row(panel, A)
    assert (row["np_med"], row["nm_max"], row["n_years"]) == (
        pytest.approx(10.0),
        pytest.approx(0.2),
        pytest.approx(10.0),
    )
    assert row["ttm_vs_med"] == pytest.approx(3.2)
    assert bool(row["margin_peak"])


def test_tc_ccp_006_deducted_profit(panel: PanelHarness) -> None:
    """TC-CCP-006"""
    row = _build_row(panel, A)
    assert row["np_dedt_q"] == pytest.approx(10.0)
    assert row["np_dedt_ttm"] == pytest.approx(18 + 17 - 7)


def test_tc_ccp_007_short_history(panel: PanelHarness) -> None:
    """TC-CCP-007"""
    row = _build_row(panel, C)
    assert row["n_years"] == pytest.approx(4.0)
    assert pd.isna(row["np_med"]) and pd.isna(row["ttm_vs_med"])
    assert not bool(row["margin_peak"])


def test_tc_ccp_008_nothing_visible(panel: PanelHarness) -> None:
    """TC-CCP-008"""
    frame = panel.build("20100101")
    assert frame.empty and list(frame.columns) == COLUMNS


def test_tc_ccp_009_errors_and_arguments() -> None:
    """TC-CCP-009"""
    panel = CompanyCyclePanel(DateCodec(), DiscoverySettings())
    assert panel.list_fields() == [*FLOWS, *STOCKS]
    assert panel.compute_start(AS_OF) == "20150101"
    with pytest.raises(ValueError):
        panel.build(pd.DataFrame(columns=["ts_code", "end_date", "field", "value"]), "2026-11-06")
    with pytest.raises(ValueError):
        panel.build(pd.DataFrame({"ts_code": [A]}), AS_OF)


def test_tc_ccp_010_list_quarters(panel: PanelHarness) -> None:
    """TC-CCP-010"""
    start = panel.panel.compute_start(AS_OF)
    versions = panel.reader.read_versions(panel.panel.list_fields(), AS_OF, start)
    hist = panel.panel.list_quarters(versions, AS_OF, count=3)
    rows = hist[hist["ts_code"] == A]
    assert rows["period"].tolist() == ["20260331", "20260630", "20260930"]
    assert rows["np_q"].tolist() == pytest.approx([4.0, 5.0, 11.0])
    assert rows["np_dedt_q"].iloc[-1] == pytest.approx(10.0)
    with pytest.raises(ValueError):
        panel.panel.list_quarters(versions, AS_OF, count=0)
