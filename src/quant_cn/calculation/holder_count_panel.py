"""Quarter-end shareholder counts: change labels and point-in-time lags (plan 21 ph2-3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.lake.lake_query import LakeQuery

_HOLDERS = """
SELECT ts_code, end_date, arg_max(holder_num, ann_date) AS n, min(ann_date) AS ann
FROM curated.stk_holdernumber
WHERE holder_num > 0 AND substr(end_date, 5, 4) IN ('0331', '0630', '0930', '1231')
  AND ann_date <= ?
GROUP BY 1, 2
"""
_QUARTER_DAYS = ("0331", "0630", "0930", "1231")
_NEVER = "99999999"  # announcement date of a quarter never announced


class HolderCountPanel:
    """
    Purpose:
        Quarter-end shareholder counts from curated.stk_holdernumber (plan 21, D-142): the
        change y = ln(holders_q / holders_{q-1}) with the first announcement date of q
        (ann_y), and the point-in-time lags prev (change of q-1) and prev2 (change of q-2),
        each NaN unless that quarter was announced on or before the row's as-of session.
        A restated count keeps the latest value; the announcement date is the first one.

    Contract:
        Input:
            query: LakeQuery  -- curated.stk_holdernumber
        Output:
            instance; `load(end)`; `compute_labels(rows)`, `compute_lags(rows)` -> DataFrame
            aligned with rows (rows: ts_code, q (quarter end YYYYMMDD), as_of (YYYYMMDD));
            `get_quarter_before(q, k)` (static)
        Raises:
            LakeError  -- curated.stk_holdernumber missing

    Used by:
        calculation.RetailGaugeNowcaster  -- labels of quarter-end rows
        cli.GaugeCommands  -- wires it
        calculation.RetailGaugeFeatureBuilder  -- prev / prev2 features

    Test cases:
        TC-HCP-001  compute_labels: ln change from the previous quarter end, ann_y = first
                    announcement; a missing previous quarter -> NaN
        TC-HCP-002  compute_lags: prev / prev2 visible only when announced on or before
                    as_of (one day later -> NaN); get_quarter_before across a year end
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query
        self._chg = pd.DataFrame(columns=["ts_code", "end_date", "chg", "ann"])

    def load(self, end: str) -> None:
        """
        Purpose:
            Read the counts announced on or before `end` and compute each quarter's change.

        Contract:
            Input:
                end: str  -- YYYYMMDD
            Output:
                None (state)
            Raises:
                LakeError  -- query failure
        """
        h = self._query.sql(_HOLDERS, [end])
        h["ts_code"] = h["ts_code"].astype(str)
        h["end_date"] = h["end_date"].astype(str)
        prev = h[["ts_code", "end_date", "n"]].rename(columns={"n": "n_prev"})
        prev["end_date"] = prev["end_date"].map(lambda q: self.get_quarter_before(q, -1))
        h = h.merge(prev, on=["ts_code", "end_date"], how="left")
        h["chg"] = np.log(h["n"] / h["n_prev"])
        self._chg = h[["ts_code", "end_date", "chg", "ann"]]

    def compute_labels(self, rows: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Label of each row's quarter q: y and ann_y.

        Contract:
            Input:
                rows: DataFrame  -- ts_code, q
            Output:
                DataFrame  -- y, ann_y (NaN / None when q is not announced), rows' index
            Raises:
                (none)
        """
        keys = rows[["ts_code", "q"]].rename(columns={"q": "end_date"})
        out = keys.merge(self._chg, on=["ts_code", "end_date"], how="left")
        return pd.DataFrame(
            {"y": out["chg"].to_numpy(), "ann_y": out["ann"].to_numpy()}, index=rows.index
        )

    def compute_lags(self, rows: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            prev / prev2: changes of the quarters q-1 and q-2, point in time at as_of.

        Contract:
            Input:
                rows: DataFrame  -- ts_code, q, as_of
            Output:
                DataFrame  -- prev, prev2, rows' index
            Raises:
                (none)
        """
        out = pd.DataFrame(index=rows.index)
        for k, name in ((1, "prev"), (2, "prev2")):
            keys = pd.DataFrame(
                {
                    "ts_code": rows["ts_code"].to_numpy(),
                    "end_date": [self.get_quarter_before(q, k) for q in rows["q"]],
                }
            )
            hit = keys.merge(self._chg, on=["ts_code", "end_date"], how="left")
            ann = hit["ann"].astype("string").fillna(_NEVER).to_numpy(dtype=object)
            seen = ann <= rows["as_of"].astype("string").to_numpy(dtype=object)
            out[name] = np.where(seen, hit["chg"].to_numpy(), np.nan)
        return out

    @staticmethod
    def get_quarter_before(q: str, k: int) -> str:
        """
        Purpose:
            The quarter end k quarters before q.

        Contract:
            Input:
                q: str  -- quarter end YYYYMMDD; k: int >= 0
            Output:
                str  -- quarter end YYYYMMDD
            Raises:
                ValueError  -- q is not a quarter end
        """
        n = int(q[:4]) * 4 + _QUARTER_DAYS.index(q[4:]) - k
        return f"{n // 4}{_QUARTER_DAYS[n % 4]}"
