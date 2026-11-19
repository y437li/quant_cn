"""Contract tests for risk.AnalystDescriptors (plan 37)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from quant_cn.risk.analyst_descriptors import AnalystDescriptors


def build_consensus(rows: list[tuple[str, str, int, float, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["trade_date", "ts_code", "fy1", "np1", "np2", "np3"]).assign(
        n_brokers=3
    )


# TC-AND-001
def test_tc_and_001_known_answers() -> None:
    cons = build_consensus([("20260630", "A", 2026, 100.0, 120.0, 169.0),
                            ("20270226", "A", 2026, 100.0, 120.0, 169.0)])  # fmt: skip
    keys = pd.DataFrame({"trade_date": ["20260715", "20270315"], "ts_code": ["A", "A"],
                         "total_mv": [1000.0, 1000.0]})  # fmt: skip
    out = AnalystDescriptors().compute(keys, cons)
    w = 5 / 12  # August to December left after a July session
    assert out.loc[0, "epfwd"] == pytest.approx((w * 100 + (1 - w) * 120) / 1000)
    assert out.loc[1, "epfwd"] == pytest.approx(120 / 1000)  # FY1 2026 has ended: FY2 only
    assert out.loc[0, "egrsf"] == pytest.approx(0.2)
    assert out.loc[0, "egrlf"] == pytest.approx(0.3)  # sqrt(169 / 100) - 1


# TC-AND-002
def test_tc_and_002_signs_and_missing() -> None:
    cons = build_consensus([("20260630", "A", 2026, -10.0, 50.0, 80.0),
                            ("20260630", "B", 2026, 10.0, 20.0, -5.0)])  # fmt: skip
    keys = pd.DataFrame({"trade_date": ["20260701"] * 3, "ts_code": ["A", "B", "C"],
                         "total_mv": [100.0, 100.0, 100.0]})  # fmt: skip
    out = AnalystDescriptors().compute(keys, cons).set_index("ts_code")
    assert math.isnan(out.at["A", "egrsf"]) and math.isnan(out.at["A", "egrlf"])
    assert out.at["B", "egrsf"] == pytest.approx(1.0) and math.isnan(out.at["B", "egrlf"])
    assert out.loc["C", ["epfwd", "egrsf", "egrlf"]].isna().all()
    assert np.isfinite(out.at["A", "epfwd"])  # a negative forward EP is kept


# TC-AND-003
def test_tc_and_003_pit_and_dtypes() -> None:
    cons = build_consensus([("20260630", "A", 2026, 100.0, 120.0, 144.0),
                            ("20260731", "A", 2026, 50.0, 60.0, 72.0)])  # fmt: skip
    keys = pd.DataFrame({"trade_date": ["20260715", "20260803"], "ts_code": ["A", "A"],
                         "total_mv": [1000.0, 1000.0]})  # fmt: skip
    out = AnalystDescriptors().compute(keys, cons)
    first = AnalystDescriptors().compute(keys, cons.iloc[:1])
    assert out.loc[0, "epfwd"] == pytest.approx(first.loc[0, "epfwd"])
    assert out.loc[1, "epfwd"] < out.loc[0, "epfwd"]
    mixed = keys.assign(ts_code=keys["ts_code"].astype(pd.StringDtype(na_value=np.nan)))
    same = AnalystDescriptors().compute(
        mixed, cons.assign(ts_code=cons["ts_code"].astype("string"))
    )
    assert same["epfwd"].tolist() == pytest.approx(out["epfwd"].tolist())
    assert AnalystDescriptors().compute(keys, cons.iloc[0:0])["epfwd"].isna().all()
