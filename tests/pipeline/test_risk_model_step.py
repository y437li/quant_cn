"""Tests of risk_model_step (plan 05)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.frames import FACTOR_COV, RISK_EXPOSURE, SPECIFIC_RISK
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


# TC-RMST-001
def test_tc_rmst_001_units(lake: MiniLake, config: Config) -> None:
    step = ServiceBuilder().build_risk_model(build_config(config), lake.catalog)
    assert step.list_units() == []
    SampleRiskLake.write(lake, config)
    assert step.list_units() == ["2025", "2026"]
    late = SampleRiskLake.build_settings().model_copy(update={"start": "20300101"})
    assert (
        ServiceBuilder().build_risk_model(build_config(config, late), lake.catalog).list_units()
        == []
    )


# TC-RMST-002
def test_tc_rmst_002_writes_frames_views_digests(fitted: tuple[MiniLake, Config]) -> None:
    lake, _ = fitted
    for table in TABLES:
        assert (lake.lake_root / "derived" / table / "year=2025" / "part-0.parquet").exists()
        assert (lake.lake_root / "derived" / table / "year=2026" / "part-0.parquet").exists()
        assert lake.query.has_view(f"derived.{table}")
    exposure = lake.query.sql("SELECT * FROM derived.risk_exposure")
    RISK_EXPOSURE.validate(exposure)
    assert {"size", "liquidity"} <= set(exposure["factor"])
    cov = lake.query.sql("SELECT * FROM derived.risk_factor_cov")
    FACTOR_COV.validate(cov)
    assert {"country", "size", "ind_800"} <= set(cov["factor_i"])
    spec = lake.query.sql("SELECT * FROM derived.risk_specific_risk")
    SPECIFIC_RISK.validate(spec)
    assert (spec["sigma"] > 0).all()
    fr = lake.query.sql("SELECT * FROM derived.risk_factor_return")
    assert fr["trade_date"].min() == SampleRiskLake.DAYS[1]  # first session has no t-1 exposures
    monitor = pd.read_parquet(
        lake.lake_root / "derived" / "reports" / "risk_test" / "monitor_returns.parquet"
    )
    assert set(monitor["factor"]) == {"beta_monitor"} and len(monitor) > 0
    assert "beta_monitor" in set(exposure["factor"]) and "beta_monitor" not in set(cov["factor_i"])
    digests = json.loads(
        (lake.lake_root / "meta" / "manifest" / "derived_digests.json").read_text()
    )
    assert all(digests[f"derived.{t}"].startswith("h:") for t in TABLES)  # scalable (D-135)
