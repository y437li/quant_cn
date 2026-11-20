"""Position-to-stock look-through for the holdings risk model: ETFs as index baskets (ph7q)."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from quant_cn.core.positions_book import Position
from quant_cn.lake.lake_query import LakeQuery

_WEIGHTS = """
SELECT index_code, con_code AS ts_code, weight FROM curated.index_weight w
WHERE list_contains(?, index_code) AND trade_date = (
    SELECT max(trade_date) FROM curated.index_weight
    WHERE index_code = w.index_code AND trade_date <= ?)
"""


class LookThroughWeights:
    """
    Purpose:
        Map each position to the stocks the risk model covers: a stock is itself, an ETF with
        `tracks` is its index's constituents at the latest index weights on or before the
        session, renormalised over the covered names. Positions that resolve to no covered
        stock are left out (the caller lists them as missing).

    Contract:
        Input:
            query: LakeQuery  -- curated.index_weight
        Output:
            instance; `build(positions, session, universe)` -> DataFrame
        Raises:
            (none at construction)

    Used by:
        portfolio.HoldingsRiskBuilder  -- stock weights and position covariance for ETFs
        cli.AppServiceBuilder          -- wires it into the holdings risk builder

    Test cases:
        TC-LTW-001  a covered stock row is 1 on itself; an uncovered stock is left out
        TC-LTW-002  an ETF row is its index weights renormalised over covered names (sums
                    to 1), from the latest weights on or before the session only
        TC-LTW-003  an ETF without `tracks` or without index weights is left out; no positions
                    -> empty frame with the universe as columns
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def build(
        self, positions: Sequence[Position], session: str, universe: pd.Index
    ) -> pd.DataFrame:
        """
        Purpose:
            The look-through matrix, rows = position codes, columns = covered stocks.

        Contract:
            Input:
                positions: Sequence[Position]  -- the book
                session:   str       -- YYYYMMDD; index weights dated <= session
                universe:  pd.Index  -- ts_codes the risk model covers
            Output:
                DataFrame  -- one row per resolvable position, each row sums to 1, columns =
                              universe; zeros elsewhere
            Raises:
                (none)
        """
        baskets = self._read_baskets([p.tracks for p in positions if p.tracks], session)
        rows: dict[str, pd.Series] = {}
        for p in positions:
            if p.tracks:
                basket = baskets.get(p.tracks, pd.Series(dtype=float))
                basket = basket[basket.index.isin(universe)]
                if basket.sum() > 0:
                    rows[p.code] = basket / basket.sum()
            elif p.code in universe:
                rows[p.code] = pd.Series({p.code: 1.0})
        frame = pd.DataFrame(rows).T.reindex(columns=universe).fillna(0.0)
        return frame.astype(float)

    def _read_baskets(self, indices: list[str], session: str) -> dict[str, pd.Series]:
        if not indices or not self._query.has_view("curated.index_weight"):
            return {}
        rows = self._query.sql(_WEIGHTS, [sorted(set(indices)), session])
        return {
            str(code): group.groupby("ts_code")["weight"].sum().astype(float)
            for code, group in rows.groupby("index_code")
        }
