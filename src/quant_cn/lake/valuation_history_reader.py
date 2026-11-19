"""A stock's valuation against its own history (plan 21 ph4)."""

from __future__ import annotations

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery

COLUMNS = ["value", "median", "n_days"]
FIELDS = ("pb", "pe_ttm")
_SQL = """
SELECT ts_code, arg_max(coalesce({field}, 0), trade_date) AS value,
       median({field}) FILTER (WHERE {field} > 0) AS median,
       count(*) FILTER (WHERE {field} > 0) AS n_days
FROM curated.daily_basic
WHERE list_contains(?, ts_code) AND trade_date >= ? AND trade_date <= ?
GROUP BY 1
"""


class ValuationHistoryReader:
    """
    Purpose:
        For each stock, its latest pb or pe_ttm on or before `as_of` (0 when the vendor leaves
        it empty, i.e. a loss) and the median of its positive values over [start, as_of]
        (curated.daily_basic; losses and negative equity are left out of the median).

    Contract:
        Input:
            query: LakeQuery  -- curated.daily_basic
        Output:
            instance; `read(codes, field, start, as_of) -> DataFrame` indexed by ts_code with
            COLUMNS (value, median, n_days = positive sessions); median NaN without a
            positive value; a code without rows in the window is absent
        Raises:
            (none at construction)

    Used by:
        portfolio.OpportunityScreen  -- valuation rule
        cli.GaugeCommands            -- wires it

    Test cases:
        TC-VHR-001  latest value and the median of positive values over the window; rows after
                    as_of or before start are ignored; a latest loss gives value 0; unknown
                    field raises LakeError
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def read(self, codes: list[str], field: str, start: str, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Latest value and the median of positive values over [start, as_of] per code.

        Contract:
            Input:
                codes: list[str]; field: "pb" | "pe_ttm"; start, as_of: str YYYYMMDD
            Output:
                DataFrame  -- index ts_code, COLUMNS
            Raises:
                LakeError  -- unknown field or query failure
        """
        if field not in FIELDS:
            raise LakeError(f"valuation field must be one of {FIELDS}: {field!r}")
        frame = self._query.sql(_SQL.format(field=field), [codes, start, as_of])
        return frame.set_index("ts_code")[COLUMNS].astype(float)
