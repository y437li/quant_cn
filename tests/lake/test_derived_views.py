from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from tests.support import MiniLake, Sample, SampleLake


def rebuild_curated(lake: MiniLake, config: Config, *names: str) -> None:
    compactor = Compactor(lake.catalog, lake.query, lake.writer, lake.clock)
    for name in names:
        compactor.rebuild(config.get_dataset(name))


# TC-DV-001
def test_tc_dv_001_prices_adj(lake: MiniLake, config: Config) -> None:
    daily = Sample.build_bars("20260828").assign(
        open=1.0, high=1.0, low=1.0, pre_close=1.0, change=0.0, pct_chg=0.0, vol=1.0, amount=1.0
    )
    lake.writer.write_raw(config.get_dataset("daily"), "20260828", daily)
    adj = daily[["ts_code", "trade_date"]].assign(adj_factor=[2.0, 3.0])
    lake.writer.write_raw(config.get_dataset("adj_factor"), "20260828", adj)
    rebuild_curated(lake, config, "daily", "adj_factor")
    assert "derived.prices_adj" in DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    out = lake.query.read_prices("20260801", "20260831")
    assert out["close_adj"].tolist() == pytest.approx([10.0 * 2.0, 11.0 * 3.0])


# TC-DV-002
def test_tc_dv_002_fundamentals_long(lake: MiniLake, config: Config) -> None:
    rows = [
        ("20251231", "20260320", "1", 1.0),
        ("20251231", "20260410", "1", 2.0),
        ("20251231", "20260320", "2", 99.0),
    ]
    SampleLake.write_income(lake, config.get_dataset("income_vip"), rows)
    rebuild_curated(lake, config, "income_vip")
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    df = lake.query.sql(
        "SELECT known_on, field, value, source FROM derived.fundamentals_long ORDER BY known_on"
    )
    assert df["value"].tolist() == [1.0, 2.0] and set(df["field"]) == {"total_profit"}
    assert set(df["source"]) == {"income_vip"}


# TC-DV-003
def test_tc_dv_003_missing_inputs(lake: MiniLake, config: Config) -> None:
    assert DerivedViews(lake.catalog, lake.query, config.datasets).refresh() == []
    assert not lake.query.has_view("derived.prices_adj")


# TC-DV-004
def test_tc_dv_004_alias_codes_dropped(lake: MiniLake, config: Config) -> None:
    daily = Sample.build_bars("20260828", ("000043.SZ", "001914.SZ")).assign(
        open=1.0, high=1.0, low=1.0, pre_close=1.0, change=0.0, pct_chg=0.0, vol=1.0, amount=1.0
    )
    lake.writer.write_raw(config.get_dataset("daily"), "20260828", daily)
    adj = daily[["ts_code", "trade_date"]].assign(adj_factor=1.0)
    lake.writer.write_raw(config.get_dataset("adj_factor"), "20260828", adj)
    listed = {f: None for f in config.get_dataset("stock_basic").fields}
    basic = pd.DataFrame([{**listed, "ts_code": "001914.SZ", "list_status": "L"}])
    lake.writer.write_raw(config.get_dataset("stock_basic"), "L", basic)
    rebuild_curated(lake, config, "daily", "adj_factor", "stock_basic")
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    assert lake.query.read_prices("20260801", "20260831")["ts_code"].tolist() == ["001914.SZ"]
