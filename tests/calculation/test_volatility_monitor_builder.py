"""Contract tests for calculation.VolatilityMonitorBuilder (plan 03 ph6, D-152)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.calculation.volatility_monitor_builder import VolatilityMonitorBuilder
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.core.volatility_monitor_settings import VolatilityLine, VolatilityMonitorSettings
from tests.support import MiniLake, Sample, SampleFactorLake, SampleOptions

SESSIONS = [d.strftime("%Y%m%d") for d in pd.bdate_range("20260801", "20261231")]
DAY = "20260828"
US = [f"202608{d:02d}" for d in range(3, 28)]  # 25 days; values 10..33 then the last


def _build_settings(**kw: object) -> VolatilityMonitorSettings:
    lines = [
        VolatilityLine(key="us_vix", name="美国 VIX", group="美国", kind="cboe", code="VIX",
                       alert_level=30.0, alert_jump=0.3, alert_pct=0.9),
        VolatilityLine(key="cn_test", name="测试 VIX", group="A股", kind="option",
                       code="OPTEST"),
    ]  # fmt: skip
    return VolatilityMonitorSettings(**({"window": 250, "min_obs": 5, "lines": lines} | kw))


def _write(lake: MiniLake, config: Config, us_last: float = 34.0, options: bool = True) -> None:
    w = SampleFactorLake.write
    w(lake, config, "trade_cal", Sample.build_trade_cal(SESSIONS).to_dict("records"))
    values = [10.0 + i for i in range(len(US) - 1)] + [us_last]
    us = [{"index_code": "VIX", "trade_date": d, "close": v}
          for d, v in zip(US, values, strict=True)]  # fmt: skip
    w(lake, config, "cboe_vix", us)
    chain = SampleOptions.build_chain(DAY)
    if options:
        basic = chain.drop_duplicates("ts_code")
        w(lake, config, "opt_basic", [
            {"ts_code": r.ts_code, "exchange": "SSE", "name": "test", "opt_code": "OPTEST",
             "call_put": r.call_put, "exercise_price": r.strike, "maturity_date": r.maturity_date}
            for r in basic.itertuples()
        ])  # fmt: skip
        w(lake, config, "opt_daily", [
            {"ts_code": r.ts_code, "trade_date": DAY, "exchange": "SSE", "close": r.close,
             "vol": 1.0, "oi": 1.0}
            for r in chain.itertuples()
        ])  # fmt: skip
    w(lake, config, "shibor", SampleOptions.SHIBOR.to_dict("records"))


# TC-VMB-001
def test_tc_vmb_001_cboe_line(lake: MiniLake, config: Config) -> None:
    _write(lake, config, us_last=20.0)
    doc = VolatilityMonitorBuilder(_build_settings(), lake.query).build(None)
    us = {x["key"]: x for x in doc["lines"]}["us_vix"]
    assert us["value"] == pytest.approx(20.0) and us["chg"] == pytest.approx(-13.0)
    assert us["date"] == US[-1] and us["n_obs"] == len(US)
    assert us["pct"] == pytest.approx(0.48)  # 10..20 and itself: 12 of 25 at or below
    assert us["history"][0] == {"date": US[0], "value": 10.0} and doc["as_of"] == DAY


# TC-VMB-002
def test_tc_vmb_002_option_line(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    doc = VolatilityMonitorBuilder(_build_settings(), lake.query).build(None)
    cn = {x["key"]: x for x in doc["lines"]}["cn_test"]
    assert 15.0 < cn["value"] < 30.0 and cn["quality_flag"] == "ok"
    assert cn["date"] == DAY and cn["pct"] is None  # one day < min_obs


# TC-VMB-003
def test_tc_vmb_003_alerts(lake: MiniLake, config: Config) -> None:
    _write(lake, config, us_last=34.0)  # 34 vs 33 the day before: +3%; level 30 and pct hit
    builder = VolatilityMonitorBuilder(_build_settings(), lake.query)
    first = builder.build(None)
    kinds = {f["kind"] for f in first["flags"]}
    assert kinds == {"level", "pct"} and len(first["new_flags"]) == 2
    assert builder.build(first)["new_flags"] == []
    few = VolatilityMonitorBuilder(_build_settings(min_obs=100), lake.query).build(None)
    assert {f["kind"] for f in few["flags"]} == {"level"}
    _write(lake, config, us_last=43.0)  # 33 -> 43 = +30%
    doc = VolatilityMonitorBuilder(_build_settings(), lake.query).build(None)
    assert "jump" in {f["kind"] for f in doc["flags"]}


# TC-VMB-004
def test_tc_vmb_004_missing(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    extra = VolatilityLine(key="none", name="无", group="A股", kind="option", code="OPNONE")
    settings = _build_settings(lines=[*_build_settings().lines, extra])
    assert VolatilityMonitorBuilder(settings, lake.query).build(None)["missing"] == ["none"]
    gone = VolatilityLine(key="gone", name="无", group="美国", kind="cboe", code="VIX")
    lake.query.sql("DROP VIEW curated.cboe_vix")
    only = _build_settings(lines=[gone])
    assert VolatilityMonitorBuilder(only, lake.query).build(None)["missing"] == ["gone"]


# TC-VMB-006
def test_tc_vmb_006_no_options(lake: MiniLake, config: Config) -> None:
    _write(lake, config, options=False)
    with pytest.raises(LakeError):
        VolatilityMonitorBuilder(_build_settings(), lake.query).build(None)


# TC-VMB-005
def test_tc_vmb_005_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    _write(lake, config)
    builder = VolatilityMonitorBuilder(_build_settings(), lake.query)
    with pytest.raises(LakeError):
        builder.write(tmp_path / "nope")
    doc = json.loads(builder.write(tmp_path).read_text(encoding="utf-8"))
    assert doc["as_of"] == DAY and len(doc["lines"]) == 2
