"""Contract tests for portfolio.SectorMetricReader (plan 31 ph4)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.graph_store import GraphStore
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS, SectorMetricReader
from tests.support import MiniLake, SampleFactorLake

REPO = Path(__file__).resolve().parents[2]
NAMES = {"001979.SZ": "招商蛇口", "600048.SH": "保利发展"}


def build_reader(lake: MiniLake) -> SectorMetricReader:
    settings = SectorMonitorSettings.load(REPO)
    return SectorMetricReader(settings, lake.query, GraphStore(lake.writer, lake.lake_root))


def build_value(row: pd.DataFrame, label: str, period: str) -> float:
    hit = row[(row["label"] == label) & (row["period"] == period)]["value"]
    return float(hit.iloc[0])


# TC-SMR-001
def test_tc_smr_001_house_price_tiers(lake: MiniLake, config: Config) -> None:
    rows = [
        {"month": "202610", "city": c, "house_type": "second_hand", "mom": m, "yoy": 95.0,
         "published": "20261116", "source_url": "u"}
        for c, m in (("北京", 100.4), ("上海", 100.0), ("天津", 99.8), ("唐山", 99.6))
    ]  # fmt: skip
    SampleFactorLake.write(lake, config, "house_price_70", rows)
    out = build_reader(lake).read_house_prices("second_hand")
    assert list(out.columns) == LINE_COLUMNS
    assert build_value(out, "一线", "2026-10") == pytest.approx(0.2)
    assert build_value(out, "二线", "2026-10") == pytest.approx(-0.2)
    assert build_value(out, "三线", "2026-10") == pytest.approx(-0.4)  # 唐山 is in no list


# TC-SMR-002
def test_tc_smr_002_dividends_winner_closes(lake: MiniLake, config: Config) -> None:
    reader = build_reader(lake)
    assert reader.read_dividends(NAMES).empty and reader.read_closes(["001979.SZ"], "X").empty
    SampleFactorLake.write(lake, config, "dividend", [
        {"ts_code": "001979.SZ", "end_date": "20251231", "ann_date": "20260401",
         "div_proc": "实施", "cash_div_tax": 0.051},
        {"ts_code": "001979.SZ", "end_date": "20260630", "ann_date": "20260820",
         "div_proc": "预案", "cash_div_tax": 0.0},
    ])  # fmt: skip
    SampleFactorLake.write(
        lake,
        config,
        "cyq_perf",
        [{"ts_code": "001979.SZ", "trade_date": "20261117", "winner_rate": 54.3}],
    )
    SampleFactorLake.write(lake, config, "sw_daily", [
        {"ts_code": "801180.SI", "trade_date": d, "close": c}
        for d, c in (("20261116", 2000.0), ("20261117", 2010.0))
    ])  # fmt: skip
    dividends = reader.read_dividends(NAMES)
    assert dividends[["label", "period", "value"]].values.tolist() == [["招商蛇口", "2025", 0.051]]
    assert build_value(reader.read_winner_rate(NAMES), "招商蛇口", "20261117") == 54.3
    closes = reader.read_closes(["001979.SZ"], "801180.SI")
    assert list(closes.index) == ["20261116", "20261117"] and "801180.SI" in closes.columns


# TC-SMR-003
def test_tc_smr_003_quarterly_and_games(lake: MiniLake, config: Config) -> None:
    income = [
        ("20260331", -10e8, -1e8, 100e8, 10e8),
        ("20260630", -30e8, -2e8, 250e8, 22e8),
    ]
    SampleFactorLake.write(lake, config, "income_vip", [
        {"ts_code": "001979.SZ", "end_date": e, "ann_date": e, "f_ann_date": e,
         "report_type": "1", "update_flag": "0", "assets_impair_loss": a,
         "credit_impa_loss": c, "revenue": r, "sell_exp": s}
        for e, a, c, r, s in income
    ])  # fmt: skip
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    reader = build_reader(lake)
    impairment = reader.read_quarterly(NAMES, "impairment")
    assert build_value(impairment, "招商蛇口", "20260331") == pytest.approx(11.0)
    assert build_value(impairment, "招商蛇口", "20260630") == pytest.approx(21.0)  # Q2 only
    ratio = reader.read_quarterly(NAMES, "selling_ratio")
    assert build_value(ratio, "招商蛇口", "20260630") == pytest.approx(12 / 150 * 100, abs=0.01)
    graph = GraphStore(lake.writer, lake.lake_root)
    graph.write("game_company", pd.DataFrame({
        "approval_no": ["a", "a", "b", "c"], "ts_code": ["001979.SZ", None, None, None],
        "known_on": ["20261029", "20261029", "20261029", "20260930"],
    }))  # fmt: skip
    games = reader.read_game_approvals(NAMES)
    assert build_value(games, "全部", "2026-10") == 2
    assert build_value(games, "全部", "2026-09") == 1
    assert build_value(games, "招商蛇口", "2026-10") == 1


# TC-SMR-004
def test_tc_smr_004_house_breadth(lake: MiniLake, config: Config) -> None:
    assert build_reader(lake).read_house_breadth().empty
    rows = [
        {"month": "202610", "city": c, "house_type": t, "mom": m, "yoy": 95.0,
         "published": "20261116", "source_url": "u"}
        for c, t, m in (("北京", "new", 99.9), ("上海", "new", 100.2), ("天津", "new", 99.5),
                        ("北京", "second_hand", 100.0), ("上海", "second_hand", 99.0))
    ]  # fmt: skip
    SampleFactorLake.write(lake, config, "house_price_70", rows)
    out = build_reader(lake).read_house_breadth()
    assert sorted(out.values.tolist()) == [["二手", "2026-10", 1.0], ["新房", "2026-10", 2.0]]
