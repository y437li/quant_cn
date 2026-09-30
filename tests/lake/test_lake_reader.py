from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.core.config import Config, TickerAlias
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.lake_reader import LakeReader
from quant_cn.lake.panel_cache import PanelCache
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.trading_calendar import TradingCalendar
from tests.support import MiniLake, Sample

DAYS = ["20260105", "20260106", "20260107", "20260108"]
OLD, NEW, OTHER = "000043.SZ", "001914.SZ", "600000.SH"
ALIASES = [TickerAlias(old_code=OLD, new_code=NEW)]


def write(
    lake: MiniLake, config: Config, name: str, key: str, rows: list[dict[str, object]]
) -> None:
    spec = config.get_dataset(name)
    base = {f: None for f in spec.fields}
    lake.writer.write_raw(spec, key, pd.DataFrame([base | r for r in rows]))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)


def build_reader(lake: MiniLake, config: Config, cache: PanelCache | None = None) -> LakeReader:
    lake.writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(DAYS))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(
        config.get_dataset("trade_cal")
    )
    write(
        lake, config, "stock_basic", "L", [{"ts_code": c, "list_status": "L"} for c in (NEW, OTHER)]
    )
    bars = [{"ts_code": OTHER, "trade_date": d, "close": 5.0} for d in (DAYS[0], DAYS[3])]  # gap
    bars += [{"ts_code": c, "trade_date": d, "close": 9.0} for c in (OLD, NEW) for d in DAYS]
    write(lake, config, "daily", "x", bars)
    write(
        lake,
        config,
        "adj_factor",
        "x",
        [{"ts_code": b["ts_code"], "trade_date": b["trade_date"], "adj_factor": 1.0} for b in bars],
    )
    limits = [{"ts_code": OLD, "trade_date": d, "up_limit": 1.0} for d in DAYS[:2]]
    limits += [{"ts_code": NEW, "trade_date": DAYS[1], "up_limit": 2.0}]
    write(lake, config, "stk_limit", "x", limits)
    statement = {
        "end_date": "20251231",
        "report_type": "1",
        "update_flag": "1",
        "total_profit": 7.0,
    }
    write(
        lake,
        config,
        "income_vip",
        "x",
        [{"ts_code": OLD, "ann_date": DAYS[0], "f_ann_date": DAYS[0], **statement}],
    )
    DerivedViews(lake.catalog, lake.query, config.datasets, aliases=ALIASES).refresh()
    aligner = PitAligner(lake.catalog, lake.query, DateCodec())
    aligner.refresh()
    alias_map = TickerAliasMap(lake.catalog, lake.query, ALIASES)
    return LakeReader(
        lake.catalog,
        lake.query,
        config.datasets,
        aligner,
        alias_map,
        TradingCalendar(lake.query),
        cache,
    )


# TC-LRD-001
def test_tc_lrd_001_read_panel(lake: MiniLake, config: Config) -> None:
    reader = build_reader(lake, config)
    out = reader.read_panel("stk_limit", DAYS[0], DAYS[3], tickers=[NEW], columns=["up_limit"])
    assert out[["trade_date", "ts_code", "up_limit"]].values.tolist() == [
        [DAYS[0], NEW, 1.0],  # only under the old code: attached to the new code
        [DAYS[1], NEW, 2.0],  # both codes: the new code's row wins
    ]
    with pytest.raises(LakeError):
        reader.read_panel("trade_cal", DAYS[0], DAYS[3])  # no date column: read_reference


# TC-LRD-002
def test_tc_lrd_002_dense_prices(lake: MiniLake, config: Config) -> None:
    reader = build_reader(lake, config)
    sparse = reader.read_prices(DAYS[0], DAYS[3], tickers=[OTHER])
    dense = reader.read_prices(DAYS[0], DAYS[3], tickers=[OTHER], dense=True)
    assert len(sparse) == 2 and dense["trade_date"].tolist() == DAYS
    assert math.isnan(dense.loc[1, "close"]) and dense.loc[3, "close"] == 5.0


# TC-LRD-003
def test_tc_lrd_003_fundamentals_alias(lake: MiniLake, config: Config) -> None:
    reader = build_reader(lake, config)
    out = reader.read_fundamentals_pit(["total_profit"], DAYS[0], DAYS[3], tickers=[NEW])
    assert out["ts_code"].unique().tolist() == [NEW]
    assert out["trade_date"].tolist() == DAYS[1:]  # visible the session after the announcement
    assert out["value"].tolist() == [7.0, 7.0, 7.0]


# TC-LRD-004
def test_tc_lrd_004_reference(lake: MiniLake, config: Config) -> None:
    reader = build_reader(lake, config)
    assert set(reader.read_reference("stock_basic")["ts_code"]) == {NEW, OTHER}
    with pytest.raises(LakeError):
        reader.read_reference("daily")
    with pytest.raises(LakeError):
        reader.read_reference("no_such_dataset")


# TC-LRD-006
def test_tc_lrd_006_cache(lake: MiniLake, config: Config) -> None:
    cache = PanelCache()
    reader = build_reader(lake, config, cache)
    reader.read_prices(DAYS[0], DAYS[3])
    reader.read_prices(DAYS[0], DAYS[3])
    assert (cache.misses, cache.hits) == (1, 1)


# TC-LRD-007
def test_tc_lrd_007_read_universe(lake: MiniLake, config: Config) -> None:
    rows = pd.DataFrame(
        {
            "trade_date": [DAYS[0], DAYS[0], DAYS[1]],
            "ts_code": [NEW, OTHER, NEW],
            "in_universe": [1.0, 0.0, 1.0],
            "reason": ["", "suspended", ""],
        }
    )
    lake.writer.write_derived("universe", 2026, rows)
    reader = build_reader(lake, config)
    assert len(reader.read_universe(DAYS[0], DAYS[0])) == 2
    members = reader.read_universe(DAYS[0], DAYS[3], members_only=True)
    assert members["ts_code"].tolist() == [NEW, NEW]
