"""Contract tests for calculation.EarningsEventBuilder (plan 35, D-172)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.earnings_event_builder import EarningsEventBuilder
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.sector_earnings_signal_settings import SectorEarningsSignalSettings
from tests.support import MiniLake, SampleFactorLake

YTD = {"2018": [10, 20, 30, 40], "2019": [11, 23, 36, 50], "2020": [15, 31, 48, 66]}
ENDS = ["0331", "0630", "0930", "1231"]


def build_profit(drop: str | None = None) -> pd.DataFrame:
    rows = [
        {"ts_code": "A", "end_date": y + e, "cum": float(v)}
        for y, vals in YTD.items()
        for e, v in zip(ENDS, vals, strict=True)
    ]
    return pd.DataFrame([r for r in rows if r["end_date"] != drop])


# TC-EEB-001
def test_tc_eeb_001_sue() -> None:
    out = EarningsEventBuilder.compute_sue(build_profit(), 8, 4).set_index("end_date")["sue"]
    # single quarters 2019: 11 12 13 14, 2020: 15 16 17 18 -> yoy 1 2 3 4 then 4 4 4 4
    assert math.isnan(out["20191231"])  # only 3 prior changes
    assert out["20200331"] == pytest.approx(4 / np.std([1, 2, 3, 4], ddof=1))
    assert out["20200630"] == pytest.approx(4 / np.std([1, 2, 3, 4, 4], ddof=1))
    gap = EarningsEventBuilder.compute_sue(build_profit("20200630"), 8, 4).set_index("end_date")
    assert "20200630" not in gap.index and math.isnan(gap.at["20200930", "sue"])


# TC-EEB-002
def test_tc_eeb_002_windows() -> None:
    days = [f"2025010{d}" for d in range(1, 7)]
    cum = pd.DataFrame(
        {"A": [0.0, 0.01, 0.03, 0.06, 0.10, 0.15], "B": [np.nan, np.nan, 0.0, 0.0, 0.01, 0.02]},
        index=days,
    )
    events = pd.DataFrame(
        {"ts_code": ["A", "B", "A"], "first_ann": ["20250104", "20250104", "20250110"]}
    )
    out = EarningsEventBuilder.compute_windows(events, cum, 2, 1)
    assert out.loc[0, "day0"] == "20250104"
    assert out.loc[0, ["pre", "react"]].tolist() == pytest.approx([3.0, 7.0])
    assert math.isnan(out.loc[0, "post"])  # 20 sessions after are not there yet
    assert math.isnan(out.loc[1, "pre"]) and out.loc[1, "react"] == pytest.approx(1.0)
    assert pd.isna(out.loc[2, "day0"]) and math.isnan(out.loc[2, "react"])


DAYS = ["20250407", "20250408", "20250409", "20250410", "20250411", "20250414", "20250415"]
A, B = "000001.SZ", "000002.SZ"


def write_lake(lake: MiniLake, config: Config) -> None:
    rise = [{"ts_code": A, "trade_date": d, "close": 10.0 + i} for i, d in enumerate(DAYS)]
    flat = [{"ts_code": B, "trade_date": d, "close": 10.0} for d in DAYS]
    SampleFactorLake.write(lake, config, "daily", rise + flat)
    adj = [{"ts_code": c, "trade_date": d, "adj_factor": 1.0} for c in (A, B) for d in DAYS]
    SampleFactorLake.write(lake, config, "adj_factor", adj)
    flag = {"ts_code": A, "update_flag": "0"}
    report = {"end_date": "20250331", "ann_date": "20250425", "f_ann_date": "20250425"}
    SampleFactorLake.write(
        lake, config, "income_vip", [flag | report | {"report_type": "1", "n_income_attr_p": 5.0}]
    )
    previews = [("20250331", "20250410"), ("20250630", "20250301")]
    SampleFactorLake.write(
        lake, config, "forecast_vip", [flag | {"end_date": e, "ann_date": a} for e, a in previews]
    )
    SampleFactorLake.write(
        lake, config, "express_vip", [flag | {"end_date": "20250331", "ann_date": "20250414"}]
    )


# TC-EEB-003
def test_tc_eeb_003_build_pit(lake: MiniLake, config: Config) -> None:
    settings = SectorEarningsSignalSettings(start="20250101", pre_window=2, react_window=1)
    builder = EarningsEventBuilder(settings, lake.query, DateCodec())
    assert builder.build("20250420").empty
    write_lake(lake, config)
    out = builder.build("20250420")
    # the H1 preview inside the Q1 season counts as the H1 event's first disclosure
    assert out[["end_date", "first_ann", "day0"]].values.tolist() == [
        ["20250331", "20250410", "20250410"],
        ["20250630", "20250301", "20250407"],
    ]
    assert math.isnan(out.loc[0, "sue"]) and math.isnan(out.loc[0, "dec"])
    # stock 1 rises ~10% a day, stock 2 is flat: half the gap is the excess over the mean
    assert out.loc[0, "pre"] > 0 and out.loc[0, "react"] > 0
    early = builder.build("20250410")  # only day 0 is out: the reaction window is incomplete
    assert math.isnan(early.loc[0, "react"]) and early.loc[0, "pre"] == pytest.approx(
        out.loc[0, "pre"]
    )
    assert builder.build("20250409")["end_date"].tolist() == ["20250630"]  # Q1 not out yet
