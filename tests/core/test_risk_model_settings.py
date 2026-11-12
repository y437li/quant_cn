"""Tests of RiskModelSettings and StyleSpec (plan 05, D-127)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from quant_cn.core.config import Config
from quant_cn.core.risk_model_settings import (
    ExternalSeriesSpec,
    RiskModelSettings,
    StyleSpec,
    ThemeBasketSpec,
)

REPO = Path(__file__).resolve().parents[2]


# TC-RMS-001
def test_tc_rms_001_yaml_loads_cne5_weights(repo: Path, tmp_path: Path) -> None:
    env = {"QUANT_CN_LAKE_ROOT": str(tmp_path / "lake")}
    assert Config.load(repo_root=repo, env=env).risk_model == RiskModelSettings()
    shutil.copy(REPO / "config" / "risk_model.yaml", repo / "config" / "risk_model.yaml")
    s = Config.load(repo_root=repo, env=env).risk_model
    assert s.style_names[:3] == ["size", "beta", "momentum"]
    styles = {x.name: x for x in s.styles}
    assert styles["residual_volatility"].descriptors == {
        "dastd": 0.74,
        "cmra": 0.16,
        "hsigma": 0.10,
    }
    assert styles["residual_volatility"].orthogonalize_to == ["size", "beta"]
    assert sum(styles["leverage"].descriptors.values()) == pytest.approx(1.0)
    assert (s.vol_half_life, s.corr_half_life, s.cov_nw_lags) == (90, 480, 2)
    assert RiskModelSettings().external_series == []


# TC-RMS-002
def test_tc_rms_002_bad_orthogonalisation_and_date_refused() -> None:
    size = StyleSpec(name="size", descriptors={"lncap": 1.0})
    later = StyleSpec(name="liquidity", descriptors={"stom": 1.0}, orthogonalize_to=["beta"])
    with pytest.raises(ValidationError):
        RiskModelSettings(styles=[size, later])
    with pytest.raises(ValidationError):
        RiskModelSettings(start="2019-01-02")
    with pytest.raises(ValidationError):
        StyleSpec(name="x", descriptors={"a": 0.0})
    with pytest.raises(ValidationError):
        RiskModelSettings(specific_min_obs=50, specific_full_obs=50)
    with pytest.raises(ValidationError):
        RiskModelSettings(styles=[size], monitor_styles=[size])
    ok = RiskModelSettings(
        styles=[size],
        monitor_styles=[StyleSpec(name="m", descriptors={"a": 1.0}, orthogonalize_to=["size"])],
    )
    assert ok.monitor_styles[0].name == "m"


# TC-RMS-003
def test_tc_rms_003_external_series_and_themes() -> None:
    s = RiskModelSettings(
        external_series=[
            {
                "descriptor": "usd_beta",
                "dataset": "fx_daily",
                "code": "USDCNH.FXCM",
                "column": "bid_close",
                "kind": "price",
                "date_shift_days": 1,
            }
        ],
        theme_baskets=[{"descriptor": "aidc_beta", "concept": "885887.TI", "start": "20200306"}],
    )
    assert s.external_series[0] == ExternalSeriesSpec(
        descriptor="usd_beta",
        dataset="fx_daily",
        code="USDCNH.FXCM",
        column="bid_close",
        kind="price",
        date_shift_days=1,
    )
    assert s.theme_baskets[0].start == "20200306"
    with pytest.raises(ValidationError):
        ExternalSeriesSpec(descriptor="x", dataset="d", code="c", kind="level")
    with pytest.raises(ValidationError):
        ExternalSeriesSpec(descriptor="x", dataset="d", code="c", date_shift_days=-1)
    with pytest.raises(ValidationError):
        ThemeBasketSpec(descriptor="x", concept="c", start="2020-03-06")
