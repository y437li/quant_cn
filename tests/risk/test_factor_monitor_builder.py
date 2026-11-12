"""Contract tests for risk.FactorMonitorBuilder (plan 15 phase 7c, D-132)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.risk.factor_monitor_builder import FactorMonitorBuilder
from tests.support import MiniLake

DAYS = [d.strftime("%Y%m%d") for d in pd.bdate_range("2025-10-01", periods=80)]
FACTORS = ["size", "country", "ind_801010.SI"]
MISSING = {DAYS[-5], DAYS[-30]}  # size has no return on these sessions
RNG = np.random.default_rng(7)
RET = {f: RNG.normal(0, 0.01, len(DAYS)) for f in FACTORS}
VAR = {"country": 1e-4, "size": 4e-5, "ind_801010.SI": 9e-5}


def _write(lake: MiniLake, config: Config) -> None:
    rows = [
        {"trade_date": d, "factor": f, "ret": RET[f][t], "t_stat": 1.0, "r2": 0.3, "n_obs": 100}
        for f in FACTORS
        for t, d in enumerate(DAYS)
        if not (f == "size" and d in MISSING)
    ]
    cov = [
        {
            "trade_date": d,
            "factor_i": fi,
            "factor_j": fj,
            "cov": VAR[fi] * (1 + t / 100) if fi == fj else 1e-6,
            "cov_raw": 0.0,
            "horizon_days": 21,
        }
        for t, d in enumerate(DAYS)
        for fi in FACTORS
        for fj in FACTORS
    ]
    for name, frame in (("risk_factor_return", rows), ("risk_factor_cov", cov)):
        lake.writer.write_derived(name, 2025, pd.DataFrame(frame))
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh_tables()


@pytest.fixture
def doc(lake: MiniLake, config: Config) -> dict[str, Any]:
    _write(lake, config)
    return FactorMonitorBuilder(lake.query, "m1", series_days=30).build()


def _get(doc: dict[str, Any], factor: str) -> dict[str, Any]:
    return next(f for f in doc["factors"] if f["factor"] == factor)


def _build_series(factor: str) -> pd.Series:
    s = pd.Series(RET[factor], index=DAYS)
    return s.drop(sorted(MISSING)) if factor == "size" else s


# TC-FMB-001
def test_tc_fmb_001_window_returns(doc: dict[str, Any]) -> None:
    country = _get(doc, "country")["ret"]
    r = RET["country"]
    assert country["d1"] == pytest.approx(r[-1], abs=1e-6)
    assert country["w1"] == pytest.approx(np.prod(1 + r[-5:]) - 1, abs=1e-6)
    assert country["m3"] == pytest.approx(np.prod(1 + r[-63:]) - 1, abs=1e-6)
    ytd = [x for d, x in zip(DAYS, r, strict=True) if d >= "20260101"]
    assert country["ytd"] == pytest.approx(np.prod(1 + np.array(ytd)) - 1, abs=1e-6)
    assert country["y1"] == pytest.approx(np.prod(1 + r) - 1, abs=1e-6)  # fewer than 252 rows
    size_w1 = _build_series("size")[DAYS[-5] :]
    assert _get(doc, "size")["ret"]["w1"] == pytest.approx(np.prod(1 + size_w1) - 1, abs=1e-6)
    assert doc["as_of"] == DAYS[-1]
    assert doc["model"] == "m1"
    assert doc["n_sessions"] == len(DAYS)


# TC-FMB-002
def test_tc_fmb_002_volatility(doc: dict[str, Any]) -> None:
    c = _get(doc, "country")
    t = len(DAYS) - 1
    assert c["forecast_vol"] == pytest.approx(math.sqrt(1e-4 * (1 + t / 100) * 252), abs=1e-6)
    prev_sd = math.sqrt(1e-4 * (1 + (t - 1) / 100))
    assert c["sigma_move"] == pytest.approx(RET["country"][-1] / prev_sd, abs=1e-5)
    r21 = float(np.std(RET["country"][-21:], ddof=1) * math.sqrt(252))
    r63 = float(np.std(RET["country"][-63:], ddof=1) * math.sqrt(252))
    assert c["realized_vol_21"] == pytest.approx(r21, abs=1e-6)
    assert c["realized_vol_63"] == pytest.approx(r63, abs=1e-6)
    assert c["vol_ratio"] == pytest.approx(r21 / c["forecast_vol"], abs=1e-5)
    assert c["realized"][0] is not None
    assert c["forecast"][-1] == pytest.approx(c["forecast_vol"], abs=1e-6)


# TC-FMB-003
def test_tc_fmb_003_missing_days_series_kinds(doc: dict[str, Any]) -> None:
    assert doc["dates"] == DAYS[-30:]
    size = _get(doc, "size")
    assert len(size["cum"]) == len(size["forecast"]) == len(size["realized"]) == 30
    assert size["cum"][DAYS[-30:].index(DAYS[-5])] is None
    rows = _build_series("size")
    sd21 = float(rows.iloc[-21:].std(ddof=1) * math.sqrt(252))  # 21 rows, not 21 sessions
    assert size["realized_vol_21"] == pytest.approx(sd21, abs=1e-6)
    shown = rows[rows.index >= DAYS[-30]]
    assert size["cum"][-1] == pytest.approx(np.prod(1 + shown) - 1, abs=1e-6)
    assert [f["factor"] for f in doc["factors"]] == ["country", "size", "ind_801010.SI"]
    assert [f["kind"] for f in doc["factors"]] == ["country", "style", "industry"]
    assert _get(doc, "ind_801010.SI")["label"] == "ind_801010.SI"  # no industry_l1 view


# TC-FMB-004
def test_tc_fmb_004_errors_and_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        FactorMonitorBuilder(lake.query, "m", series_days=0)
    builder = FactorMonitorBuilder(lake.query, "m", series_days=10)
    with pytest.raises(LakeError):
        builder.build()
    _write(lake, config)
    with pytest.raises(LakeError):
        builder.write(tmp_path / "absent")
    path = builder.write(tmp_path)
    assert path == tmp_path / "factor_monitor.json"
    assert len(json.loads(path.read_text(encoding="utf-8"))["dates"]) == 10
