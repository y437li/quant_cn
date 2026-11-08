from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.factor.base_factor import FactorInputs
from quant_cn.factor.library.earnings_yield_factor import EarningsYieldFactor
from quant_cn.factor.library.profit_growth_factor import ProfitGrowthFactor
from quant_cn.factor.library.roe_factor import RoeFactor
from quant_cn.lake.lake_reader import LakeReader

MV = 50.0 * 1e4  # total_mv 50 (10k CNY) in CNY
DAYS = ["20260424", "20260427", "20260515", "20260518"]  # ann day, next session, restatement, next


def build_inputs(reader: LakeReader, fields: list[str]) -> FactorInputs:
    return FactorInputs(
        prices=reader.read_prices("20260401", "20260530", dense=True),
        fundamentals=reader.read_fundamentals_pit(fields, "20260401", "20260530"),
        daily_basic=reader.read_panel("daily_basic", "20260401", "20260530", columns=["total_mv"]),
    )


def get_value(frame: pd.DataFrame, day: str) -> float | None:
    rows = frame[frame["trade_date"] == day]["value"]
    return float(rows.iloc[0]) if len(rows) else None


# TC-EYF-001
def test_tc_eyf_001_earnings_yield(reader: LakeReader) -> None:
    out = EarningsYieldFactor("ep_ttm").compute(
        build_inputs(reader, ["n_income_attr_p_ttm"]), "20260401", "20260530"
    )
    assert get_value(out, DAYS[0]) == pytest.approx(
        100.0 / MV
    )  # Q1-26 not visible on its announcement day
    assert get_value(out, DAYS[1]) == pytest.approx((30 + 100 - 20) / MV)
    assert get_value(out, DAYS[2]) == pytest.approx(
        (30 + 100 - 20) / MV
    )  # restatement not visible yet
    assert get_value(out, DAYS[3]) == pytest.approx((30 + 120 - 20) / MV)


# TC-ROE-001
def test_tc_roe_001_roe(reader: LakeReader) -> None:
    fields = ["n_income_attr_p_ttm", "total_hldr_eqy_exc_min_int"]
    out = RoeFactor("roe_ttm").compute(build_inputs(reader, fields), "20260401", "20260530")
    assert (
        get_value(out, DAYS[0]) is None
    )  # equity first announced that day: visible the next session
    assert get_value(out, DAYS[1]) == pytest.approx(110.0 / 1000.0)
    assert get_value(out, DAYS[3]) == pytest.approx(130.0 / 1000.0)


# TC-PGF-001
def test_tc_pgf_001_profit_growth(reader: LakeReader) -> None:
    out = ProfitGrowthFactor("profit_growth_ttm").compute(
        build_inputs(reader, ["n_income_attr_p_ttm_yoy"]), "20260401", "20260530"
    )
    assert get_value(out, DAYS[0]) == pytest.approx(100.0 / 80.0 - 1)  # FY-25 vs FY-24
    assert get_value(out, DAYS[1]) == pytest.approx(110.0 / 90.0 - 1)  # TTM Q1-26 vs TTM Q1-25
    assert get_value(out, DAYS[3]) == pytest.approx(130.0 / 90.0 - 1)
