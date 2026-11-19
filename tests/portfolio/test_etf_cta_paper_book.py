"""Contract tests for portfolio.EtfCtaPaperBook (plan 27)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.portfolio.etf_cta_paper_book import EtfCtaPaperBook

IDX = pd.bdate_range("2026-03-02", periods=6)  # Mon..Mon
A, B = "510300.SH", "518880.SH"


def _build_flat(**kw: float) -> pd.DataFrame:
    return pd.DataFrame({A: kw.get("a", 0.0), B: kw.get("b", 0.0)}, index=IDX)


def _build_targets(*rows: tuple[str, float, float]) -> pd.DataFrame:
    return pd.DataFrame(
        {A: [r[1] for r in rows], B: [r[2] for r in rows]},
        index=pd.DatetimeIndex([r[0] for r in rows]),
    )


CASH = pd.Series(0.0, index=IDX)


def test_tc_ecp_001_band() -> None:
    """TC-ECP-001"""
    t = _build_targets(
        ("2026-03-02", 0.5, 0.0), ("2026-03-04", 0.51, 0.0), ("2026-03-06", 0.53, 0.0)
    )
    out = EtfCtaPaperBook(0.02, 0.0).run(_build_flat(), CASH, t, IDX[0])
    assert out["weights"].loc["2026-03-04", A] == pytest.approx(0.5)
    assert out["weights"].loc["2026-03-06", A] == pytest.approx(0.53)


def test_tc_ecp_002_zero_target_sells() -> None:
    """TC-ECP-002"""
    t = _build_targets(("2026-03-02", 0.01, 0.0), ("2026-03-04", 0.0, 0.0))
    out = EtfCtaPaperBook(0.02, 0.0).run(_build_flat(), CASH, t, IDX[0])
    assert out["weights"].loc["2026-03-02", A] == pytest.approx(0.0)  # 1% < band: never bought
    t = _build_targets(("2026-03-02", 0.05, 0.0), ("2026-03-04", 0.0, 0.0))
    out = EtfCtaPaperBook(0.10, 0.0).run(_build_flat(), CASH, t, IDX[0])
    assert out["weights"].loc["2026-03-04", A] == pytest.approx(0.0)


def test_tc_ecp_003_costs() -> None:
    """TC-ECP-003"""
    t = _build_targets(("2026-03-02", 0.5, 0.5))
    out = EtfCtaPaperBook(0.0, 0.001).run(_build_flat(), CASH, t, IDX[0])
    assert out["nav"].iloc[-1] == pytest.approx(1.0 - 0.001)


def test_tc_ecp_004_drift_and_cash() -> None:
    """TC-ECP-004"""
    t = _build_targets(("2026-03-02", 0.5, 0.0))
    cash = pd.Series(0.001, index=IDX)
    out = EtfCtaPaperBook(0.0, 0.0).run(_build_flat(a=0.01), cash, t, IDX[0])
    a, m = 0.5 * 1.001 * 1.01**5, 0.5 * 1.001**6  # day 0: cash return, then the trade
    assert out["nav"].iloc[-1] == pytest.approx(a + m)
    assert out["weights"].iloc[-1][A] == pytest.approx(a / (a + m))


@pytest.mark.parametrize(("band", "cost"), [(-0.1, 0.0), (0.0, -0.1)])
def test_tc_ecp_005_bad_inputs(band: float, cost: float) -> None:
    """TC-ECP-005"""
    with pytest.raises(ValueError):
        EtfCtaPaperBook(band, cost)
    with pytest.raises(ValueError):
        EtfCtaPaperBook(0.0, 0.0).run(
            _build_flat(), CASH, _build_targets(("2026-03-02", 0, 0)), pd.Timestamp("2027-01-01")
        )


def test_tc_ecp_006_no_add() -> None:
    """TC-ECP-006"""
    t = _build_targets(("2026-03-02", 0.3, 0.3), ("2026-03-04", 0.5, 0.1))
    day = pd.Timestamp("2026-03-04")
    out = EtfCtaPaperBook(0.0, 0.0).run(_build_flat(), CASH, t, IDX[0], {day: [A, B]})
    assert out["weights"].loc[day, A] == pytest.approx(0.3) and out["weights"].loc[
        day, B
    ] == pytest.approx(0.1)


def test_tc_ecp_007_group_band() -> None:
    """TC-ECP-007"""
    t = _build_targets(("2026-03-02", 0.012, 0.012))
    out = EtfCtaPaperBook(0.02, 0.0, {A: "股票", B: "股票"}).run(_build_flat(), CASH, t, IDX[0])
    assert out["weights"].loc["2026-03-02", [A, B]].to_numpy() == pytest.approx([0.012, 0.012])
