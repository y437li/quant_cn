"""Contract tests for visualization.VolatilityReportSection (plan 03 ph6, D-152)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.volatility_report_section import VolatilityReportSection


def build_volatility(new: bool = True) -> dict[str, Any]:
    line = {"key": "us_vix", "name": "美国 VIX", "value": 28.2, "chg": 11.6, "pct": 0.97,
            "low": 13.0, "high": 31.1, "date": "20261105"}  # fmt: skip
    cn = {"key": "cn_300", "name": "300ETF VIX", "value": 17.6, "chg": -0.2, "pct": None,
          "low": 16.0, "high": 22.4, "date": "20261113"}  # fmt: skip
    flag = {
        "key": "us_vix:level",
        "kind": "level",
        "name": "美国 VIX",
        "message": "美国 VIX 28.2 ≥ 25",
    }
    return {"as_of": "20261113", "lines": [line, cn], "flags": [flag],
            "new_flags": ["us_vix:level"] if new else []}  # fmt: skip


# TC-VRS-001
def test_tc_vrs_001_summary() -> None:
    s = VolatilityReportSection()
    assert s.build_summary(build_volatility()) == (
        "波动率：美国 VIX 28.2（1年 97% 分位），300ETF VIX 17.6；1 个提醒，新增：美国 VIX 28.2 ≥ 25"
    )
    assert s.build_summary(build_volatility(new=False)).endswith("；1 个提醒")
    assert s.build_summary(build_volatility() | {"flags": []}).endswith("；没有提醒。")
    assert s.build_summary(None) == ""


# TC-VRS-002
def test_tc_vrs_002_rows() -> None:
    s = VolatilityReportSection()
    rows = s.build_rows(build_volatility())
    assert "波动率" in rows and "300ETF VIX" in rows and "美国 VIX 28.2 ≥ 25" in rows
    assert "+11.6" in rows and "#d08a2e" in rows  # alerting line in amber
    assert "数据缺失：没有 volatility_monitor.json" in s.build_rows(None)
