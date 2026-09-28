from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.calculation.term_selector import TermSelector


# TC-TS-001
def test_tc_ts_001_select() -> None:
    day = pd.DataFrame(
        {
            "maturity_date": ["20260902", "20260923", "20261028", "20261223"],
            "days": [5, 26, 61, 117],
        }
    )
    assert TermSelector(7).list_terms(day) == ("20260923", "20261028")


# TC-TS-002
def test_tc_ts_002_not_enough() -> None:
    day = pd.DataFrame({"maturity_date": ["20260902", "20260923"], "days": [5, 26]})
    with pytest.raises(ValueError):
        TermSelector(7).list_terms(day)
