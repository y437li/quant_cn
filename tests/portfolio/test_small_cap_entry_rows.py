"""Contract tests for portfolio.SmallCapEntryRows (plan 30 ph5)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_cn.core.small_cap_watch_settings import SmallCapWatchSettings, WatchIndex
from quant_cn.portfolio.small_cap_entry_rows import SmallCapEntryRows

DAYS = ["20261118", "20261119", "20261120", "20261123"]


def _build_settings(**kw: Any) -> SmallCapWatchSettings:
    base: dict[str, Any] = {
        "small_index": WatchIndex(code="000852.SH", name="中证1000"),
        "large_index": WatchIndex(code="000300.SH", name="沪深300"),
        "star_index": WatchIndex(code="000688.SH", name="科创50"),
        "levels": [6075.0, 5500.0], "panic_limit_downs": 500, "entry_since": "20261119",
    }  # fmt: skip
    return SmallCapWatchSettings(**(base | kw))


def _build_vols(
    ret: list[float], turn: list[float], small: list[float] | None = None
) -> pd.DataFrame:
    small = small or [6000.0] * len(ret)
    return pd.DataFrame({"small": small, "small_ret": ret, "small_turn": turn}, index=DAYS)


def _build_market(ld: list[float], dd: list[float] | None = None, chg: list[float] | None = None
            ) -> pd.DataFrame:  # fmt: skip
    frame = pd.DataFrame({"limit_downs": ld}, index=DAYS)
    if dd is not None:
        frame["rz_dd"], frame["rz_chg"] = dd, chg
    return frame


def _get_state(ret: float, turn: float) -> str | None:
    row = SmallCapEntryRows(_build_settings()).build_selloff_row(
        _build_vols([0.0, 0.0, 0.0, ret], [1.0, 1.0, 1.0, turn])
    )
    return None if row is None else str(row["state"])


def _get_steps(market: pd.DataFrame, vols: pd.DataFrame, **kw: Any) -> dict[str, dict[str, Any]]:
    rows = SmallCapEntryRows(_build_settings(**kw)).build_tranche_rows(market, vols)
    return {r["key"]: r for r in rows}


# TC-SCE-001
def test_tc_sce_001_selloff_row() -> None:
    assert _get_state(-0.03, 1.3) == "on"
    assert _get_state(-0.0299, 1.3) == "near"  # -2.99% on 1.3x is still near
    assert _get_state(-0.03, 1.29) == "near"
    assert _get_state(-0.02, 1.0) == "near"
    assert _get_state(-0.019, 1.5) == "off"
    assert _get_state(-0.05, 0.9) == "off"
    empty = pd.DataFrame({"small_ret": [float("nan")], "small_turn": [1.0]}, index=DAYS[:1])
    assert SmallCapEntryRows(_build_settings()).build_selloff_row(empty) is None
    row = SmallCapEntryRows(_build_settings()).build_selloff_row(_build_vols([0.0] * 4, [1.0] * 4))
    assert row is not None and row["unit"] == "涨跌" and row["trigger"] == -0.03


# TC-SCE-002
def test_tc_sce_002_step2_keeps_first_date() -> None:
    quiet = _build_vols([0.0] * 4, [1.0] * 4)
    assert _get_steps(_build_market([0, 10, 10, 10]), quiet)["entry_2"]["state"] == "off"
    # panic day on 11-20 only: stays on with its first date
    step = _get_steps(_build_market([0, 10, 600, 10]), quiet)["entry_2"]
    assert step["state"] == "on" and "首次触发 20261120" in step["note"]
    # 放量大跌 on the last day
    step = _get_steps(_build_market([0] * 4), _build_vols([0, 0, 0, -0.04], [1, 1, 1, 1.5]))[
        "entry_2"
    ]
    assert step["state"] == "on" and "今天触发" in step["note"]
    # lowest level touched on 11-19
    step = _get_steps(
        _build_market([0] * 4), _build_vols([0.0] * 4, [1.0] * 4, [6000, 5500, 5600, 5700])
    )
    assert "首次触发 20261119" in step["entry_2"]["note"]
    # a panic day before entry_since does not count
    assert _get_steps(_build_market([900, 0, 0, 0]), quiet)["entry_2"]["state"] == "off"


# TC-SCE-003
def test_tc_sce_003_step3_bought_and_off() -> None:
    quiet = _build_vols([0.0] * 4, [1.0] * 4)
    market = _build_market([0] * 4, dd=[-0.2, -0.2, -0.2, -0.09], chg=[-0.01, -0.01, 0.0, 0.01])
    steps = _get_steps(market, quiet)
    assert steps["entry_1"]["state"] == "on" and "还没买" in steps["entry_1"]["note"]
    assert steps["entry_3"]["state"] == "on" and "首次触发 20261120" in steps["entry_3"]["note"]
    assert (
        _get_steps(_build_market([0] * 4, [-0.2] * 4, [-0.01] * 4), quiet)["entry_3"]["state"]
        == "off"
    )
    bought = _get_steps(market, quiet, entry_bought=1)
    assert bought["entry_1"]["state"] == "info" and bought["entry_1"]["note"] == "已买"
    assert [r["group"] for r in bought.values()] == ["建仓档"] * 3
    assert _get_steps(market, quiet, entry_since=None) == {}
