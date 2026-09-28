from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from tests.support import Build, MiniLake


# TC-LQ-001
def test_tc_lq_001_params(lake: MiniLake) -> None:
    df = lake.query.sql("SELECT ? + 1 AS x", [41])
    assert df["x"].iloc[0] == 42


# TC-LQ-002
def test_tc_lq_002_bad_sql(lake: MiniLake) -> None:
    with pytest.raises(LakeError):
        lake.query.sql("SELEC nonsense")


# TC-LQ-003
def test_tc_lq_003_has_view(lake: MiniLake, config: Config) -> None:
    assert not lake.query.has_view("raw.trade_cal")
    lake.writer.write_raw(config.get_dataset("trade_cal"), "all", Build.trade_cal(["20260828"]))
    lake.catalog.refresh_views()
    assert lake.query.has_view("raw.trade_cal")
