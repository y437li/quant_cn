"""Statement values as known on a date: the latest (or first) announced version per period."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.ticker_alias_map import TickerAliasMap

logger = logging.getLogger(__name__)

VIEW = "derived.fundamentals_long"
COLUMNS = ["ts_code", "end_date", "field", "value"]
_SQL = f"""
SELECT ts_code, end_date, field, arg_max(value, known_on) AS value
FROM {VIEW}
WHERE known_on <= ? AND end_date >= ? AND list_contains(?, field)
GROUP BY ts_code, end_date, field
ORDER BY ts_code, end_date, field
"""
FIRST_COLUMNS = ["ts_code", "end_date", "field", "value", "known_on"]
# first version announced per key; same-day versions resolved by the highest update_flag
_FIRST_SQL = f"""
SELECT ts_code, end_date, field, value, known_on
FROM {VIEW}
WHERE known_on <= ? AND end_date >= ? AND list_contains(?, field)
QUALIFY row_number() OVER (PARTITION BY ts_code, end_date, field
                           ORDER BY known_on, update_flag DESC NULLS LAST) = 1
ORDER BY ts_code, end_date, field
"""


class StatementVersionReader:
    """
    Purpose:
        Read every company's statement values as they were known on one date: for each
        (company, period, field) the version with the latest known_on <= as_of (D-092 versions,
        ann_date PIT), or the first version ever announced (guidance outcomes, D-124). Retired
        codes are mapped to their surviving codes (new code wins).

    Contract:
        Input:
            query:     LakeQuery       -- reads derived.fundamentals_long
            alias_map: TickerAliasMap  -- retired -> surviving codes
            codec:     DateCodec
        Output:
            instance; `read_versions(fields, as_of, start) -> DataFrame[COLUMNS]`;
            `read_first_versions(fields, as_of, start) -> DataFrame[FIRST_COLUMNS]`
        Raises:
            (none at construction)

    Used by:
                       pipeline.GuidanceStep feeds calculation.ForecastTracker (plan 18 ph6)
        risk.RiskInputLoader  -- injected type or call
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-SVR-001  the latest version known on as_of wins; later announcements are ignored
        TC-SVR-002  periods before start and fields not asked for are left out
        TC-SVR-003  statements filed under a retired code come back under the surviving code
        TC-SVR-004  missing view or malformed dates raise LakeError
        TC-SVR-005  read_first_versions: the first announced version with its known_on; a
                    restatement does not replace it; versions after as_of are not seen
    """

    def __init__(self, query: LakeQuery, alias_map: TickerAliasMap, codec: DateCodec) -> None:
        self._query = query
        self._alias = alias_map
        self._codec = codec

    def read_versions(self, fields: Sequence[str], as_of: str, start: str) -> pd.DataFrame:
        """
        Purpose:
            Statement values per (company, period, field) as known on `as_of`.

        Contract:
            Input:
                fields: Sequence[str]  -- fundamentals_long field names, e.g. "revenue"
                as_of:  str            -- YYYYMMDD; versions with known_on <= as_of
                start:  str            -- YYYYMMDD; periods with end_date >= start
            Output:
                DataFrame  -- COLUMNS, key (ts_code, end_date, field) unique, sorted by key
            Raises:
                LakeError  -- view missing, malformed dates, query failure
        """
        try:
            self._codec.validate(as_of)
            self._codec.validate(start)
        except ValueError as exc:
            raise LakeError(f"dates must be YYYYMMDD: {as_of!r}, {start!r}") from exc
        if not self._query.has_view(VIEW):
            raise LakeError(f"{VIEW} missing: run make curate")
        raw = self._query.sql(_SQL, [as_of, start, list(fields)])
        frame = self._alias.normalize_codes(raw, ["ts_code", "end_date", "field"])
        logger.info("statement versions %s: %d rows", as_of, len(frame))
        return frame[COLUMNS].reset_index(drop=True)

    def read_first_versions(self, fields: Sequence[str], as_of: str, start: str) -> pd.DataFrame:
        """
        Purpose:
            The first announced value per (company, period, field) known on `as_of`, with the
            date it became known, so outcomes are scored against what was first reported, never
            a later restatement (D-124).

        Contract:
            Input:
                fields: Sequence[str]  -- fundamentals_long field names, e.g. "n_income_attr_p"
                as_of:  str            -- YYYYMMDD; versions with known_on <= as_of
                start:  str            -- YYYYMMDD; periods with end_date >= start
            Output:
                DataFrame  -- FIRST_COLUMNS, key (ts_code, end_date, field) unique, sorted by key;
                              known_on = announcement date of that first version
            Raises:
                LakeError  -- view missing, malformed dates, query failure
        """
        try:
            self._codec.validate(as_of)
            self._codec.validate(start)
        except ValueError as exc:
            raise LakeError(f"dates must be YYYYMMDD: {as_of!r}, {start!r}") from exc
        if not self._query.has_view(VIEW):
            raise LakeError(f"{VIEW} missing: run make curate")
        raw = self._query.sql(_FIRST_SQL, [as_of, start, list(fields)])
        frame = self._alias.normalize_codes(raw, ["ts_code", "end_date", "field"])
        logger.info("first statement versions %s: %d rows", as_of, len(frame))
        return frame[FIRST_COLUMNS].reset_index(drop=True)
