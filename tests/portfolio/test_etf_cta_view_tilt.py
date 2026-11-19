"""Contract tests for portfolio.EtfCtaViewTilt (plan 27 ph5, D-163)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_cta_settings import EtfCtaSettings
from quant_cn.core.etf_cta_views import EtfCtaView, EtfCtaViews
from quant_cn.portfolio.etf_cta_view_tilt import EtfCtaViewTilt

A, H, G, C, B5, B30 = "510300.SH", "159920.SZ", "518880.SH", "159980.SZ", "511010.SH", "511090.SH"
DAYS = pd.DatetimeIndex(["2026-11-06", "2026-11-13", "2026-11-20"])
ROW = {A: 0.1, H: 0.1, G: 0.15, C: 0.15, B5: 0.15, B30: 0.15}


def _build_tilt() -> EtfCtaViewTilt:
    s = EtfCtaSettings.model_validate(
        {
            "groups": [
                {"name": "股票", "members": {A: 1, H: 1}},
                {"name": "黄金", "members": {G: 1}},
                {"name": "商品", "members": {C: 1}},
            ],
            "bonds": {B5: 1, B30: 1},
            "cash": "511880.SH",
            "timed": [A],
            "subsets": {"A股": [A], "港股": [H]},
            "history_start": "20260101",
            "paper_start": "20261101",
        }
    )
    return EtfCtaViewTilt(s, DateCodec())


def _build_targets(**over: float) -> pd.DataFrame:
    return pd.DataFrame([ROW | over] * len(DAYS), index=DAYS)


def _build_view(**kw: object) -> EtfCtaView:
    base: dict[str, object] = {"reason": "x", "start": "20261101", "expires": "20261231"}
    return EtfCtaView.model_validate(base | kw)


def _build_closes(gold: list[float] | None = None) -> pd.DataFrame:
    return pd.DataFrame({G: gold or [10.0] * len(DAYS)}, index=DAYS)


def _build_applied(views: list[EtfCtaView], targets: pd.DataFrame | None = None) -> pd.DataFrame:
    t = _build_targets() if targets is None else targets
    return _build_tilt().compute_targets(t, EtfCtaViews(views=views), _build_closes())


def test_tc_ecvt_001_no_live_views() -> None:
    """TC-ECVT-001"""
    pd.testing.assert_frame_equal(_build_applied([]), _build_targets())
    late = _build_view(kind="scale", target="黄金", multiplier=2, start="20261121")
    pd.testing.assert_frame_equal(_build_applied([late]), _build_targets())


def test_tc_ecvt_002_group_and_subset_scale() -> None:
    """TC-ECVT-002"""
    w = _build_applied([_build_view(kind="scale", target="黄金", multiplier=1.5)]).iloc[-1]
    assert w[G] == pytest.approx(0.225) and w[C] == pytest.approx(0.15)
    w = _build_applied([_build_view(kind="scale", target="港股", multiplier=2)]).iloc[-1]
    assert w[A] + w[H] == pytest.approx(0.2) and w[H] == pytest.approx(2 * w[A])


def test_tc_ecvt_003_clip_and_cap() -> None:
    """TC-ECVT-003"""
    views = [
        _build_view(kind="scale", target="港股", multiplier=2),
        _build_view(kind="scale", target="股票", multiplier=2),
    ]
    assert _build_applied(views).iloc[-1][H] == pytest.approx(0.2)  # 2.67x clipped to 2x
    big = [_build_view(kind="scale", target=n, multiplier=2) for n in ("黄金", "商品", "债券")]
    w = _build_applied(big).iloc[-1]
    assert w.sum() == pytest.approx(1.0) and w[G] == pytest.approx(0.3 / 1.4)


def test_tc_ecvt_004_relative() -> None:
    """TC-ECVT-004"""
    w = _build_applied([_build_view(kind="relative", over="黄金", under="商品", points=0.05)]).iloc[
        -1
    ]
    assert w[G] == pytest.approx(0.2) and w[C] == pytest.approx(0.1)
    small = _build_targets(**{H: 0.02})
    w = _build_applied(
        [_build_view(kind="relative", over="黄金", under="港股", points=0.05)], small
    )
    assert w.iloc[-1][H] == pytest.approx(0.0) and w.iloc[-1][G] == pytest.approx(0.17)
    off = _build_targets(**{A: 0.0})
    w = _build_applied([_build_view(kind="relative", over="A股", under="黄金", points=0.05)], off)
    pd.testing.assert_frame_equal(w, off)


def test_tc_ecvt_005_condition_latches() -> None:
    """TC-ECVT-005"""
    view = _build_view(kind="scale", target="黄金", multiplier=2, when={"code": G, "below": 9.5})
    t = _build_tilt().compute_targets(
        _build_targets(), EtfCtaViews(views=[view]), _build_closes([10.0, 9.0, 10.0])
    )
    assert list(t[G].round(4)) == [0.15, 0.3, 0.3]


def test_tc_ecvt_006_floor() -> None:
    """TC-ECVT-006"""
    full = _build_targets()
    for held, want in ((0.0, 0.03), (0.05, 0.05)):
        t = _build_tilt().compute_targets(
            _build_targets(**{A: held}), EtfCtaViews(a_share_floor=0.3), _build_closes(), full
        )
        assert t.iloc[-1][A] == pytest.approx(want) and t.iloc[-1][H] == pytest.approx(0.1)


def test_tc_ecvt_007_summary() -> None:
    """TC-ECVT-007"""
    views = EtfCtaViews(
        views=[
            _build_view(kind="scale", target="黄金", multiplier=0.5, expires="20261110"),
            _build_view(kind="scale", target="商品", multiplier=2, when={"code": G, "below": 9.5}),
            _build_view(kind="scale", target="债券", multiplier=2, start="20261201"),
        ]
    )
    tilt, closes = _build_tilt(), _build_closes([10.0, 10.0, 9.0])
    system = _build_targets()
    d = tilt.build_summary(system, tilt.compute_targets(system, views, closes), views, closes)
    assert [i["status"] for i in d["items"]] == ["已过期", "生效", "未开始"]
    assert [f["key"] for f in d["flags"]] == ["view:expired:0:20261110", "view:on:1:20261101"]
    effect = {g["name"]: g["effect"] for g in d["groups"]}
    assert effect["商品"] == pytest.approx(0.15) and effect["现金"] == pytest.approx(-0.15)
