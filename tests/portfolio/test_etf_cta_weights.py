"""Contract tests for portfolio.EtfCtaWeights (plan 27)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.etf_cta_settings import EtfCtaSettings
from quant_cn.portfolio.etf_cta_weights import EtfCtaWeights

IDX = pd.bdate_range("2026-01-01", "2026-03-31")
A, B, C, BOND = "510300.SH", "518880.SH", "159980.SZ", "511010.SH"


def _build_settings(**kw: object) -> EtfCtaSettings:
    raw: dict[str, object] = {
        "groups": [
            {"name": "股票", "members": {A: 1}},
            {"name": "黄金", "members": {B: 1}},
            {"name": "商品", "members": {C: 1}},
        ],
        "bonds": {BOND: 1},
        "cash": "511880.SH",
        "history_start": "20260101",
        "paper_start": "20260301",
        "risk_share": 0.6,
        "bond_share": 0.4,
        "timed": [],
        "trend_windows": [2],
        "switch_windows": [3],
        "vol_window": 5,
        "vol_min_obs": 3,
    }
    return EtfCtaSettings.model_validate(raw | kw)


def _build_alternating(size: float, drift: float = 0.0) -> np.ndarray:
    return size * np.where(np.arange(len(IDX)) % 2 == 0, 1.0, -1.0) + drift


def _build_returns(**over: np.ndarray) -> pd.DataFrame:
    base = {
        A: _build_alternating(0.01),
        B: _build_alternating(0.01),
        C: _build_alternating(0.01),
        BOND: np.full(len(IDX), 0.0002),
    }
    return pd.DataFrame(base | over, index=IDX)


def test_tc_ecw_001_equal_and_double_vol() -> None:
    """TC-ECW-001"""
    t = EtfCtaWeights(_build_settings()).compute_targets(_build_returns())
    assert t.iloc[-1][[A, B, C]].to_numpy() == pytest.approx([0.2, 0.2, 0.2])
    t = EtfCtaWeights(_build_settings()).compute_targets(
        _build_returns(**{A: _build_alternating(0.02)})
    )
    w = t.iloc[-1]
    assert w[A] == pytest.approx(w[B] / 2) and w[[A, B, C]].sum() == pytest.approx(0.6)
    assert w[BOND] == pytest.approx(0.4)


def test_tc_ecw_002_monthly_hold() -> None:
    """TC-ECW-002"""
    r = _build_returns(**{A: np.r_[_build_alternating(0.01)[:30], _build_alternating(0.03)[30:]]})
    t = EtfCtaWeights(_build_settings()).compute_targets(r)
    feb = t.loc["2026-02-06":"2026-02-27", A]
    assert feb.nunique() == 1  # vol jumped mid-February, weight waits for March
    assert t.loc["2026-03-06", A] < feb.iloc[0]


def test_tc_ecw_003_timed_position() -> None:
    """TC-ECW-003"""
    up = _build_returns(**{A: _build_alternating(0.01, 0.004)})
    s = _build_settings(timed=[A], vol_target=1.0)
    t = EtfCtaWeights(s).compute_targets(up)
    plain = EtfCtaWeights(_build_settings()).compute_targets(up)
    assert t.iloc[-1][A] == pytest.approx(plain.iloc[-1][A])  # up on the 2-session window, size 1
    down = EtfCtaWeights(s).compute_targets(_build_returns(**{A: _build_alternating(0.01, -0.004)}))
    assert down.iloc[-1][A] == pytest.approx(0.0)
    first = up.copy()
    first.loc[: IDX[1], A] = np.nan
    early = EtfCtaWeights(s).compute_targets(first)
    assert early.iloc[0][A] == pytest.approx(0.0)


def test_tc_ecw_004_bond_switch() -> None:
    """TC-ECW-004"""
    falling = _build_returns(**{BOND: np.full(len(IDX), -0.001)})
    t = EtfCtaWeights(_build_settings()).compute_targets(falling)
    assert t.iloc[-1][BOND] == pytest.approx(0.0)
    assert t.iloc[0][BOND] == pytest.approx(0.4)  # unknown at the start: kept on


def test_tc_ecw_005_decisions_and_unlisted() -> None:
    """TC-ECW-005"""
    d = EtfCtaWeights.list_decisions(IDX)
    assert list(d[:2]) == [pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-09")]
    assert d[-1] == pd.Timestamp("2026-03-31") and len(d) == len(set(IDX.to_period("W")))
    r = _build_returns()
    r[C] = np.nan
    t = EtfCtaWeights(_build_settings()).compute_targets(r)
    assert (t[C] == 0).all() and t.iloc[-1][[A, B]].sum() == pytest.approx(0.6)


def test_tc_ecw_006_describe() -> None:
    """TC-ECW-006"""
    d = EtfCtaWeights(_build_settings(timed=[A])).build_summary(_build_returns())
    assert [g["name"] for g in d["groups"]] == ["股票", "黄金", "商品"]
    assert d["groups"][0]["risk_weight"] == pytest.approx(1 / 3, abs=1e-4)
    assert d["timed"][0]["code"] == A and d["bond_switch"]["blend"] == 1.0
