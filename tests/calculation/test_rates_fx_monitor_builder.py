"""Contract tests for RatesFxSeriesReader and RatesFxMonitorBuilder (plan 34, D-171)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.calculation.rates_fx_monitor_builder import RatesFxMonitorBuilder
from quant_cn.calculation.rates_fx_series_reader import RatesFxSeriesReader
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.core.rates_fx_monitor_settings import RatesFxLine, RatesFxMonitorSettings
from tests.support import MiniLake, SampleFactorLake

DAYS = [d.strftime("%Y%m%d") for d in pd.bdate_range("20250101", "20261117")]
GOVT, BANK = "中债国债收益率曲线", "中债商业银行普通债收益率曲线(AAA)"


def _build_line(key: str, kind: str, unit: str, **kw: object) -> RatesFxLine:
    return RatesFxLine(key=key, name=key, group="债市" if unit != "rate" else "汇率",
                       kind=kind, unit=unit, **kw)  # type: ignore[arg-type]  # fmt: skip


def _build_settings(*extra: RatesFxLine) -> RatesFxMonitorSettings:
    lines = [
        _build_line("cn_10y", "curve", "yield", curve=GOVT, field="y_10y", extreme=True,
              week_move=10, below=1.5),
        _build_line("bank_10y", "curve", "yield", curve=BANK, field="y_10y", show=False),
        _build_line("credit", "combo", "bp", op="diff", a="bank_10y", b="cn_10y", week_widen=10),
        _build_line("usdcnh", "fx", "rate", code="USDCNH.FXCM", week_move=0.01),
        _build_line("fix_usd", "fixing", "rate", field="usd"),
        _build_line("gap", "combo", "gap", op="gap", a="usdcnh", b="fix_usd", abs_above=0.01),
        _build_line("eurusd", "fx", "rate", code="EURUSD.FXCM"),
        _build_line("eurcnh", "combo", "rate", op="mul", a="eurusd", b="usdcnh"),
        _build_line("cnhjpy", "combo", "rate", op="div", a="eurusd", b="usdcnh"),
        _build_line("ep", "equity_ep", "yield", code="000300.SH", show=False),
        _build_line("erp", "combo", "bp", op="diff", a="ep", b="cn_10y", pct_above=0.9),
        *extra,
    ]  # fmt: skip
    return RatesFxMonitorSettings(min_obs=20, history_start="20250101", stale_days=4,
                                  curve={"curve": GOVT, "fields": ["y_1y", "y_10y"]},
                                  lines=lines)  # fmt: skip


def _write(lake: MiniLake, config: Config, last_10y: float = 1.40, fx: bool = True) -> None:
    w = SampleFactorLake.write
    n = len(DAYS)
    govt = [2.0 - 0.0002 * i for i in range(n - 1)] + [last_10y]  # falls slowly, then last
    bank = [g + 0.20 for g in govt[:-5]] + [g + 0.35 for g in govt[-5:]]  # widens 15bp in the week
    w(lake, config, "cn_bond_yield", [
        {"curve_name": c, "trade_date": d, "y_1y": 1.2, "y_10y": v}
        for c, vals in ((GOVT, govt), (BANK, bank)) for d, v in zip(DAYS, vals, strict=True)
    ])  # fmt: skip
    if fx:
        cnh = [7.0] * (n - 6) + [7.0, 7.0, 7.0, 7.0, 7.0, 7.10]  # +1.43% in the last week
        rows = [
            {
                "ts_code": "USDCNH.FXCM",
                "trade_date": d,
                "bid_close": v - 0.01,
                "ask_close": v + 0.01,
            }
            for d, v in zip(DAYS, cnh, strict=True)
        ]
        rows += [{"ts_code": "EURUSD.FXCM", "trade_date": d, "bid_close": 1.1,
                  "ask_close": 1.1} for d in DAYS]  # fmt: skip
        w(lake, config, "fx_daily", rows)
    w(lake, config, "cny_fixing", [{"trade_date": d, "usd": 700.0} for d in DAYS[:-1]])
    w(lake, config, "index_weight", [
        {"index_code": "000300.SH", "con_code": c, "trade_date": "20241231", "weight": 50.0}
        for c in ("A.SH", "B.SH")
    ])  # fmt: skip
    w(lake, config, "daily_basic", [
        {"ts_code": c, "trade_date": d, "total_mv": mv, "pe_ttm": pe}
        for d in DAYS[-30:] for c, mv, pe in (("A.SH", 100.0, 10.0), ("B.SH", 300.0, 20.0),
                                              ("C.SH", 900.0, 1.0))
    ])  # fmt: skip


def _build_builder(lake: MiniLake, settings: RatesFxMonitorSettings) -> RatesFxMonitorBuilder:
    return RatesFxMonitorBuilder(settings, RatesFxSeriesReader(settings, lake.query), lake.query)


# TC-RFR-001
def test_tc_rfr_001_sources(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    s = RatesFxSeriesReader(_build_settings(), lake.query).read_series("20250101")
    assert s["cn_10y"].iloc[-1] == pytest.approx(1.40) and s["cn_10y"].index[0] == "20250101"
    assert s["fix_usd"].iloc[-1] == pytest.approx(7.0)
    assert s["usdcnh"].iloc[-1] == pytest.approx(7.10)


# TC-RFR-002
def test_tc_rfr_002_combos(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    s = RatesFxSeriesReader(_build_settings(), lake.query).read_series("20250101")
    assert s["credit"].iloc[-1] == pytest.approx(35.0)
    assert s["gap"].iloc[-1] == pytest.approx(7.10 / 7.0 - 1)  # fixing carried to the last day
    assert s["eurcnh"].iloc[-1] == pytest.approx(1.1 * 7.10)
    assert s["cnhjpy"].iloc[-1] == pytest.approx(1.1 / 7.10)


# TC-RFR-003
def test_tc_rfr_003_equity_ep(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    s = RatesFxSeriesReader(_build_settings(), lake.query).read_series("20250101")
    assert s["ep"].iloc[-1] == pytest.approx(100 * (10 + 15) / 400)  # C.SH is not a member


# TC-RFR-004
def test_tc_rfr_004_unreadable(lake: MiniLake, config: Config) -> None:
    _write(lake, config, fx=False)
    s = RatesFxSeriesReader(_build_settings(), lake.query).read_series("20250101")
    assert s["usdcnh"].empty and s["gap"].empty


# TC-RFM-001
def test_tc_rfm_001_rows(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    doc = _build_builder(lake, _build_settings()).build(None)
    rows = {r["key"]: r for r in doc["rows"]}
    ten = rows["cn_10y"]
    assert ten["chg"]["1w"] == pytest.approx(
        (1.40 - (2.0 - 0.0002 * (len(DAYS) - 6))) * 100, abs=0.1
    )
    assert ten["pct"] == pytest.approx(1 / len(DAYS), abs=0.01) and ten["low_1y"] > 1.40
    assert rows["usdcnh"]["chg"]["1w"] == pytest.approx(7.10 / 7.0 - 1, abs=1e-4)


# TC-RFM-002
def test_tc_rfm_002_alerts(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    builder = _build_builder(lake, _build_settings())
    doc = builder.build(None)
    kinds = {f["key"] for f in doc["flags"]}
    assert {"cn_10y:extreme", "cn_10y:week_move", "cn_10y:below", "credit:week_widen",
            "usdcnh:week_move", "gap:abs", "erp:pct"} <= kinds  # fmt: skip
    assert set(doc["new_flags"]) == kinds
    assert builder.build(doc)["new_flags"] == []


# TC-RFM-003
def test_tc_rfm_003_pit_missing_stale(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    extra = _build_line("dxy", "fx", "rate", code="USDOLLAR")
    doc = _build_builder(lake, _build_settings(extra)).build(None, as_of="20261110")
    rows = {r["key"]: r for r in doc["rows"]}
    assert doc["as_of"] == "20261110" and rows["cn_10y"]["date"] == "20261110"
    assert "dxy" in doc["missing"] and "bank_10y" not in rows and "ep" not in rows
    late = _build_builder(lake, _build_settings()).build(None, as_of="20261130")
    assert "cn_10y" in late["stale"]


# TC-RFM-004
def test_tc_rfm_004_curve_and_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    _write(lake, config)
    builder = _build_builder(lake, _build_settings())
    doc = builder.build(None)
    assert doc["curve"]["tenors"] == ["1Y", "10Y"]
    assert [p["label"] for p in doc["curve"]["points"]] == ["今天", "1 月前", "1 年前"]
    path = builder.write(tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["as_of"] == DAYS[-1]
    with pytest.raises(LakeError):
        builder.write(tmp_path / "missing")
    with pytest.raises(LakeError):
        _build_builder(
            lake, RatesFxMonitorSettings(lines=[_build_line("x", "us", "yield", field="us_10y")])
        ).build(None)
