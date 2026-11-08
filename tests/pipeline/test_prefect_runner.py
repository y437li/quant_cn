from __future__ import annotations

from collections.abc import Iterator

import pytest
from prefect.testing.utilities import prefect_test_harness

from quant_cn.core.exceptions import DataSourceError, PermissionDeniedError
from quant_cn.pipeline.prefect_runner import PrefectRunner
from tests.support import MiniLake, ScriptStep


@pytest.fixture(scope="module", autouse=True)
def prefect_backend() -> Iterator[None]:
    with prefect_test_harness():
        yield


# TC-PFR-001
def test_tc_pfr_001_order(lake: MiniLake) -> None:
    report = PrefectRunner(lake.run_log).run("t", [ScriptStep("a"), ScriptStep("b")])
    assert [s.name for s in report.steps] == ["a", "b"] and report.status == "ok"
    runs = lake.query.sql("SELECT status FROM meta.run_log WHERE dataset IS NULL")
    assert runs["status"].tolist() == ["ok"]


# TC-PFR-002
def test_tc_pfr_002_blocked_continues(lake: MiniLake) -> None:
    later = ScriptStep("c")
    report = PrefectRunner(lake.run_log).run(
        "t", [ScriptStep("vip", PermissionDeniedError("no")), later]
    )
    assert report.list_blocked() == ["vip"] and later.ran


# TC-PFR-003
def test_tc_pfr_003_failure(lake: MiniLake) -> None:
    later = ScriptStep("c")
    with pytest.raises(DataSourceError):
        PrefectRunner(lake.run_log).run("t", [ScriptStep("x", DataSourceError("boom")), later])
    assert not later.ran
    runs = lake.query.sql("SELECT status FROM meta.run_log WHERE dataset IS NULL")
    assert runs["status"].tolist() == ["failed"]
