"""Tests of risk_validation_writer (plan 05)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import RISK_VALIDATION
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.service_builder import ServiceBuilder
from tests.risk.sample_risk_lake import SampleRiskLake
from tests.support import MiniLake

TABLES = [
    "risk_exposure",
    "risk_factor_return",
    "risk_specific_return",
    "risk_factor_cov",
    "risk_specific_risk",
]


def build_config(config: Config, settings: RiskModelSettings | None = None) -> Config:
    return config.model_copy(update={"risk_model": settings or SampleRiskLake.build_settings()})


@pytest.fixture
def fitted(lake: MiniLake, config: Config) -> tuple[MiniLake, Config]:
    SampleRiskLake.write(lake, config)
    cfg = build_config(config)
    report = ServiceBuilder().build_risk_model(cfg, lake.catalog).run("r1")
    assert report.fetched == 2 and report.rows > 0
    return lake, cfg


# TC-RVW-001
def test_tc_rvw_001_validation_report(fitted: tuple[MiniLake, Config]) -> None:
    lake, _ = fitted
    report = pd.read_parquet(
        lake.lake_root / "derived" / "reports" / "risk_test" / "validation.parquet"
    )
    RISK_VALIDATION.validate(report)
    metrics = set(zip(report["metric"], report["scope"], strict=True))
    assert ("median_r2", "model") in metrics and ("median_r2", "window") in metrics
    assert ("bias", "factor:size") in metrics and ("bias", "rp_000") in metrics
    assert ("share_in_band", "random_portfolios") in metrics
    assert report["notes"].str.contains("run r1").all()


# TC-RVW-002
def test_tc_rvw_002_short_window_writes_nothing(lake: MiniLake, config: Config) -> None:
    SampleRiskLake.write(lake, config)
    cfg = build_config(config)
    step = ServiceBuilder().build_risk_model(cfg, lake.catalog)
    with pytest.raises(LakeError):
        step._validation.write(pd.DataFrame(), "r0")  # no risk views yet
    lake.writer.write_derived(
        "risk_specific_risk",
        2026,
        pd.DataFrame(
            {
                "trade_date": [SampleRiskLake.DAYS[-1]],
                "ts_code": ["000000.SZ"],
                "sigma": [0.02],
                "sigma_raw": [0.02],
                "method": ["ewma"],
            }
        ),
    )
    step._views.refresh_tables()
    out = step._validation.write(pd.DataFrame(), "r0")
    assert out.empty
    assert not (lake.lake_root / "derived" / "reports" / "risk_test").exists()
