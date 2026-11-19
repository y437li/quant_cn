"""Contract tests for core.EtfCtaViews (plan 27 ph5, D-163)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.etf_cta_settings import EtfCtaSettings
from quant_cn.core.etf_cta_views import EtfCtaView, EtfCtaViews
from quant_cn.core.exceptions import ConfigError

REPO = Path(__file__).resolve().parents[2]
OK = {"reason": "实际利率还在涨", "start": "20261116", "expires": "20270215"}


def _write(tmp: Path, text: str) -> EtfCtaSettings:
    (tmp / "config").mkdir(exist_ok=True)
    (tmp / "config" / "local.etf_cta_views.yaml").write_text(text, encoding="utf-8")
    return EtfCtaSettings.load(REPO)


def test_tc_ecv_001_load(tmp_path: Path) -> None:
    """TC-ECV-001"""
    s = EtfCtaSettings.load(REPO)
    assert EtfCtaViews.load(tmp_path, s).views == []
    assert EtfCtaViews.load(tmp_path, s.model_copy(update={"views_file": None})).views == []
    _write(
        tmp_path,
        "views:\n"
        "  - {kind: scale, target: 黄金, multiplier: 0.7, reason: r, start: '20261116',"
        " expires: '20270215'}\n"
        "  - {kind: relative, over: 港股, under: A股, points: 0.03, reason: r,"
        " start: '20261116', expires: '20261231', when: {code: 513130.SH, below: 0.7}}\n"
        "a_share_floor: 0.3\n",
    )
    v = EtfCtaViews.load(tmp_path, s)
    assert [x.kind for x in v.views] == ["scale", "relative"] and v.a_share_floor == 0.3
    assert v.views[1].list_names() == ["港股", "A股", "513130.SH"]


@pytest.mark.parametrize(
    "raw",
    [
        {**OK, "kind": "scale", "target": "黄金", "multiplier": 2.5},
        {**OK, "kind": "scale", "target": "黄金"},
        {**OK, "kind": "relative", "over": "黄金", "under": "黄金", "points": 0.02},
        {**OK, "kind": "relative", "over": "黄金", "under": "商品", "points": 0.08},
        {**OK, "kind": "scale", "target": "黄金", "multiplier": 1.2, "expires": "20270301"},
        {**OK, "kind": "scale", "target": "黄金", "multiplier": 1.2, "reason": ""},
        {
            **OK,
            "kind": "scale",
            "target": "黄金",
            "multiplier": 1.2,
            "when": {"code": "518880.SH", "below": 9, "above": 11},
        },
    ],
)
def test_tc_ecv_002_bad_views(raw: dict[str, object]) -> None:
    """TC-ECV-002"""
    with pytest.raises(ValidationError):
        EtfCtaView.model_validate(raw)


@pytest.mark.parametrize(
    "text",
    [
        "views:\n  - {kind: scale, target: 美股, multiplier: 1.2, reason: r, start: '20261116',"
        " expires: '20261231'}\n",
        "views:\n  - {kind: scale, target: 黄金, multiplier: 1.2, reason: r, start: '20261116',"
        " expires: '20261231', when: {code: 600000.SH, below: 9}}\n",
        "views: [\n",
    ],
)
def test_tc_ecv_003_bad_file(tmp_path: Path, text: str) -> None:
    """TC-ECV-003"""
    s = _write(tmp_path, text)
    with pytest.raises(ConfigError):
        EtfCtaViews.load(tmp_path, s)
