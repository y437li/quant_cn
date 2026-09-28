from __future__ import annotations

import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from tests.support import MiniLake, Sample


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
    lake.writer.write_raw(
        config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(["20260828"])
    )
    lake.catalog.refresh_views()
    assert lake.query.has_view("raw.trade_cal")


# TC-LQ-004
def test_tc_lq_004_read_prices(lake: MiniLake, config: Config) -> None:
    for day in ("20260827", "20260828"):
        bars = Sample.build_bars(day).assign(
            open=1.0, high=1.0, low=1.0, pre_close=1.0, change=0.0, pct_chg=0.0, vol=1.0, amount=1.0
        )
        lake.writer.write_raw(config.get_dataset("daily"), day, bars)
        lake.writer.write_raw(
            config.get_dataset("adj_factor"),
            day,
            bars[["ts_code", "trade_date"]].assign(adj_factor=1.0),
        )
    compactor = Compactor(lake.catalog, lake.query, lake.writer, lake.clock)
    compactor.rebuild(config.get_dataset("daily"))
    compactor.rebuild(config.get_dataset("adj_factor"))
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    out = lake.query.read_prices("20260828", "20260828", tickers=["600000.SH"])
    assert out[["trade_date", "ts_code"]].values.tolist() == [["20260828", "600000.SH"]]
    assert len(lake.query.read_prices("20260801", "20260831")) == 4
