"""Industry and size exposures of universe members (D-093): the neutralisation inputs."""

from __future__ import annotations

import pandas as pd

from quant_cn.core.frames import EXPOSURE_PANEL
from quant_cn.lake.lake_query import LakeQuery

_SQL = """
SELECT u.trade_date, u.ts_code, i.l1_code,
       CAST(coalesce(i.industry_backfilled, FALSE) AS DOUBLE) AS industry_backfilled,
       CASE WHEN b.total_mv > 0 THEN ln(b.total_mv * 1e4) END AS log_mcap
FROM derived.universe u
LEFT JOIN derived.industry_l1 i
  ON i.ts_code = u.ts_code AND coalesce(i.valid_from, '00000000') <= u.trade_date
 AND coalesce(i.valid_to, '99991231') >= u.trade_date
LEFT JOIN curated.daily_basic b ON b.ts_code = u.ts_code AND b.trade_date = u.trade_date
WHERE u.in_universe = 1 AND u.trade_date BETWEEN ? AND ?
ORDER BY u.trade_date, u.ts_code"""


class ExposureReader:
    """
    Purpose:
        Per universe member and session: the Shenwan L1 group in effect (derived.industry_l1,
        l1_grouping = the PIT row or the back-filled first-known L1, flagged; D-071, D-093) and
        log market cap (ln of total_mv in CNY, from daily_basic at the close of t). The inputs of
        FactorPreprocessor's neutralisation.

    Contract:
        Input:
            query: LakeQuery
        Output:
            instance; `read_exposures`
        Raises:
            (none at construction)

    Used by:
        (none yet)

    Test cases:
        TC-EXR-001  members only; L1 from the interval covering t with its backfilled flag;
                    log_mcap = ln(total_mv * 1e4); missing market value -> NaN
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def read_exposures(self, start: str, end: str) -> pd.DataFrame:
        """
        Purpose:
            Exposures of universe members in [start, end].

        Contract:
            Input:
                start, end: str  -- YYYYMMDD, inclusive
            Output:
                DataFrame  -- EXPOSURE_PANEL sorted by (trade_date, ts_code)
            Raises:
                LakeError  -- derived.universe / derived.industry_l1 / curated.daily_basic missing
        """
        raw = self._query.sql(_SQL, [start, end])
        return EXPOSURE_PANEL.validate(EXPOSURE_PANEL.normalize(raw, strict=True))
