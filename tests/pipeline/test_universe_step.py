from __future__ import annotations

import pandas as pd

from quant_cn.core.config import Config, UniverseConfig
from quant_cn.lake.compactor import Compactor
from quant_cn.pipeline.universe_step import UniverseStep
from tests.support import MiniLake, Sample

D = [f"202601{d:02d}" for d in (5, 6, 7, 8, 9, 12, 13, 14)]


def write(lake: MiniLake, config: Config, name: str, rows: list[dict[str, object]]) -> None:
    spec = config.get_dataset(name)
    base = {f: None for f in spec.fields}
    lake.writer.write_raw(spec, "x", pd.DataFrame([base | r for r in rows]))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)


def build_step(lake: MiniLake, config: Config) -> UniverseStep:
    lake.writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(D))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(
        config.get_dataset("trade_cal")
    )
    basic = [
        {"ts_code": "600001.SH", "list_date": D[0]},  # clean, suspended on D[4]
        {"ts_code": "000002.SZ", "list_date": D[0]},  # ST from D[3] to D[5]
        {"ts_code": "830001.BJ", "list_date": D[0]},  # exchange
        {"ts_code": "600005.SH", "list_date": D[4]},  # new listing
        {"ts_code": "600006.SH", "list_date": D[0], "delist_date": D[5]},  # delisted
        {"ts_code": "000007.SZ", "list_date": D[0]},  # delisting arrangement from D[2]
    ]
    write(lake, config, "stock_basic", [b | {"list_status": "L"} for b in basic])
    names = [
        {"ts_code": "000002.SZ", "name": "某某股份", "start_date": D[0], "end_date": D[2]},
        {"ts_code": "000002.SZ", "name": "ST某某", "start_date": D[3], "end_date": D[5]},
        {"ts_code": "000002.SZ", "name": "某某股份", "start_date": D[6]},
        {"ts_code": "000007.SZ", "name": "国华退", "start_date": D[2]},
    ]
    write(lake, config, "namechange", names)
    bars = [
        {"ts_code": b["ts_code"], "trade_date": d, "close": 1.0}
        for b in basic
        for d in D
        if not (b["ts_code"] == "600001.SH" and d == D[4])
    ]
    write(lake, config, "daily", bars)
    rules = UniverseConfig(start="20260101", min_sessions=3, exchanges=["SH", "SZ"])
    return UniverseStep(lake.query, lake.writer, rules)


def read(lake: MiniLake) -> pd.DataFrame:
    return pd.read_parquet(lake.lake_root / "derived" / "universe" / "year=2026" / "part-0.parquet")


# TC-US-001
def test_tc_us_001_reasons(lake: MiniLake, config: Config) -> None:
    step = build_step(lake, config)
    report = step.run("r1")
    out = read(lake).set_index(["ts_code", "trade_date"])
    assert report.fetched == 1 and report.rows == len(out)
    assert out.loc[("600001.SH", D[3]), "in_universe"] == 1.0
    assert out.loc[("600001.SH", D[4]), "reason"] == "suspended"
    assert out.loc[("830001.BJ", D[3]), "reason"] == "exchange"
    assert out.loc[("000007.SZ", D[3]), "reason"] == "delisting"
    assert out.loc[("600005.SH", D[5]), "reason"] == "new_listing"  # 2nd session since listing
    assert out.loc[("600005.SH", D[6]), "in_universe"] == 1.0  # 3rd session
    assert out.loc[("600001.SH", D[0]), "reason"] == "new_listing"


# TC-US-002
def test_tc_us_002_st_pit(lake: MiniLake, config: Config) -> None:
    build_step(lake, config).run("r1")
    st = read(lake).query("ts_code == '000002.SZ'").set_index("trade_date")
    assert st.loc[D[2], "in_universe"] == 1.0
    assert st.loc[D[3], "reason"] == "st" and st.loc[D[5], "reason"] == "st"
    assert st.loc[D[6], "in_universe"] == 1.0  # ST name ended


# TC-US-003
def test_tc_us_003_listed_only(lake: MiniLake, config: Config) -> None:
    step = build_step(lake, config)
    assert step.list_units() == ["2026"]
    step.run("r1")
    delisted = read(lake).query("ts_code == '600006.SH'")["trade_date"].tolist()
    assert delisted == D[:5]  # trades until the session before delist_date
    assert read(lake).query("ts_code == '600005.SH'")["trade_date"].min() == D[4]


# TC-US-004
def test_tc_us_004_missing_inputs(lake: MiniLake) -> None:
    step = UniverseStep(lake.query, lake.writer, UniverseConfig())
    assert step.list_units() == [] and step.run("r1").keys_total == 0
