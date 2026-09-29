from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.config import Config, FuturesCategory
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


def build_holding(rows: list[tuple[str, str, str, str, float]], config: Config) -> pd.DataFrame:
    base = {f: None for f in config.get_dataset("fut_holding").fields}
    return pd.DataFrame(
        [
            {**base, "trade_date": d, "exchange": e, "symbol": s, "broker": b, "long_hld": v}
            for d, e, s, b, v in rows
        ]
    )


# TC-DV-005
def test_tc_dv_005_fut_holding_brokers(lake: MiniLake, config: Config) -> None:
    rows = [
        ("20220615", "DCE", "M2207", "国泰君安", 10.0),
        ("20220615", "DCE", "M2207", "期货公司会员", 99.0),  # category total
        ("20220615", "DCE", "M", "国泰君安", 50.0),  # product-level symbol
        ("20200318", "ZCE", "SR005", "华泰期货", 5.0),  # vendor label slip
    ]
    lake.writer.write_raw(config.get_dataset("fut_holding"), "x", build_holding(rows, config))
    rebuild_curated(lake, config, "fut_holding")
    cats = [FuturesCategory(exchange="DCE", broker="期货公司会员")]
    DerivedViews(lake.catalog, lake.query, config.datasets, cats).refresh()
    out = lake.query.sql(
        "SELECT exchange, symbol, broker FROM derived.fut_holding_brokers ORDER BY symbol"
    )
    assert out.to_dict("records") == [
        {"exchange": "DCE", "symbol": "M2207", "broker": "国泰君安"},
        {"exchange": "CZCE", "symbol": "SR005", "broker": "华泰期货"},
    ]


# TC-DV-006
def test_tc_dv_006_fut_daily_one_sided(lake: MiniLake, config: Config) -> None:
    base = {f: None for f in config.get_dataset("fut_daily").fields}
    rows = [
        ("CU2003.SHF", "20191231", 200.0),
        ("CU2003.SHF", "20200102", 110.0),
        ("IF2001.CFX", "20191231", 80.0),
    ]
    df = pd.DataFrame(
        [
            {**base, "ts_code": c, "trade_date": d, "oi": v, "vol": v, "amount": v}
            for c, d, v in rows
        ]
    )
    lake.writer.write_raw(config.get_dataset("fut_daily"), "x", df)
    rebuild_curated(lake, config, "fut_daily")
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    out = lake.query.sql(
        "SELECT ts_code, trade_date, oi, vol, amount, two_sided_adjusted"
        " FROM derived.fut_daily_one_sided ORDER BY ts_code, trade_date"
    )
    assert out["oi"].tolist() == [100.0, 110.0, 80.0]
    assert out["amount"].tolist() == [100.0, 110.0, 80.0]
    assert out["two_sided_adjusted"].tolist() == [True, False, False]


# TC-DV-007
def test_tc_dv_007_industry_l1(lake: MiniLake, config: Config) -> None:
    base = {f: None for f in config.get_dataset("index_member_all").fields}
    rows = [  # joins 2019-07-24 in L1 A, leaves 2020-06-30, rejoins 2021-07-30 in L1 B
        ("600001.SH", "801010.SI", "857001.SI", "20190724", "20200630"),
        ("600001.SH", "801020.SI", "857002.SI", "20210730", None),
    ]
    df = pd.DataFrame(
        [
            {**base, "ts_code": t, "l1_code": l1, "l3_code": l3, "in_date": i, "out_date": o}
            for t, l1, l3, i, o in rows
        ]
    )
    lake.writer.write_raw(config.get_dataset("index_member_all"), "Y", df)
    rebuild_curated(lake, config, "index_member_all")
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh()
    out = lake.query.sql(
        "SELECT l1_code, valid_from, valid_to, industry_backfilled FROM derived.industry_l1"
        " ORDER BY coalesce(valid_from, '')"
    )
    out = out.astype(object).where(out.notna(), None)
    assert out.values.tolist() == [
        ["801010.SI", None, "20190723", True],
        ["801010.SI", "20190724", "20200630", False],
        ["801010.SI", "20200701", "20210729", True],
        ["801020.SI", "20210730", None, False],
    ]
