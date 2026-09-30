"""Append-only record of every variant evaluated in a campaign (FACTOR_TESTING_DESIGN §5)."""

from __future__ import annotations

import json
from collections.abc import Mapping

import pandas as pd

from quant_cn.core.frames import TRIAL_LOG


class TrialLog:
    """
    Purpose:
        Record every factor / parameter / horizon variant evaluated in a campaign, including the
        failures, because the deflated Sharpe ratio (Bailey & López de Prado 2014) and the
        multiple-testing adjusters need the number and dispersion of all trials, not just the
        winners. Append-only: trials get sequential ids and can never be edited or removed. No
        I/O: the caller persists `build_frame()` and resumes with `from_frame()`.

    Contract:
        Input:
            campaign: str  -- campaign id, e.g. "factor_campaign_01"
        Output:
            instance; `add_trial`, `find_trial`, `build_frame`, `from_frame`; `n_trials`
        Raises:
            ValueError  -- empty campaign id

    Used by:
        factor.FactorEvaluator  -- injected type or call

    Test cases:
        TC-TL-001  trials get sequential ids and appear in build_frame as TRIAL_LOG
        TC-TL-002  append-only: modifying a built frame does not change the log; no remove
        TC-TL-003  from_frame resumes numbering; a frame from another campaign raises
        TC-TL-004  find_trial returns the id of an identical variant, None otherwise
    """

    def __init__(self, campaign: str) -> None:
        if not campaign:
            raise ValueError("campaign id is empty")
        self._campaign = campaign
        self._rows: list[dict[str, object]] = []

    @property
    def n_trials(self) -> int:
        """
        Purpose:
            Number of trials recorded (N for the deflated Sharpe ratio).

        Contract:
            Input:
                (none)
            Output:
                int
            Raises:
                (none)
        """
        return len(self._rows)

    def add_trial(
        self,
        factor: str,
        params: Mapping[str, object],
        horizon: int,
        sr: float | None,
        ic_mean: float | None,
    ) -> str:
        """
        Purpose:
            Append one evaluated variant.

        Contract:
            Input:
                factor:  str                  -- factor name
                params:  Mapping[str, object] -- variant parameters (stored as sorted JSON)
                horizon: int >= 1             -- sessions
                sr:      float | None         -- per-period Sharpe of the traded variant
                ic_mean: float | None         -- mean IC
            Output:
                str  -- trial id "<campaign>-<n:05d>"
            Raises:
                TypeError  -- params not JSON-serialisable
        """
        trial_id = f"{self._campaign}-{len(self._rows) + 1:05d}"
        self._rows.append(
            {
                "campaign": self._campaign,
                "trial_id": trial_id,
                "factor": factor,
                "params": json.dumps(dict(params), sort_keys=True, default=str),
                "horizon": float(horizon),
                "sr": sr,
                "ic_mean": ic_mean,
            }
        )
        return trial_id

    def find_trial(self, factor: str, params: Mapping[str, object], horizon: int) -> str | None:
        """
        Purpose:
            The id of an already recorded identical variant (re-running a campaign does not
            inflate N).

        Contract:
            Input:
                factor: str; params: Mapping[str, object]; horizon: int
            Output:
                str | None  -- trial id, or None when this variant was never recorded
            Raises:
                TypeError  -- params not JSON-serialisable
        """
        key = json.dumps(dict(params), sort_keys=True, default=str)
        for row in self._rows:
            if (
                row["factor"] == factor
                and row["params"] == key
                and row["horizon"] == float(horizon)
            ):
                return str(row["trial_id"])
        return None

    def build_frame(self) -> pd.DataFrame:
        """
        Purpose:
            The log as a TRIAL_LOG frame (a copy).

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- TRIAL_LOG, in insertion order
            Raises:
                (none)
        """
        frame = pd.DataFrame(self._rows, columns=TRIAL_LOG.columns)
        return TRIAL_LOG.validate(TRIAL_LOG.normalize(frame, strict=True))

    @classmethod
    def from_frame(cls, campaign: str, frame: pd.DataFrame) -> TrialLog:
        """
        Purpose:
            Resume a campaign's log from a saved TRIAL_LOG frame.

        Contract:
            Input:
                campaign: str; frame: DataFrame  -- TRIAL_LOG of that campaign
            Output:
                TrialLog  -- next trial continues the numbering
            Raises:
                ValueError  -- rows of another campaign
                SchemaError -- frame is not TRIAL_LOG
        """
        rows = TRIAL_LOG.validate(TRIAL_LOG.normalize(frame, strict=True))
        if (rows["campaign"] != campaign).any():
            raise ValueError(f"frame holds trials of another campaign than {campaign!r}")
        log = cls(campaign)
        log._rows = [{str(k): v for k, v in r.items()} for r in rows.to_dict("records")]
        return log
