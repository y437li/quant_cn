"""Contract tests for calculation.FuturesMonitorBuilder (plan 15 ph7i, D-145)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.calculation.futures_monitor_builder import FuturesMonitorBuilder
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings
from tests.support import MiniLake, SampleFactorLake

DATES = [f"202611{d:02d}" for d in range(1, 21)]
# month -> (price offset, oi); 2611 is the delivery month with almost no open interest
CU = {"202611": (100.0, 10.0), "202612": (0.0, 5000.0), "202701": (-1.0, 3000.0),
      "202702": (-2.0, 2000.0), "202703": (-3.0, 2000.0), "202704": (-4.0, 2000.0)}  # fmt: skip


def _build_settings(**kw: object) -> FuturesMonitorSettings:
    raw = {
        "families": [
            {"family": "CU.SHF", "name": "铜", "group": "有色"},
            {"family": "RB.SHF", "name": "螺纹钢", "group": "黑色"},
            {"family": "ZN.SHF", "name": "锌", "group": "有色"},
        ],
        "spreads": [
            {"key": "cu_rb", "name": "铜-2x螺纹", "legs": [
                {"family": "CU.SHF", "coef": 1.0}, {"family": "RB.SHF", "coef": -2.0}]},
            {"key": "cu_rb_ratio", "name": "铜/螺纹", "kind": "ratio", "legs": [
                {"family": "CU.SHF", "coef": 10.0}, {"family": "RB.SHF", "coef": 2.0}]},
        ],
    }  # fmt: skip
    return FuturesMonitorSettings(**(raw | kw))


def _write(lake: MiniLake, config: Config, last_front: float | None = None) -> None:
    w = SampleFactorLake.write
    basic = [{"ts_code": f"CU{m[2:]}.SHF", "fut_code": "CU", "exchange": "SHFE", "d_month": m}
             for m in CU] + [{"ts_code": "RB2701.SHF", "fut_code": "RB", "exchange": "SHFE",
                              "d_month": "202701"}]  # fmt: skip
    w(lake, config, "fut_basic", basic)
    rows = []
    for i, d in enumerate(DATES):
        for m, (off, oi) in CU.items():
            base = 100.0 + i if m != "202703" else 100.0  # 4th liquid month fixed at 100
            price = base + off if m != "202703" else base
            if m == "202612" and i == len(DATES) - 1 and last_front is not None:
                price = last_front
            rows.append({"ts_code": f"CU{m[2:]}.SHF", "trade_date": d, "settle": price,
                         "close": price, "oi": oi + i, "vol": 1.0})  # fmt: skip
        rows.append({"ts_code": "RB2701.SHF", "trade_date": d, "settle": 50.0, "close": 50.0,
                     "oi": 9000.0, "vol": 1.0})  # fmt: skip
    w(lake, config, "fut_daily", rows)


def test_tc_fum_001_family(lake: MiniLake, config: Config) -> None:
    """TC-FUM-001"""
    _write(lake, config)
    doc = FuturesMonitorBuilder(_build_settings(), lake.query).build(None)
    cu = next(f for f in doc["families"] if f["family"] == "CU.SHF")
    assert doc["as_of"] == "20261120" and cu["contract"] == "CU2612.SHF" and cu["price"] == 119.0
    assert cu["chg_1w"] == round(119 / 114 - 1, 4)
    assert cu["front_vs_4th"] == round(119 / 100 - 1, 4) and cu["front_vs_4th_pct"] == 1.0
    assert cu["oi"] == 5000 + 3000 + 2000 * 3 + 10 + 6 * 19
    assert [c["month"] for c in cu["curve"]] == ["202612", "202701", "202702", "202703", "202704"]


def test_tc_fum_002_delivery_month_skipped(lake: MiniLake, config: Config) -> None:
    """TC-FUM-002"""
    _write(lake, config)
    doc = FuturesMonitorBuilder(_build_settings(), lake.query).build(None)
    cu = next(f for f in doc["families"] if f["family"] == "CU.SHF")
    assert all(c["month"] != "202611" for c in cu["curve"])  # oi 10 < min_oi
    assert cu["front_vs_4th"] < 0.5  # 2611 at 219 would give > 1


def test_tc_fum_003_spreads(lake: MiniLake, config: Config) -> None:
    """TC-FUM-003"""
    _write(lake, config)
    doc = FuturesMonitorBuilder(_build_settings(), lake.query).build(None)
    by_key = {s["key"]: s for s in doc["spreads"]}
    assert by_key["cu_rb"]["value"] == 119.0 - 100.0 and by_key["cu_rb"]["chg_1w"] == 5.0
    assert by_key["cu_rb_ratio"]["value"] == round(10 * 119 / (2 * 50), 2)


def test_tc_fum_004_flag_boundary(lake: MiniLake, config: Config) -> None:
    """TC-FUM-004"""
    _write(lake, config, last_front=117.5)  # 19 of 20 values <= latest: 95th pct
    builder = FuturesMonitorBuilder(_build_settings(), lake.query)
    doc = builder.build(None)
    assert "curve:CU.SHF" in doc["new_flags"]
    assert builder.build(doc)["new_flags"] == []


def test_tc_fum_007_inside(lake: MiniLake, config: Config) -> None:
    """TC-FUM-007"""
    _write(lake, config, last_front=116.5)  # 18 of 20: 90th pct
    doc = FuturesMonitorBuilder(_build_settings(), lake.query).build(None)
    assert "curve:CU.SHF" not in {f["key"] for f in doc["flags"]}


def test_tc_fum_005_missing_family(lake: MiniLake, config: Config) -> None:
    """TC-FUM-005"""
    _write(lake, config)
    doc = FuturesMonitorBuilder(_build_settings(), lake.query).build(None)
    assert doc["missing"] == ["ZN.SHF"]
    assert [f["family"] for f in doc["families"]] == ["CU.SHF", "RB.SHF"]


def test_tc_fum_006_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-FUM-006"""
    _write(lake, config)
    builder = FuturesMonitorBuilder(_build_settings(), lake.query)
    with pytest.raises(LakeError):
        builder.write(tmp_path / "nope")
    assert json.loads(builder.write(tmp_path).read_text(encoding="utf-8"))["as_of"] == "20261120"


def test_tc_fum_008_reversion_flag(lake: MiniLake, config: Config) -> None:
    """TC-FUM-008"""
    dates = [d.strftime("%Y%m%d") for d in pd.bdate_range("20260401", periods=130)]
    w = SampleFactorLake.write
    w(
        lake,
        config,
        "fut_basic",
        [
            {"ts_code": "CU2612.SHF", "fut_code": "CU", "exchange": "SHFE", "d_month": "202612"},
            {"ts_code": "RB2701.SHF", "fut_code": "RB", "exchange": "SHFE", "d_month": "202701"},
        ],
    )
    rows = []
    for i, d in enumerate(dates):
        cu = 130.0 if i == len(dates) - 1 else 100.0 + (i % 5)  # last day far above the mean
        rows += [{"ts_code": "CU2612.SHF", "trade_date": d, "settle": cu, "close": cu,
                  "oi": 5000.0, "vol": 1.0},
                 {"ts_code": "RB2701.SHF", "trade_date": d, "settle": 50.0, "close": 50.0,
                  "oi": 9000.0, "vol": 1.0}]  # fmt: skip
    w(lake, config, "fut_daily", rows)
    base = _build_settings().model_dump()
    rev = {**base["spreads"][0], "reversion": True, "half_life_d": 12}
    doc = FuturesMonitorBuilder(_build_settings(spreads=[rev]), lake.query).build(None)
    spread = doc["spreads"][0]
    assert spread["z_1y"] > 2 and spread["reversion"] is True
    flag = next(f for f in doc["flags"] if f["key"] == "reversion:cu_rb")
    assert flag["kind"] == "reversion" and "高于一年均值" in flag["message"]
    assert "12 个交易日" in flag["message"]
    plain = FuturesMonitorBuilder(_build_settings(), lake.query).build(None)
    assert not any(f["kind"] == "reversion" for f in plain["flags"])
