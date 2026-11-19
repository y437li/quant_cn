"""CNE5 analyst descriptors EPFWD, EGRSF, EGRLF from the consensus panel (plan 37)."""

from __future__ import annotations

import numpy as np
import pandas as pd

ANALYST_COLUMNS = ("epfwd", "egrsf", "egrlf")
MONTHS = 12
FY1_END_MONTH = 12  # A-share fiscal years end in December


class AnalystDescriptors:
    """
    Purpose:
        The CNE5 analyst descriptors per stock and session (plan 37), from the latest consensus
        reading on or before the session (ConsensusPanelBuilder month ends, notes visible from
        the session after their report date):
        - EPFWD = forward 12-month earnings / total market value, the forward earnings being
          w x FY1 + (1 - w) x FY2 with w = whole months left in FY1 after the session's month / 12
          (0 once FY1 has ended, as in January to April);
        - EGRSF = FY2 / FY1 - 1;
        - EGRLF = (FY3 / FY1)^(1/2) - 1, the longest horizon the consensus covers.
        Growth needs FY1 > 0 (and FY3 > 0 for EGRLF); EPFWD may be negative. Forecasts and
        total_mv are both in 10k CNY. A stock without a consensus gets NaN (its style weights
        are renormalised later, ExposureStandardizer).

    Contract:
        Input:
            (none)
        Output:
            instance; `compute(keys, consensus) -> DataFrame`
        Raises:
            (none at construction)

    Used by:
        risk.DescriptorBuilder  -- analyst columns of the descriptor table
        risk.RiskModelFactory  -- injected into DescriptorBuilder

    Test cases:
        TC-AND-001  known answers: EPFWD blend by months left (a session in March 2027 with
                    FY1 = 2026 uses FY2 only; in July 2026 w = 5/12), EGRSF, EGRLF
        TC-AND-002  FY1 <= 0 -> no EGRSF / EGRLF; FY3 <= 0 -> no EGRLF; no consensus -> NaN
        TC-AND-003  each session takes the last reading on or before it (a later reading does
                    not change earlier sessions); string dtypes of the keys may differ
    """

    def compute(self, keys: pd.DataFrame, consensus: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            EPFWD, EGRSF, EGRLF for every (trade_date, ts_code) of keys.

        Contract:
            Input:
                keys:      DataFrame  -- trade_date, ts_code, total_mv (10k CNY)
                consensus: DataFrame  -- CONSENSUS_COLUMNS (possibly empty)
            Output:
                DataFrame  -- trade_date, ts_code, epfwd, egrsf, egrlf in keys' order
            Raises:
                (none)
        """
        out = keys[["trade_date", "ts_code"]].copy()
        if consensus.empty or keys.empty:
            return out.assign(**{c: np.nan for c in ANALYST_COLUMNS})
        left = keys.assign(
            k=keys["trade_date"].astype(str).astype(int), ts_code=keys["ts_code"].astype(str)
        )
        left = left.reset_index(names="row").sort_values("k")
        right = consensus.assign(k=consensus["trade_date"].astype(str).astype(int),
                                 ts_code=consensus["ts_code"].astype(str))  # fmt: skip
        right = right.drop(columns="trade_date").sort_values("k")
        j = pd.merge_asof(left, right, on="k", by="ts_code", direction="backward")
        j = j.sort_values("row")
        np1, np2, np3 = (j[c].to_numpy(float) for c in ("np1", "np2", "np3"))
        month = (j["k"].to_numpy() // 100 % 100).astype(float)
        year = (j["k"].to_numpy() // 10000).astype(float)
        fy1 = j["fy1"].to_numpy(float)
        left_months = np.clip((fy1 - year) * MONTHS + (FY1_END_MONTH - month), 0, MONTHS)
        w = left_months / MONTHS
        fwd = np.where(w > 0, w * np1 + (1 - w) * np2, np2)
        mv = j["total_mv"].where(j["total_mv"] > 0).to_numpy(float)
        pos1 = np1 > 0
        with np.errstate(divide="ignore", invalid="ignore"):
            out["epfwd"] = fwd / mv
            out["egrsf"] = np.where(pos1, np2 / np1 - 1, np.nan)
            out["egrlf"] = np.where(pos1 & (np3 > 0), np.sqrt(np3 / np1) - 1, np.nan)
        return out
