"""Contract tests for core.EtfCtaSettings (plan 27, D-160)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.etf_cta_settings import EtfCtaPremium, EtfCtaSettings
from quant_cn.core.exceptions import ConfigError

REPO = Path(__file__).resolve().parents[2]
BASE = {"cash": "511880.SH", "history_start": "20200401", "paper_start": "20261113"}


def test_tc_ecs_001_loads_committed_file(tmp_path: Path) -> None:
    """TC-ECS-001"""
    s = EtfCtaSettings.load(REPO)
    assert [g.name for g in s.groups] == ["股票", "黄金", "商品"]
    assert s.risk_share == pytest.approx(0.6) and s.bond_share == pytest.approx(0.4)
    assert set(s.bonds) == {"511010.SH", "511090.SH"} and s.list_codes()[-1] == "511880.SH"
    assert "161129.SZ" in s.premium.codes and s.band == pytest.approx(0.02)
    with pytest.raises(ConfigError):
        EtfCtaSettings.load(tmp_path)


def test_tc_ecs_002_premium_order() -> None:
    """TC-ECS-002"""
    with pytest.raises(ValidationError):
        EtfCtaPremium(buy_below=0.1, high=0.05)


@pytest.mark.parametrize(
    "raw",
    [
        {**BASE, "risk_share": 0.7, "bond_share": 0.4},
        {
            **BASE,
            "groups": [
                {"name": "a", "members": {"510300.SH": 1}},
                {"name": "b", "members": {"510300.SH": 1}},
            ],
        },
        {**BASE, "groups": [{"name": "a", "members": {"510300.SH": 1}}], "timed": ["510500.SH"]},
    ],
)
def test_tc_ecs_003_bad_books(raw: dict[str, object]) -> None:
    """TC-ECS-003"""
    with pytest.raises(ValidationError):
        EtfCtaSettings.model_validate(raw)


def test_tc_ecs_004_list_members() -> None:
    """TC-ECS-004"""
    s = EtfCtaSettings.load(REPO)
    assert s.list_members("黄金") == ["518880.SH"]
    assert s.list_members("债券") == ["511010.SH", "511090.SH"]
    assert s.list_members("港股") == ["159920.SZ", "513050.SH", "513130.SH"]
    assert s.list_members("161129.SZ") == ["161129.SZ"]
    for bad in ("美股", "511880.SH"):
        with pytest.raises(ConfigError):
            s.list_members(bad)
    with pytest.raises(ValidationError):
        EtfCtaSettings.model_validate({**BASE, "subsets": {"x": ["600000.SH"]}})
