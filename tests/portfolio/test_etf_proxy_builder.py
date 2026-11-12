"""Contract tests for portfolio.EtfProxyBuilder (plan 15 phase 7b, D-126)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_proxy_settings import EtfProxyIndex, EtfProxySettings
from quant_cn.core.exceptions import LakeError
from quant_cn.portfolio.etf_flow_calculator import EtfFlowCalculator
from quant_cn.portfolio.etf_proxy_builder import EtfProxyBuilder
from tests.support import MiniLake, SampleFactorLake

CORE, OTHER, BOND = "510300.SH", "159925.SZ", "511010.SH"
D1, D2, D3, D4 = "20260105", "20260106", "20260107", "20260112"  # D4 in the next ISO week
SETTINGS = EtfProxySettings(
    start=D1,
    core=[CORE],
    indices=[EtfProxyIndex(name="沪深300", benchmark="沪深300指数", reference=CORE)],
    recent_days=2,
)


def _build_builder(lake: MiniLake, config: Config, settings: EtfProxySettings) -> EtfProxyBuilder:
    cfg = config.model_copy(update={"etf_proxy": settings})
    return EtfProxyBuilder(cfg, lake.query, DateCodec(), EtfFlowCalculator(settings))


def _write_lake(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    funds = [
        (CORE, "华泰柏瑞沪深300ETF", "沪深300指数\u00d7100%"),
        (OTHER, "嘉实沪深300ETF", "沪深300指数\u00d7100%"),
        (BOND, "国债ETF", "上证5年期国债指数\u00d7100%"),
    ]
    w(
        lake,
        config,
        "fund_basic",
        [{"ts_code": c, "name": n, "benchmark": b, "market": "E"} for c, n, b in funds],
    )
    px = [(D1, 4.0, 4.0), (D2, 4.4, 4.0), (D3, 4.4, 4.4), (D4, 4.4, 4.4), ("20260113", 4.4, 4.4)]
    w(
        lake,
        config,
        "fund_daily",
        [
            {"ts_code": c, "trade_date": d, "close": v, "pre_close": p}
            for c in (CORE, OTHER)
            for d, v, p in px
        ],
    )
    shares = {CORE: [1e6, 1e6, 5e5, 6e5], OTHER: [1e5, 1e5, 1e5, 2e5]}  # 万份 (100 亿份 = 1e6)
    w(
        lake,
        config,
        "fund_share",
        [
            {"ts_code": c, "trade_date": d, "fd_share": s}
            for c, v in shares.items()
            for d, s in zip((D1, D2, D3, D4), v, strict=True)
        ],
    )


@pytest.fixture
def built(lake: MiniLake, config: Config) -> dict[str, Any]:
    _write_lake(lake, config)
    return _build_builder(lake, config, SETTINGS).build()


def _to_approx(value: Any) -> Any:
    """Wrap every float (also inside dicts and lists) in pytest.approx (no float ==, §6)."""
    if isinstance(value, float):
        return pytest.approx(value)
    if isinstance(value, dict):
        return {k: _to_approx(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_to_approx(v) for v in value]
    return value


# TC-EP-001
def test_tc_ep_001_core_and_other(built: dict[str, Any]) -> None:
    assert built["as_of"] == D4 and built["price_as_of"] == "20260113" and built["n_members"] == 2
    core, other = built["totals"]["core"], built["totals"]["other"]
    # core: AUM 400 -> 440 (price) -> 220 (redeem 50 亿份 at 4.4) -> 264 (+10 亿份);
    # peak 400 亿 at D1 is 440 at today's price (x1.1)
    assert core == _to_approx(
        {
            "aum": 264.0,
            "position": 264.0,
            "flow_recent": -176.0,
            "flow_ytd": -176.0,
            "peak": {"date": D1, "position": 440.0},
            "trough_since_peak": {"date": D3, "position": 220.0},
        }
    )
    assert [other["position"], other["flow_ytd"]] == _to_approx([88.0, 44.0])
    assert built["recent"] == _to_approx(
        [{"date": D3, "core": -220.0, "other": 0.0}, {"date": D4, "core": 44.0, "other": 44.0}]
    )
    assert built["yearly"] == _to_approx([{"year": "2026", "core": -176.0, "other": 44.0}])
    assert built["weekly"] == _to_approx(
        [
            {
                "date": D3,
                "core_flow": -220.0,
                "core_position": 220.0,
                "other_flow": 0.0,
                "other_position": 44.0,
            },
            {
                "date": D4,
                "core_flow": 44.0,
                "core_position": 264.0,
                "other_flow": 44.0,
                "other_position": 88.0,
            },
        ]
    )
    index = built["indices"][0]
    assert (index["name"], index["reference"], index["n_etf"]) == ("沪深300", CORE, 2)
    assert [index["aum"], index["position"], index["core_position"]] == _to_approx(
        [352.0, 352.0, 264.0]
    )
    assert index["flow_ytd"] == pytest.approx(-132.0)
    assert index["weekly"] == _to_approx(
        [
            {"date": D3, "position": 264.0, "flow": -220.0},
            {"date": D4, "position": 352.0, "flow": 88.0},
        ]
    )


# TC-EP-002
def test_tc_ep_002_no_indices(lake: MiniLake, config: Config) -> None:
    doc = _build_builder(lake, config, EtfProxySettings()).build()
    assert doc["indices"] == [] and doc["as_of"] == "" and doc["n_members"] == 0


# TC-EP-003
def test_tc_ep_003_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    builder = _build_builder(lake, config, EtfProxySettings())
    path = builder.write(tmp_path)
    assert path == tmp_path / "etf_proxy.json"
    assert json.loads(path.read_text(encoding="utf-8"))["indices"] == []
    with pytest.raises(LakeError):
        builder.write(tmp_path / "missing")


# TC-EP-004
def test_tc_ep_004_no_share_rows(lake: MiniLake, config: Config) -> None:
    SampleFactorLake.write(
        lake,
        config,
        "fund_basic",
        [
            {
                "ts_code": CORE,
                "name": "沪深300ETF",
                "benchmark": "沪深300指数\u00d7100%",
                "market": "E",
            }
        ],
    )
    SampleFactorLake.write(
        lake, config, "fund_share", [{"ts_code": CORE, "trade_date": "20200102", "fd_share": 1.0}]
    )
    with pytest.raises(LakeError):
        _build_builder(lake, config, SETTINGS).build()
