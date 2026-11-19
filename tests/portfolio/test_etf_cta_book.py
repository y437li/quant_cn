"""Contract tests for portfolio.EtfCtaBook (plan 27, D-160)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_cta_settings import EtfCtaSettings
from quant_cn.core.etf_cta_views import EtfCtaView, EtfCtaViews
from quant_cn.core.exceptions import LakeError
from quant_cn.portfolio.etf_cta_book import EtfCtaBook
from tests.support import MiniLake, SampleFactorLake

DAYS = [d.strftime("%Y%m%d") for d in pd.bdate_range("2026-07-01", "2026-10-30")]
A, B, C, OIL, BOND, CASH = (
    "510300.SH",
    "518880.SH",
    "159980.SZ",
    "161129.SZ",
    "511010.SH",
    "511880.SH",
)


def _build_settings(**kw: object) -> EtfCtaSettings:
    raw: dict[str, object] = {
        "groups": [
            {"name": "股票", "members": {A: 1}},
            {"name": "黄金", "members": {B: 1}},
            {"name": "商品", "members": {C: 1, OIL: 1}},
        ],
        "bonds": {BOND: 1},
        "cash": CASH,
        "trend_windows": [2],
        "switch_windows": [3],
        "vol_window": 5,
        "vol_min_obs": 3,
        "band": 0.0,
        "cost": 0.0,
        "history_start": "20260801",
        "paper_start": "20261001",
        "names": {A: "沪深300", OIL: "原油LOF", "501018.SH": "南方原油"},
        "premium": {"codes": [OIL], "alternative": {OIL: "501018.SH"}},
    }
    return EtfCtaSettings.model_validate(raw | kw)


def _write(lake: MiniLake, config: Config, premium: float = 0.0, jump: float = 0.0) -> None:
    rows, navs = [], []
    for code, size in ((A, 0.01), (B, 0.01), (C, 0.01), (OIL, 0.01), (BOND, 0.001), (CASH, 0.0)):
        px = 1.0
        for i, d in enumerate(DAYS):
            r = size * (1 if i % 2 == 0 else -1) + (0.0005 if size else 0.0001)
            if code == A and i >= len(DAYS) - 3:
                r += jump
            rows.append({"ts_code": code, "trade_date": d, "pre_close": px, "close": px * (1 + r)})
            px *= 1 + r
            if code == OIL:
                navs.append(
                    {"ts_code": OIL, "ann_date": d, "nav_date": d, "unit_nav": px / (1 + premium)}
                )
    SampleFactorLake.write(lake, config, "fund_daily", rows)
    SampleFactorLake.write(lake, config, "fund_nav", navs)


def test_tc_ecb_001_document(lake: MiniLake, config: Config) -> None:
    """TC-ECB-001"""
    _write(lake, config)
    doc = EtfCtaBook(_build_settings(), lake.query, DateCodec()).build(None)
    assert doc["as_of"] == "20261030" and doc["decision_date"] == "20261030"
    codes = [r["code"] for r in doc["weights"]]
    assert codes == [A, B, C, OIL, BOND, CASH]
    assert sum(r["target"] for r in doc["weights"]) == pytest.approx(1.0, abs=1e-3)
    groups = {g["name"]: g["target"] for g in doc["groups"]}
    assert groups["债券"] == pytest.approx(0.4) and set(groups) == {
        "股票",
        "黄金",
        "商品",
        "债券",
        "现金",
    }
    a = doc["weights"][0]
    assert a["name"] == "沪深300" and a["action"] in {"买入", "卖出", "不动"}
    assert a["held"] + a["trade"] == pytest.approx(a["target"], abs=1e-3)


def test_tc_ecb_002_premium_guard(lake: MiniLake, config: Config) -> None:
    """TC-ECB-002"""
    _write(lake, config, premium=0.25)
    doc = EtfCtaBook(_build_settings(paper_start="20261030"), lake.query, DateCodec()).build(None)
    oil = next(r for r in doc["weights"] if r["code"] == OIL)
    assert oil["target"] > 0 and oil["trade"] == pytest.approx(0.0)
    p = doc["premium"][0]
    assert p["state"] == "很高" and p["blocked"] and p["alternative"] == "501018.SH"
    assert any(f["kind"] == "premium" and "南方原油" in f["message"] for f in doc["flags"])


def test_tc_ecb_003_records(lake: MiniLake, config: Config) -> None:
    """TC-ECB-003"""
    _write(lake, config)
    doc = EtfCtaBook(_build_settings(), lake.query, DateCodec()).build(None)
    assert doc["backtest"]["start"] == "20260803" and doc["paper"]["start"] == "20261001"
    assert doc["paper"]["points"][0]["d"] <= "20261002"
    assert doc["backtest"]["max_dd"] <= 0 and doc["backtest"]["years"][0]["year"] == 2026


def test_tc_ecb_004_flags(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-ECB-004"""
    _write(lake, config, jump=-0.004)  # 沪深300 turns down in the last week
    book = EtfCtaBook(_build_settings(timed=[A], vol_target=5.0), lake.query, DateCodec())
    path = book.write(tmp_path)
    first = json.loads(path.read_text(encoding="utf-8"))
    assert any(f["key"].startswith("group:股票") for f in first["flags"])
    assert first["new_flags"] == [f["key"] for f in first["flags"]]
    second = json.loads(book.write(tmp_path).read_text(encoding="utf-8"))
    assert second["new_flags"] == []


def test_tc_ecb_005_errors(lake: MiniLake, tmp_path: Path) -> None:
    """TC-ECB-005"""
    book = EtfCtaBook(_build_settings(), lake.query, DateCodec())
    with pytest.raises(LakeError):
        book.write(tmp_path / "missing")
    with pytest.raises(LakeError):
        book.build(None)


def test_tc_ecb_006_views_track(lake: MiniLake, config: Config) -> None:
    """TC-ECB-006"""
    _write(lake, config)
    s = _build_settings()
    plain = EtfCtaBook(s, lake.query, DateCodec()).build(None)
    assert plain["views"]["weights"] == plain["weights"] and plain["views"]["items"] == []
    assert plain["views"]["paper"] == plain["paper"]
    view = EtfCtaView(
        kind="scale",
        target="黄金",
        multiplier=0.5,
        reason="r",
        start="20261001",
        expires="20261231",
    )
    doc = EtfCtaBook(s, lake.query, DateCodec(), views=EtfCtaViews(views=[view])).build(None)
    gold = {g["name"]: g for g in doc["views"]["groups"]}["黄金"]
    assert gold["views"] == pytest.approx(gold["system"] / 2, abs=1e-4) and gold["effect"] < 0
    assert doc["views"]["items"][0]["status"] == "生效"
    assert gold["system"] > 0 and doc["views"]["paper"]["nav"] != doc["paper"]["nav"]
    assert doc["weights"] == plain["weights"]  # the system track is untouched
