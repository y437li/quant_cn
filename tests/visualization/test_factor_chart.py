from __future__ import annotations

import math
from typing import cast

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.exceptions import SchemaError
from quant_cn.core.frames import IC_SERIES, IC_TEST, QUANTILE_RETURNS
from quant_cn.visualization.chart_theme import ChartTheme
from quant_cn.visualization.factor_chart import FactorChart, Kind

THEME = ChartTheme.from_mode("light")


def build_ic_series() -> pd.DataFrame:
    days = pd.bdate_range("2024-01-01", periods=40).strftime("%Y%m%d")
    ic = np.random.default_rng(0).normal(0.05, 0.1, len(days))
    return IC_SERIES.normalize(
        pd.DataFrame({"trade_date": days, "factor": "f", "horizon": 5.0, "ic": ic, "n": 100.0}),
        strict=True,
    )


def build_ic_test(half_life: float = math.nan) -> pd.DataFrame:
    base = {c: None for c in IC_TEST.columns} | {"window": "full"}
    rows = [
        base
        | {
            "factor": f,
            "horizon": 5.0,
            "metric": "icir",
            "value": v,
            "ci_lo": v - 0.1,
            "ci_hi": v + 0.2,
        }
        for f, v in (("a", 0.2), ("b", 0.5), ("f", 0.3))
    ]
    rows += [
        base
        | {
            "factor": "f",
            "horizon": float(h),
            "metric": "ic_mean",
            "value": v,
            "ci_lo": v - 0.01,
            "ci_hi": v + 0.01,
        }
        for h, v in ((20, 0.04), (1, 0.01), (5, 0.02))
    ]
    rows += [
        base | {"factor": "f", "horizon": 0.0, "metric": m, "value": v}
        for m, v in (("peak_horizon", 20.0), ("half_life", half_life))
    ]
    return IC_TEST.normalize(pd.DataFrame(rows), strict=True)


def build_quantiles() -> pd.DataFrame:
    rows = [
        {"trade_date": d, "factor": "f", "horizon": 5.0, "quantile": q, "ret": r, "n": 10.0}
        for d in ("20240102", "20240103")
        for q, r in ((0, 0.02), (1, -0.01), (2, 0.0), (3, 0.01))
    ]
    return QUANTILE_RETURNS.normalize(pd.DataFrame(rows), strict=True)


# TC-FC-001
def test_tc_fc_001_ic_series() -> None:
    frame = build_ic_series()
    fig = FactorChart(THEME, "ic_series", "f", horizon=5, window=10).render(frame)
    upper, lower, mean = fig.data
    ic = frame["ic"].to_numpy(float)
    assert mean.y[9] == pytest.approx(ic[:10].mean()) and math.isnan(mean.y[8])
    half = 1.96 * ic[:10].std(ddof=1) / math.sqrt(10 / 5)
    assert upper.y[9] - mean.y[9] == pytest.approx(half)
    assert lower.fill == "tonexty" and mean.x[0] == "2024-01-01"


# TC-FC-002
def test_tc_fc_002_icir_and_quantiles() -> None:
    bars = FactorChart(THEME, "icir", horizon=5).render(build_ic_test()).data[0]
    assert list(bars.x) == ["b", "f", "a"]
    assert list(bars.error_y.array) == pytest.approx([0.2, 0.2, 0.2])
    fig = FactorChart(THEME, "quantiles", "f", horizon=5).render(build_quantiles())
    assert list(fig.data[0].x) == ["Q1", "Q2", "Q3"]
    assert list(fig.data[0].y) == pytest.approx([-1.0, 0.0, 1.0])
    assert "long-short 2.00%" in fig.layout.title.text


# TC-FC-003
def test_tc_fc_003_horizon() -> None:
    fig = FactorChart(THEME, "horizon", "f").render(build_ic_test())
    assert list(fig.data[0].x) == ["1", "5", "20"]
    assert list(fig.data[0].error_y.arrayminus) == pytest.approx([0.01] * 3)
    assert "peak 20, rising" in fig.layout.title.text
    decaying = FactorChart(THEME, "horizon", "f").render(build_ic_test(12.0))
    assert "half-life 12 sessions" in decaying.layout.title.text


# TC-FC-004
def test_tc_fc_004_errors() -> None:
    with pytest.raises(ValueError):
        FactorChart(THEME, cast(Kind, "pie"), "f")
    with pytest.raises(ValueError):
        FactorChart(THEME, "horizon")
    with pytest.raises(ValueError):
        FactorChart(THEME, "ic_series", "zz", horizon=5).build_figure(build_ic_series())
    with pytest.raises(SchemaError):
        FactorChart(THEME, "quantiles", "f").build_figure(build_ic_series())
