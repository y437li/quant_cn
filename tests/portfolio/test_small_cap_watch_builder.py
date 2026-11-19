"""Contract tests for portfolio.SmallCapWatchBuilder (plan 30)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.core.small_cap_watch_settings import (
    MarginEpisode,
    SmallCapWatchSettings,
    WatchEtf,
    WatchIndex,
)
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator
from quant_cn.portfolio.small_cap_watch_builder import SmallCapWatchBuilder
from quant_cn.portfolio.small_cap_watch_rows import SmallCapWatchRows
from tests.support import MiniLake, Sample, SampleFactorLake

DAYS = [d.strftime("%Y%m%d") for d in pd.bdate_range("20260803", periods=12)]
LAST = DAYS[-1]
SMALL = [100.0, 102.0, 99.0, 103.0, 98.0, 104.0, 97.0, 101.0, 99.0, 103.0, 102.0, 100.0]


def _build_settings(**kw: object) -> SmallCapWatchSettings:
    base: dict[str, object] = {
        "levels": [101.0, 98.0, 90.0], "panic_limit_downs": 1, "low_window": 3,
        "low_share_trigger": 0.6, "ma_window": 2, "vol_window": 2, "pct_window": 5,
        "pct_min_obs": 3, "history": 10, "flow_days": 2,
        "etfs": [WatchEtf(code="512100.SH", name="中证1000ETF", own_row=True)],
        "small_index": WatchIndex(code="000852.SH", name="中证1000"),
        "large_index": WatchIndex(code="000300.SH", name="沪深300"),
        "star_index": WatchIndex(code="000688.SH", name="科创50"),
    }  # fmt: skip
    return SmallCapWatchSettings(**(base | kw))


def _write(lake: MiniLake, config: Config, funds: bool = True, daily: bool = True) -> None:
    w = SampleFactorLake.write
    w(lake, config, "trade_cal", Sample.build_trade_cal(DAYS).to_dict("records"))
    closes = {
        "A.SZ": [10.0] * 11 + [9.0],  # at a 3-day low on the last day, at its down limit
        "B.SZ": [10.0 + i for i in range(12)],  # rising; one tick above its down limit
        "C.SZ": [None] * 10 + [5.0, 6.0],  # two days only: no 3-day low row
    }
    rows, limits = [], []
    for code, values in closes.items():
        for day, close in zip(DAYS, values, strict=True):
            if close is not None:
                rows.append({"ts_code": code, "trade_date": day, "close": close})
    limits = [
        {"ts_code": "A.SZ", "trade_date": LAST, "down_limit": 9.0},
        {"ts_code": "B.SZ", "trade_date": LAST, "down_limit": closes["B.SZ"][-1] - 0.01},
        {"ts_code": "C.SZ", "trade_date": LAST, "down_limit": 0.0},
    ]
    if daily:
        w(lake, config, "daily", rows)
        w(lake, config, "adj_factor", [
            {"ts_code": r["ts_code"], "trade_date": r["trade_date"], "adj_factor": 1.0}
            for r in rows
        ])  # fmt: skip
        w(lake, config, "stk_limit", limits)
        DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    large = [100.0 * 1.01**i for i in range(12)]  # constant log return: zero vol
    w(lake, config, "index_daily", [
        {"ts_code": c, "trade_date": d, "close": v, "amount": 20.0 if d == LAST else 10.0}
        for c, series in (("000852.SH", SMALL), ("000300.SH", large))
        for d, v in zip(DAYS, series, strict=True)
    ])  # fmt: skip
    if funds:
        w(lake, config, "fund_daily", [
            {"ts_code": "512100.SH", "trade_date": d, "close": 1.0, "pre_close": 1.0}
            for d in DAYS
        ])  # fmt: skip
        w(lake, config, "fund_share", [
            {"ts_code": "512100.SH", "trade_date": DAYS[-2], "fd_share": 100.0},
            {"ts_code": "512100.SH", "trade_date": LAST, "fd_share": 150.0},
        ])  # fmt: skip


# financing balance in 亿 per session; DAYS[8] has SSE only (half a total) and must be dropped
MARGIN = [100.0, 100.0, 100.0, 100.0, 100.0, 90.0, 85.0, 80.0, 82.0, 84.0, 86.0, 88.0]


def _write_margin(lake: MiniLake, config: Config) -> None:
    rows = [
        {"trade_date": d, "exchange_id": ex, "rzye": v / 2 * 1e8}
        for i, (d, v) in enumerate(zip(DAYS, MARGIN, strict=True))
        for ex in (("SSE",) if i == 8 else ("SSE", "SZSE"))
    ]
    SampleFactorLake.write(lake, config, "margin", rows)
    # float market cap 4,400 亿 every session (circ_mv in 万元, two stocks)
    caps = [
        {"ts_code": c, "trade_date": d, "circ_mv": 2.2e7} for c in ("A.SZ", "B.SZ") for d in DAYS
    ]
    SampleFactorLake.write(lake, config, "daily_basic", caps)
    # per-stock financing for the percentile: same totals, two stocks a day; DAYS[3] has one only
    detail = [
        {"ts_code": c, "trade_date": d, "rzye": v / 2 * 1e8}
        for i, (d, v) in enumerate(zip(DAYS, MARGIN, strict=True))
        for c in (("A.SZ",) if i == 3 else ("A.SZ", "B.SZ"))
    ]
    SampleFactorLake.write(lake, config, "margin_detail", detail)


def _build(lake: MiniLake, config: Config, **kw: object) -> SmallCapWatchBuilder:
    settings = _build_settings(**kw)
    flows = EtfFlowCalculator(config.etf_proxy)
    vols = RealizedVolCalculator(settings.pct_window, settings.pct_min_obs)
    return SmallCapWatchBuilder(settings, lake.query, flows, SmallCapWatchRows(settings), vols)


def _get_rows(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(r["key"]): r for r in doc["rows"]}


# TC-SCW-001
def test_tc_scw_001_limit_downs(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    rows = _get_rows(_build(lake, config).build(None))
    assert rows["limit_downs"]["value"] == 1.0  # A at its limit; B a tick above; C limit 0
    assert rows["limit_downs"]["state"] == "on" and rows["limit_downs"]["date"] == LAST


# TC-SCW-002
def test_tc_scw_002_breadth(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    rows = _get_rows(_build(lake, config).build(None))
    assert rows["low_share"]["value"] == pytest.approx(0.5)  # A of A, B; C has 2 of 3 days
    assert rows["low_share"]["state"] == "near"  # 0.5 >= 0.8 x 0.6
    assert rows["above_ma"]["value"] == pytest.approx(2 / 3)
    assert rows["above_ma"]["state"] == "info"


# TC-SCW-003
def test_tc_scw_003_levels(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    rows = _get_rows(_build(lake, config).build(None))
    assert rows["level_101"]["state"] == "on"  # 100 <= 101
    assert rows["level_98"]["state"] == "near"  # 100 <= 98 x 1.03
    assert rows["level_90"]["state"] == "off"
    assert rows["drawdown"]["value"] == pytest.approx(100 / 104 - 1)


# TC-SCW-004
def test_tc_scw_004_vol_and_gap(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    doc = _build(lake, config).build(None)
    rows = _get_rows(doc)
    rets = np.log(np.array([102.0, 100.0]) / np.array([103.0, 102.0]))
    expected = float(np.std(rets, ddof=1)) * math.sqrt(252) * 100
    assert rows["small_vol"]["value"] == pytest.approx(expected)
    assert rows["gap"]["value"] == pytest.approx(expected, abs=1e-6)  # 沪深300 vol is 0
    gaps = [h["gap"] for h in doc["history"] if h["gap"] is not None][-5:]
    assert rows["gap"]["pct"] == pytest.approx(sum(g <= gaps[-1] for g in gaps) / len(gaps))
    assert rows["star_vol"]["value"] is None and rows["star_vol"]["state"] == "off"


# TC-SCW-005
def test_tc_scw_005_etf_flows(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    rows = _get_rows(_build(lake, config).build(None))
    assert rows["etf_flow_1d"]["value"] == pytest.approx(0.005)  # 50万份 x 1.0 in 亿
    assert rows["etf_flow_nd"]["value"] == pytest.approx(0.005)
    assert rows["flow_512100.SH"]["value"] == pytest.approx(0.005)


# TC-SCW-006
def test_tc_scw_006_new_triggered_once(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    builder = _build(lake, config)
    first = builder.build(None)
    assert {"limit_downs", "level_101"} <= set(first["new_triggered"])
    assert builder.build(first)["new_triggered"] == []


# TC-SCW-007
def test_tc_scw_007_missing_funds(lake: MiniLake, config: Config) -> None:
    _write(lake, config, funds=False)
    doc = _build(lake, config).build(None)
    assert "etf_flow" in doc["missing"] and "etf_flow_1d" not in _get_rows(doc)


# TC-SCW-008
def test_tc_scw_008_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    _write(lake, config)
    path = _build(lake, config).write(tmp_path)
    assert path.name == "smallcap_watch.json"
    assert json.loads(path.read_text(encoding="utf-8"))["as_of"] == LAST
    with pytest.raises(LakeError):
        _build(lake, config).write(tmp_path / "nope")


# TC-SCW-009
def test_tc_scw_009_empty_daily(lake: MiniLake, config: Config) -> None:
    _write(lake, config, daily=False)
    with pytest.raises(LakeError):
        _build(lake, config).build(None)


# TC-SCW-010
def test_tc_scw_010_margin(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    assert "margin" in _build(lake, config).build(None)["missing"]
    _write_margin(lake, config)
    kw = {"margin_turn_days": 2, "margin_high_days": 10, "margin_ma_days": 3}
    doc = _build(lake, config, **kw).build(None)
    rows = _get_rows(doc)
    assert rows["margin_balance"]["value"] == pytest.approx(88.0)
    # kept sessions 100 x5, 90, 85, 80, 84, 86, 88: high of the last 10 = 100 -> -12%;
    # 2-session change 88 / 84 - 1 > 0 -> 企稳 on at the -10% trigger
    assert rows["margin_turn"]["value"] == pytest.approx(88 / 84 - 1)
    assert rows["margin_turn"]["state"] == "on" and "-12.0%" in rows["margin_balance"]["note"]
    assert {h["date"]: h["rz"] for h in doc["history"]}[DAYS[8]] is None  # half day dropped
    assert rows["margin_level"]["value"] == pytest.approx(2.0)  # 88 / 4,400 亿 = 2% of float cap
    # pct over pct_window 5 of the full detail days (DAYS[3] partial): 80, 82, 84, 86, 88 -> 1.0
    assert rows["margin_level"]["pct"] == pytest.approx(1.0)
    shallow = _build(lake, config, margin_dd_trigger=-0.13, **kw).build(None)
    assert _get_rows(shallow)["margin_turn"]["state"] == "off"


# TC-SCW-011
def test_tc_scw_011_selloff_inputs(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    kw = {"selloff_drop": -0.015, "selloff_near_drop": -0.01, "turnover_window": 3}
    rows = _get_rows(_build(lake, config, **kw).build(None))
    assert rows["selloff"]["value"] == pytest.approx(100 / 102 - 1)
    assert rows["selloff"]["state"] == "on"  # -1.96% on 20 / mean(10, 10, 10) = 2.0x
    assert "2.00 倍" in rows["selloff"]["note"]
    assert "entry_1" not in rows  # no entry_since


# TC-SCW-012
def test_tc_scw_012_margin_share_long(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    _write_margin(lake, config)
    points = _build(lake, config).build(None)["margin_share_long"]
    assert [p["date"] for p in points] == [DAYS[4], DAYS[9], DAYS[11]]  # last day of each week
    assert points[0]["share"] == pytest.approx(100 / 4400 * 100, abs=1e-4)
    assert points[-1]["share"] == pytest.approx(88 / 4400 * 100, abs=1e-4)
    assert points[-1]["small"] == SMALL[-1]
    _build(lake, config, margin_long_start="20260807")  # field accepted
    late = _build(lake, config, margin_long_start="20260807").build(None)["margin_share_long"]
    assert late[0]["date"] == DAYS[4]


# TC-SCW-013
def test_tc_scw_013_margin_depth_and_pace(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    _write_margin(lake, config)
    episodes = [MarginEpisode(name="2018", depth=-0.33, months=12)]
    kw = {"margin_high_days": 3, "margin_speed_span": 2, "margin_acc_days": 1}
    doc = _build(lake, config, margin_episodes=episodes, **kw).build(None)
    rows = _get_rows(doc)
    # long high 100 since margin_long_start -> 88 / 100 - 1; the 3-session high is 88 -> 0%
    assert rows["margin_depth"]["value"] == pytest.approx(-0.12)
    assert "-0.0%" in rows["margin_balance"]["note"] or "+0.0%" in rows["margin_balance"]["note"]
    kept = pd.Series([100.0] * 5 + [90.0, 85.0, 80.0, 84.0, 86.0, 88.0])  # DAYS[8] half day
    speed = kept.diff().ewm(span=2).mean()
    want = f"速度 {speed.iloc[-1]:+.0f} 亿/日"
    assert (
        want in rows["margin_depth"]["note"]
        and "2018 -33% (12 个月)" in rows["margin_depth"]["note"]
    )
    assert speed.iloc[-1] > 0 and rows["margin_depth"]["note"].startswith("走平")  # +1.6 < 20
    assert doc["margin_share_long"][-1]["rz"] == pytest.approx(88.0)
    assert doc["margin_episodes"] == [{"name": "2018", "depth": -0.33, "months": 12}]
