"""Contract tests for portfolio.SectorEarningsSignalBuilder (plan 35, D-172)."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from quant_cn.calculation.earnings_event_builder import EVENT_COLUMNS, EarningsEventBuilder
from quant_cn.core.config import Config
from quant_cn.core.exceptions import LakeError
from quant_cn.core.sector_earnings_signal_settings import SectorEarningsSignalSettings
from quant_cn.portfolio.sector_earnings_signal_builder import SectorEarningsSignalBuilder
from tests.support import MiniLake, SampleFactorLake

DAYS = [f"202503{d:02d}" for d in range(1, 31)]
CODES = [f"00000{i}.SZ" for i in range(10)]
SETTINGS = SectorEarningsSignalSettings(min_events=2, back_window=5, fwd_windows=[3], rally_min=2.0)


class FixedEvents(EarningsEventBuilder):
    """Events from a fixed table, cut at as_of by day 0."""

    def __init__(self, events: pd.DataFrame) -> None:
        self._table = events

    def build(self, as_of: str) -> pd.DataFrame:
        return self._table[self._table["day0"] <= as_of].reset_index(drop=True)


def build_events(pre: float = 20.0, react: float = 0.5) -> pd.DataFrame:
    rows = []
    for q, start, p in (("20241231", 0, 0.0), ("20250331", 10, pre)):
        for i, code in enumerate(CODES):
            day = DAYS[start + 9 - i]  # the best surprises report first
            rows.append(
                {
                    "ts_code": code,
                    "end_date": q,
                    "first_ann": day,
                    "day0": day,
                    "sue": float(i),
                    "dec": float(i),
                    "pre": p,
                    "react": react if q == "20250331" else 0.0,
                    "post": 0.0,
                }
            )
    rows.append(
        {
            "ts_code": "000099.SZ",
            "end_date": "20250331",
            "first_ann": DAYS[10],
            "day0": DAYS[10],
            "sue": 9.0,
            "dec": 9.0,
            "pre": -50.0,
            "react": 9.0,
            "post": 0.0,
        }
    )  # joined the sector after the quarter end: not counted
    return pd.DataFrame(rows, columns=list(EVENT_COLUMNS))


def write_lake(lake: MiniLake, config: Config) -> None:
    SampleFactorLake.write(
        lake,
        config,
        "index_member_all",
        [
            {"l2_code": "801001.SI", "l3_code": "x", "ts_code": c, "in_date": "20000101"}
            for c in CODES
        ]
        + [{"l2_code": "801001.SI", "l3_code": "x", "ts_code": "000099.SZ", "in_date": "20250401"}],
    )
    SampleFactorLake.write(
        lake,
        config,
        "index_classify",
        [
            {"index_code": c, "industry_name": n, "level": "L2", "src": "SW2021"}
            for c, n in (("801001.SI", "测试"), ("801002.SI", "对照"))
        ],
    )
    SampleFactorLake.write(
        lake,
        config,
        "sw_daily",
        [
            {"ts_code": "801001.SI", "trade_date": d, "close": 100 * 1.01**i}
            for i, d in enumerate(DAYS)
        ]
        + [{"ts_code": "801002.SI", "trade_date": d, "close": 100.0} for d in DAYS],
    )
    SampleFactorLake.write(
        lake,
        config,
        "stk_holdernumber",
        [
            {"ts_code": c, "end_date": q, "ann_date": "20250315", "holder_num": h}
            for c in CODES
            for q, h in (("20241231", 100.0), ("20250331", 110.0))
        ],
    )


def build(lake: MiniLake, events: pd.DataFrame) -> SectorEarningsSignalBuilder:
    return SectorEarningsSignalBuilder(SETTINGS, FixedEvents(events), lake.query)


# TC-SEB-001
def test_tc_seb_001_cells(lake: MiniLake, config: Config) -> None:
    write_lake(lake, config)
    doc = build(lake, build_events()).build(None, "20250330")
    assert doc["season"] == "20250331"
    row = doc["rows"][0]
    assert (row["code"], row["name"], row["n"], row["expected"], row["share"]) == (
        "801001.SI",
        "测试",
        10,
        10,
        1.0,
    )
    assert (row["n_top"], row["pre"], row["react"]) == (2, 20.0, 0.5)
    assert row["sig_date"] == DAYS[17]  # int(0.8 x 9) + 1 = 8th of the quarter's day 0s
    assert row["hchg"] == pytest.approx(10.0)
    assert {r["end_date"] for r in doc["history"]} == {"20241231", "20250331"}


# TC-SEB-002
def test_tc_seb_002_status_index_flags(lake: MiniLake, config: Config) -> None:
    write_lake(lake, config)
    b = build(lake, build_events())
    doc = b.build(None, "20250330")
    row = doc["rows"][0]
    excess = 100 * 0.5 * math.log(1.01)  # the sector's log return less the two-index mean
    assert row["status"] == "firing" and row["rally"]
    assert row["back"] == pytest.approx(5 * excess, abs=0.01)
    assert row["fwd3"] == pytest.approx(3 * excess, abs=0.01)
    assert doc["new_flags"] == ["801001.SI"] and b.build(doc, "20250330")["new_flags"] == []
    assert doc["record"]["all"]["n"] == 1
    early = b.build(None, "20250315")  # 5 of 10 out: the same test is provisional
    assert early["rows"][0]["status"] == "provisional" and early["rows"][0]["share"] == 0.5
    assert early["rows"][0]["fwd3"] is None
    assert (
        build(lake, build_events(react=1.5)).build(None, "20250330")["rows"][0]["status"] == "none"
    )
    assert (
        build(lake, build_events(pre=14.0)).build(None, "20250330")["rows"][0]["status"] == "none"
    )


# TC-SEB-003
def test_tc_seb_003_write(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    empty = build(lake, build_events().iloc[0:0]).build(None, "20250330")
    assert empty["rows"] == [] and empty["season"] is None
    write_lake(lake, config)
    b = build(lake, build_events())
    path = b.write(tmp_path, "20250330")
    assert path.name == "sector_earnings_signal.json" and path.exists()
    with pytest.raises(LakeError):
        b.write(tmp_path / "missing", "20250330")
