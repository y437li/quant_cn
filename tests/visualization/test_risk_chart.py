"""Tests of RiskChart."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import FACTOR_COV, FACTOR_RETURN
from quant_cn.risk.risk_decomposer import RiskDecomposer
from quant_cn.risk.risk_snapshot import RiskSnapshot
from quant_cn.visualization.chart_theme import ChartTheme
from quant_cn.visualization.risk_chart import ANNUAL, RiskChart

THEME = ChartTheme.from_mode("light")
DAYS = pd.bdate_range("2024-01-01", periods=30).strftime("%Y%m%d").tolist()


def build_returns() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = [
        {
            "trade_date": d,
            "factor": f,
            "ret": rng.normal(0, 0.01),
            "t_stat": 0.0,
            "r2": 0.3,
            "n_obs": 1.0,
        }
        for d in DAYS
        for f in ("size", "beta", "ind_801010.SI")
    ]
    return FACTOR_RETURN.normalize(pd.DataFrame(rows), strict=True)


def build_cov() -> pd.DataFrame:
    names = ["beta", "size"]
    m = np.array([[4e-4, 1e-4], [1e-4, 1e-4]])
    rows = [
        {
            "trade_date": DAYS[-1],
            "factor_i": a,
            "factor_j": b,
            "cov": m[i, j],
            "cov_raw": m[i, j],
            "horizon_days": 21.0,
        }
        for i, a in enumerate(names)
        for j, b in enumerate(names)
    ]
    return FACTOR_COV.normalize(pd.DataFrame(rows), strict=True)


# TC-RC-001
def test_tc_rc_001_cumulative() -> None:
    frame = build_returns()
    fig = RiskChart(THEME, "cumulative").build_figure(frame)
    assert [t.name for t in fig.data] == ["beta", "size"]  # industries left out by default
    size = frame[frame["factor"] == "size"].sort_values("trade_date")["ret"]
    assert fig.data[1].y[-1] == pytest.approx(np.prod(1 + size) - 1)
    assert fig.data[0].x[0] == "2024-01-01"


# TC-RC-002
def test_tc_rc_002_correlation() -> None:
    z = np.array(RiskChart(THEME, "correlation").build_figure(build_cov()).data[0].z)
    np.testing.assert_allclose(np.diag(z), 1.0)
    np.testing.assert_allclose(z, z.T)
    assert z[0, 1] == pytest.approx(1e-4 / (0.02 * 0.01))


# TC-RC-003
def test_tc_rc_003_decomposition_and_errors() -> None:
    x = pd.DataFrame([[1.0, 1.0], [1.0, -1.0]], index=["A", "B"], columns=["country", "size"])
    cov = pd.DataFrame([[4e-4, 0.0], [0.0, 1e-4]], index=x.columns, columns=x.columns)
    snap = RiskSnapshot("20240101", x, cov, pd.Series([0.02, 0.03], index=["A", "B"]))
    decomp = RiskDecomposer().compute(snap, pd.Series({"A": 0.7, "B": 0.3}), "p")
    fig = RiskChart(THEME, "decomposition").build_figure(decomp)
    bars = dict(zip(fig.data[0].y, fig.data[0].x, strict=True))
    assert set(bars) == {"country", "size", "specific"}
    total = decomp.set_index("component").loc["total", "risk"]
    assert sum(bars.values()) == pytest.approx(total * ANNUAL)
    assert "annualised vol" in fig.layout.title.text
    with pytest.raises(ValueError):
        RiskChart(THEME, "bogus")  # type: ignore[arg-type]  # TC-RC-003: refused kind
    with pytest.raises(ValueError):
        RiskChart(THEME, "cumulative", factors=["nope"]).build_figure(build_returns())
