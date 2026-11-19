"""Contract tests for calculation.MacroMonitorBuilder (plan 15 ph7h, D-143)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_cn.calculation.macro_monitor_builder import SERIES, WINDOW, MacroMonitorBuilder
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from tests.support import MiniLake, SampleFactorLake

MONTHS = [f"{y}{m:02d}" for y in (2025, 2026) for m in range(1, 13)][:21]  # 202501..202609


def _write_all(lake: MiniLake, config: Config, skip: tuple[str, ...] = ()) -> None:
    w = SampleFactorLake.write
    rows = {
        "cn_cpi": [{"month": m, "nt_yoy": 0.5, "nt_mom": 0.1} for m in MONTHS],
        "cn_ppi": [
            {"month": m, "ppi_yoy": 3.0, "ppi_mom": 0.2, "ppi_mp_yoy": 4.0, "ppi_cg_yoy": 0.0}
            for m in MONTHS
        ],
        "cn_pmi": [
            {"month": m, "pmi010000": 50.0, "pmi020100": 51.0, "pmi030000": 50.5} for m in MONTHS
        ],
        "cn_m": [{"month": m, "m1_yoy": 3.0, "m2_yoy": 7.5} for m in MONTHS],
        "sf_month": [
            {"month": m, "inc_month": 1000.0 + i, "stk_endval": 400.0 + i}
            for i, m in enumerate(MONTHS)
        ],
    }
    for name, r in rows.items():
        if name not in skip:
            w(lake, config, name, r)


def test_tc_mmb_001_derived(lake: MiniLake, config: Config) -> None:
    """TC-MMB-001"""
    _write_all(lake, config)
    doc = MacroMonitorBuilder(lake.query).build(None)
    by_key = {s["key"]: s for s in doc["series"]}
    assert set(by_key) == {s.key for s in SERIES}
    assert by_key["ppi_cpi_gap"]["value"] == 2.5
    assert by_key["m1_m2"]["value"] == -4.5
    # 202609 is row 20, 202509 row 8: stock 420 / 408, new 1020 - 1008
    assert by_key["sf_stock_yoy"]["value"] == round((420 / 408 - 1) * 100, 2)
    assert by_key["sf_inc_vs_ly"]["value"] == 12.0
    assert doc["as_of"] == "202609" and doc["missing"] == []


def test_tc_mmb_002_new_print_once(lake: MiniLake, config: Config) -> None:
    """TC-MMB-002"""
    _write_all(lake, config)
    builder = MacroMonitorBuilder(lake.query)
    first = builder.build(None)
    assert len(first["new_prints"]) == len(SERIES)
    second = builder.build(first)
    assert second["new_prints"] == [] and not any(s["new_print"] for s in second["series"])


def test_tc_mmb_003_percentile_window(lake: MiniLake, config: Config) -> None:
    """TC-MMB-003"""
    _write_all(lake, config)
    doc = MacroMonitorBuilder(lake.query).build(None)
    inc = next(s for s in doc["series"] if s["key"] == "sf_inc")
    assert inc["pct_5y"] == 1.0  # rising series: latest is the maximum
    assert len(inc["history"]) == min(WINDOW, len(MONTHS))
    stock = next(s for s in doc["series"] if s["key"] == "sf_stock_yoy")
    assert len(stock["history"]) == len(MONTHS) - 12  # no value without last year's stock


def test_tc_mmb_004_missing_table(lake: MiniLake, config: Config) -> None:
    """TC-MMB-004"""
    _write_all(lake, config, skip=("sf_month",))
    doc = MacroMonitorBuilder(lake.query).build(None)
    keys = {s["key"] for s in doc["series"]}
    assert doc["missing"] == ["sf_month"]
    assert not keys & {"sf_inc", "sf_inc_vs_ly", "sf_stock_yoy"} and "cpi" in keys


def test_tc_mmb_006_no_table(lake: MiniLake, config: Config) -> None:
    """TC-MMB-006"""
    with pytest.raises(LakeError):
        MacroMonitorBuilder(lake.query).build(None)


def test_tc_mmb_005_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-MMB-005"""
    _write_all(lake, config)
    builder = MacroMonitorBuilder(lake.query)
    with pytest.raises(LakeError):
        builder.write(tmp_path / "nope")
    path = builder.write(tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["new_prints"]
    assert json.loads(builder.write(tmp_path).read_text(encoding="utf-8"))["new_prints"] == []
