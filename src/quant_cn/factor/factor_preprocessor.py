"""Winsorise, standardise and neutralise factor values per date (SRC_DESIGN §2.5, D-093)."""

from __future__ import annotations

import logging

import pandas as pd

from quant_cn.core.frames import EXPOSURE_PANEL, FACTOR_PANEL
from quant_cn.statistic.neutralizer import Neutralizer
from quant_cn.statistic.standardizer import Standardizer
from quant_cn.statistic.winsorizer import Winsorizer

logger = logging.getLogger(__name__)
KEY = ["trade_date", "ts_code", "factor"]


class FactorPreprocessor:
    """
    Purpose:
        The ordered chain applied to every raw factor, each step optional and logged: winsorise
        (median +- k * 1.4826 * MAD per date) -> standardise (z per date) -> neutralise (per-date
        OLS residual on Shenwan L1 dummies and log market cap, D-093) -> standardise again, so the
        processed value is a unit-dispersion, industry- and size-neutral z-score. `value_raw` is
        kept; `value` holds the result. Rows without exposures are dropped when neutralising.

    Contract:
        Input:
            winsorizer:  Winsorizer | None    -- None skips winsorising
            standardizer: Standardizer | None -- None skips both standardisations
            neutralizer: Neutralizer | None   -- None skips neutralising
        Output:
            instance; `compute`, `build_log`
        Raises:
            (none at construction)

    Used by:
        pipeline.FeatureStep  -- injected type or call
        cli.ServiceBuilder    -- injected type or call

    Test cases:
        TC-FPP-001  full chain: per date and factor mean 0, sd 1, zero correlation with log mcap
                    and with each industry; value_raw untouched
        TC-FPP-002  steps can be skipped; build_log records rows in/out per step and the share of
                    back-filled industry rows
    """

    def __init__(
        self,
        winsorizer: Winsorizer | None,
        standardizer: Standardizer | None,
        neutralizer: Neutralizer | None,
    ) -> None:
        self._winsorizer = winsorizer
        self._standardizer = standardizer
        self._neutralizer = neutralizer
        self._log: list[dict[str, object]] = []

    def compute(self, factors: pd.DataFrame, exposures: pd.DataFrame | None = None) -> pd.DataFrame:
        """
        Purpose:
            Processed FACTOR_PANEL.

        Contract:
            Input:
                factors:   DataFrame         -- FACTOR_PANEL (value = value_raw from BaseFactor)
                exposures: DataFrame | None  -- EXPOSURE_PANEL; required when neutralising
            Output:
                DataFrame  -- FACTOR_PANEL, value processed, sorted by key
            Raises:
                ValueError  -- neutralising without exposures
                SchemaError -- inputs not FACTOR_PANEL / EXPOSURE_PANEL
        """
        frame = FACTOR_PANEL.validate(factors).copy()
        self._log = []
        grouped_key = frame["trade_date"] + "|" + frame["factor"]
        frame = frame.assign(_group=grouped_key)
        if self._winsorizer is not None:
            frame = self._winsorizer.compute(frame, "value", by="_group")
            self._record("winsorize", frame)
        if self._standardizer is not None:
            frame = self._standardizer.compute(frame, "value", by="_group")
            self._record("standardize", frame)
        if self._neutralizer is not None:
            frame = self._compute_neutral(frame, exposures)
        out = frame.dropna(subset=["value"])[FACTOR_PANEL.columns].sort_values(KEY)
        logger.info("preprocessed %s rows over %s dates", len(out), out["trade_date"].nunique())
        return FACTOR_PANEL.validate(
            FACTOR_PANEL.normalize(out.reset_index(drop=True), strict=True)
        )

    def build_log(self) -> pd.DataFrame:
        """
        Purpose:
            What the last compute did.

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- step, rows, value (non-NaN rows after the step; for backfilled_share
                              the share of rows whose industry is back-filled)
            Raises:
                (none)
        """
        return pd.DataFrame(self._log, columns=["step", "rows", "value"])

    def _compute_neutral(self, frame: pd.DataFrame, exposures: pd.DataFrame | None) -> pd.DataFrame:
        if self._neutralizer is None:
            return frame
        if exposures is None:
            raise ValueError("neutralising needs an exposure panel")
        exp = EXPOSURE_PANEL.validate(exposures)
        frame = frame.merge(
            exp[["trade_date", "ts_code", "l1_code", "industry_backfilled", "log_mcap"]],
            on=["trade_date", "ts_code"],
            how="inner",
        )
        self._log.append(
            {
                "step": "backfilled_share",
                "rows": len(frame),
                "value": float(frame["industry_backfilled"].mean()) if len(frame) else 0.0,
            }
        )
        frame = self._neutralizer.compute(frame, "value", ["l1_code"], ["log_mcap"], by="_group")
        self._record("neutralize", frame)
        if self._standardizer is not None:
            frame = self._standardizer.compute(frame, "value", by="_group")
            self._record("restandardize", frame)
        return frame

    def _record(self, step: str, frame: pd.DataFrame) -> None:
        self._log.append(
            {"step": step, "rows": len(frame), "value": float(frame["value"].notna().sum())}
        )
