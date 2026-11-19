"""Contract tests for portfolio.SmallCapWatchRows (plan 30)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings, WatchEtf, WatchIndex
from quant_cn.portfolio.small_cap_watch_rows import SmallCapWatchRows

DAYS = ["20261112", "20261113", "20261116"]
SETTINGS = SmallCapWatchSettings(
    small_index=WatchIndex(code="000852.SH", name="中证1000"),
    large_index=WatchIndex(code="000300.SH", name="沪深300"),
    star_index=WatchIndex(code="000688.SH", name="科创50"),
    levels=[6200.0, 6100.0, 5500.0],
    panic_limit_downs=500,
    low_share_trigger=0.7,
    etfs=[WatchEtf(code="512100.SH", name="中证1000ETF", own_row=True)],
)


def _build_frames(
    ld: float, low: float, pct: float
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    market = pd.DataFrame(
        {"limit_downs": [10.0, 20.0, ld], "low_share": [0.1, 0.2, low], "above_ma": [0.5] * 3},
        index=DAYS,
    )
    vols = pd.DataFrame(
        {"small": [6400.0, 6300.0, 6165.0], "small_vol": [30.0, 35.0, 39.3],
         "small_vol_pct": [0.5, 0.7, pct], "star_vol": [None, None, None],
         "star_vol_pct": [None, None, None], "gap": [15.0, 20.0, 22.2],
         "gap_pct": [0.8, 0.9, 0.97], "gap_exit": [11.0, 11.0, 11.1]},
        index=DAYS,
    )  # fmt: skip
    flows = pd.DataFrame({"512100.SH": [-30.0, -20.0, 1.5]}, index=DAYS)
    return market, vols, flows


def _get_rows(**kw: float) -> dict[str, dict[str, Any]]:
    rows, _ = SmallCapWatchRows(SETTINGS).build(*_build_frames(**kw))
    return {r["key"]: r for r in rows}


# TC-SCR-001
def test_tc_scr_001_count_rows() -> None:
    assert _get_rows(ld=500.0, low=0.7, pct=0.5)["limit_downs"]["state"] == "on"
    rows = _get_rows(ld=400.0, low=0.55, pct=0.5)
    assert rows["limit_downs"]["state"] == "near"  # 400 >= 0.8 x 500
    assert rows["low_share"]["state"] == "off"  # 0.55 < 0.8 x 0.7
    assert _get_rows(ld=float("nan"), low=0.1, pct=0.5)["limit_downs"]["state"] == "off"


# TC-SCR-002
def test_tc_scr_002_pct_rows() -> None:
    assert _get_rows(ld=0.0, low=0.0, pct=0.90)["small_vol"]["state"] == "on"
    rows = _get_rows(ld=0.0, low=0.0, pct=0.85)
    assert rows["small_vol"]["state"] == "near" and rows["small_vol"]["pct"] == 0.85
    assert _get_rows(ld=0.0, low=0.0, pct=0.84)["small_vol"]["state"] == "off"
    assert rows["gap"]["state"] == "on" and "11.1" in rows["gap"]["note"]
    assert rows["star_vol"]["value"] is None and rows["star_vol"]["state"] == "off"


# TC-SCR-003
def test_tc_scr_003_level_rows() -> None:
    rows = _get_rows(ld=0.0, low=0.0, pct=0.5)
    assert rows["level_6200"]["state"] == "on"  # 6,165 <= 6,200
    assert rows["level_6100"]["state"] == "near"  # 6,165 <= 6,100 x 1.03
    assert rows["level_5500"]["state"] == "off"
    assert rows["flow_512100.SH"]["value"] == pytest.approx(1.5)
    assert "-48.5" in rows["flow_512100.SH"]["note"]  # 5-day total of the 3 rows


# TC-SCR-004
def test_tc_scr_004_empty_frames() -> None:
    rows, missing = SmallCapWatchRows(SETTINGS).build(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    )
    assert rows == [] and set(missing) == {
        "limit_downs", "low_share", "above_ma", "levels", "small_vol", "star_vol", "gap",
        "etf_flow", "margin",
    }  # fmt: skip


# TC-SCR-005
def test_tc_scr_005_history() -> None:
    market, vols, _ = _build_frames(ld=float("nan"), low=0.3, pct=0.5)
    history = SmallCapWatchRows(SETTINGS).build_history(market, vols, "20261113")
    assert [h["date"] for h in history] == DAYS[1:]
    assert history[-1]["limit_downs"] is None and history[-1]["small"] == 6165.0


# TC-SCR-006
def test_tc_scr_006_margin_rows() -> None:
    def turn(dd: float, chg: float) -> dict[str, Any]:
        market, vols, flows = _build_frames(ld=0.0, low=0.0, pct=0.5)
        margin = {"rz": 22083.0, "rz_dd": dd, "rz_chg": chg, "rz_chg_ma": -0.03, "rz_ma": 22932.0,
                  "rz_circ": 0.0251, "rz_circ_pct": 0.86}  # fmt: skip
        market = market.assign(**{k: [None, None, v] for k, v in margin.items()})
        rows, missing = SmallCapWatchRows(SETTINGS).build(market, vols, flows)
        assert "margin" not in missing
        by_key = {r["key"]: r for r in rows}
        assert by_key["margin_level"]["pct"] == pytest.approx(0.86)
        return by_key["margin_turn"]

    assert turn(-0.10, 0.0)["state"] == "on"  # at the trigger, change exactly 0
    assert turn(-0.099, 0.01)["state"] == "off"  # not deep enough
    assert turn(-0.27, -0.001)["state"] == "off"  # still falling
    rows, missing = SmallCapWatchRows(SETTINGS).build(*_build_frames(ld=0.0, low=0.0, pct=0.5))
    assert "margin" in missing and "margin_turn" not in {r["key"] for r in rows}


# TC-SCR-007
def test_tc_scr_007_entry_rows_order() -> None:
    market, vols, flows = _build_frames(ld=0.0, low=0.0, pct=0.5)
    vols["small_ret"], vols["small_turn"] = [0.0, 0.0, -0.035], [1.0, 1.0, 1.4]
    settings = SETTINGS.model_copy(update={"entry_since": "20261113"})
    rows, _ = SmallCapWatchRows(settings).build(market, vols, flows)
    keys = [r["key"] for r in rows]
    assert keys[:3] == ["entry_1", "entry_2", "entry_3"]
    assert keys.index("selloff") == keys.index("above_ma") + 1
    assert rows[1]["state"] == "on" and rows[keys.index("selloff")]["state"] == "on"
