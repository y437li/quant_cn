from __future__ import annotations

import pandas as pd

from quant_cn.calculation.option_chain_builder import CHAIN_COLUMNS, OptionChainBuilder

BASIC = pd.DataFrame(
    {
        "ts_code": ["A", "B", "C"],
        "opt_code": ["OPX", "OPX", "OPX"],
        "name": ["X购9月3000", "X沽9月3000", "X购9月3050A"],
        "call_put": ["C", "P", "C"],
        "exercise_price": [3.0, 3.0, 3.05],
        "maturity_date": ["20260923"] * 3,
    }
)
DAILY = pd.DataFrame(
    {
        "ts_code": ["A", "B", "C", "Z"],
        "trade_date": ["20260828"] * 4,
        "close": [0.10, 0.0, 0.08, 1.0],
        "settle": [0.11, 0.07, 0.09, 1.0],
        "vol": [5.0, 0.0, 1.0, 1.0],
        "oi": [1.0, 1.0, 1.0, 1.0],
    }
)


# TC-OCB-001
def test_tc_ocb_001_join() -> None:
    chain = OptionChainBuilder().build_chain(BASIC, DAILY, "OPX")
    assert list(chain.columns) == CHAIN_COLUMNS
    assert sorted(chain["ts_code"]) == ["A", "B"] and set(chain["days"]) == {26}


# TC-OCB-002
def test_tc_ocb_002_adjusted() -> None:
    chain = OptionChainBuilder(exclude_adjusted=False).build_chain(BASIC, DAILY, "OPX")
    assert chain.loc[chain["ts_code"] == "C", "adjusted"].tolist() == [True]


# TC-OCB-003
def test_tc_ocb_003_quotes_fallback() -> None:
    builder = OptionChainBuilder()
    quotes, used_settle = builder.build_quotes(builder.build_chain(BASIC, DAILY, "OPX"))
    assert used_settle
    assert quotes.loc[3.0, ("price", "C")] == 0.10 and quotes.loc[3.0, ("price", "P")] == 0.07
