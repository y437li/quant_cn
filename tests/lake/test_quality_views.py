from __future__ import annotations

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.quality_views import QualityViews
from tests.support import MiniLake


def write(
    lake: MiniLake, config: Config, name: str, key: str, rows: list[dict[str, object]]
) -> None:
    spec = config.get_dataset(name)
    base = {f: None for f in spec.fields}
    lake.writer.write_raw(spec, key, pd.DataFrame([base | r for r in rows]))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)


# TC-QV-001
def test_tc_qv_001_price_crosscheck(lake: MiniLake, config: Config) -> None:
    day = "20260924"
    write(
        lake,
        config,
        "daily",
        day,
        [
            {"ts_code": "600000.SH", "trade_date": day, "close": 9.0},
            {"ts_code": "600001.SH", "trade_date": day, "close": 5.0},
        ],
    )
    write(
        lake,
        config,
        "baostock_daily",
        "600000.SH",
        [
            {"ts_code": "600000.SH", "trade_date": day, "close": 9.1, "tradestatus": 1.0},
        ],
    )
    write(
        lake,
        config,
        "baostock_daily",
        "600001.SH",
        [
            {"ts_code": "600001.SH", "trade_date": day, "close": 5.0, "tradestatus": 1.0},
        ],
    )
    write(
        lake,
        config,
        "baostock_daily_recent",
        "600000.SH",
        [  # the recent refetch wins
            {"ts_code": "600000.SH", "trade_date": day, "close": 9.0, "tradestatus": 1.0},
        ],
    )
    assert "quality.price_crosscheck" in QualityViews(lake.catalog, lake.query).refresh()
    row = lake.query.sql("SELECT * FROM quality.price_crosscheck").to_dict("records")[0]
    assert (row["compared"], row["mismatches"]) == (2, 0)


# TC-QV-002
def test_tc_qv_002_adj_crosscheck(lake: MiniLake, config: Config) -> None:
    write(
        lake,
        config,
        "adj_factor",
        "x",
        [
            {"ts_code": "600000.SH", "trade_date": "20250715", "adj_factor": 10.0},
            {"ts_code": "600000.SH", "trade_date": "20250716", "adj_factor": 10.5},
        ],
    )
    write(
        lake,
        config,
        "baostock_adj_factor",
        "600000.SH",
        [
            {"ts_code": "600000.SH", "trade_date": "20240718", "back_adjust_factor": 2.0},
            {"ts_code": "600000.SH", "trade_date": "20250716", "back_adjust_factor": 2.1},
        ],
    )
    QualityViews(lake.catalog, lake.query).refresh()
    row = lake.query.sql("SELECT * FROM quality.adj_crosscheck").to_dict("records")[0]
    assert row["trade_date"] == "20250716" and abs(row["rel_diff"]) < 1e-12


# TC-QV-003
def test_tc_qv_003_missing_inputs(lake: MiniLake) -> None:
    assert QualityViews(lake.catalog, lake.query).refresh() == []
    assert not lake.query.has_view("quality.price_crosscheck")
