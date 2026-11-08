from __future__ import annotations

import pandas as pd

from quant_cn.core.config import Config, TickerAlias
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from tests.support import MiniLake

DAYS = [f"202601{d:02d}" for d in range(1, 26)]


def write(lake: MiniLake, config: Config, name: str, rows: list[dict[str, object]]) -> None:
    spec = config.get_dataset(name)
    base = {f: None for f in spec.fields}
    lake.writer.write_raw(spec, "x", pd.DataFrame([base | r for r in rows]))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)


def build_lake(lake: MiniLake, config: Config) -> TickerAliasMap:
    listed = ["001914.SZ", "600001.SH", "600002.SH"]
    write(lake, config, "stock_basic", [{"ts_code": c, "list_status": "L"} for c in listed])
    bars = []
    for i, day in enumerate(DAYS):
        bars += [
            {"ts_code": "000043.SZ", "trade_date": day, "close": 10.0 + i},  # retired, same bars
            {"ts_code": "001914.SZ", "trade_date": day, "close": 10.0 + i},
            {"ts_code": "000099.SZ", "trade_date": day, "close": 50.0 + i},  # matches two codes
            {"ts_code": "600001.SH", "trade_date": day, "close": 50.0 + i},
            {"ts_code": "600002.SH", "trade_date": day, "close": 50.0 + i},
        ]
    write(lake, config, "daily", bars)
    aliases = [TickerAlias(old_code="000022.SZ", new_code="001872.SZ")]
    alias_map = TickerAliasMap(lake.catalog, lake.query, aliases)
    alias_map.refresh()
    return alias_map


# TC-TAM-001
def test_tc_tam_001_detection(lake: MiniLake, config: Config) -> None:
    alias_map = build_lake(lake, config)
    row = lake.query.sql("SELECT * FROM derived.ticker_alias WHERE old_code = '000043.SZ'").iloc[0]
    assert (row["new_code"], row["shared_days"], row["equal_rate"]) == ("001914.SZ", 25, 1.0)
    assert (row["source"], bool(row["accepted"])) == ("detected", True)
    assert alias_map.get_pairs() == {"000043.SZ": "001914.SZ", "000022.SZ": "001872.SZ"}


# TC-TAM-002
def test_tc_tam_002_ambiguous(lake: MiniLake, config: Config) -> None:
    build_lake(lake, config)
    rows = lake.query.sql("SELECT * FROM derived.ticker_alias WHERE old_code = '000099.SZ'")
    assert len(rows) == 2 and set(rows["candidates"]) == {2} and not rows["accepted"].any()


# TC-TAM-003
def test_tc_tam_003_apply(lake: MiniLake, config: Config) -> None:
    alias_map = build_lake(lake, config)
    frame = pd.DataFrame(
        {
            "trade_date": ["20260101", "20260101", "20260102"],
            "ts_code": ["000043.SZ", "001914.SZ", "000043.SZ"],
            "up_limit": [1.0, 2.0, 3.0],
        }
    )
    out = alias_map.normalize_codes(frame, ["trade_date", "ts_code"])
    assert out.to_dict("records") == [
        {"trade_date": "20260101", "ts_code": "001914.SZ", "up_limit": 2.0},  # new code wins
        {"trade_date": "20260102", "ts_code": "001914.SZ", "up_limit": 3.0},  # only under old code
    ]


# TC-TAM-004
def test_tc_tam_004_list_codes(lake: MiniLake, config: Config) -> None:
    alias_map = build_lake(lake, config)
    assert alias_map.list_codes(["001914.SZ", "600001.SH"]) == [
        "001914.SZ",
        "600001.SH",
        "000043.SZ",
    ]
