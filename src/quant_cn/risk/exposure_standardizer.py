"""Descriptors -> standardised style and industry exposures, CNE5 recipe (plan 05 phase 2)."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from quant_cn.core.frames import RISK_EXPOSURE
from quant_cn.core.risk_model_settings import RiskModelSettings, StyleSpec
from quant_cn.statistic.neutralizer import Neutralizer
from quant_cn.statistic.standardizer import Standardizer

logger = logging.getLogger(__name__)

INDUSTRY_PREFIX = "ind_"
MIN_FILL_NAMES = 30
MAX_CLIP_ROUNDS = 20
CLIP_TOLERANCE = 0.05


class ExposureStandardizer:
    """
    Purpose:
        Turn the descriptor table into RISK_EXPOSURE, per session: each descriptor is
        standardised (circ_mv-weighted mean 0, equal-weighted sd 1), then clipped at
        +-winsor_sd and standardised again until no value exceeds the bound (at most 20
        rounds); a style is the weighted mean of its descriptors' z-scores (weights renormalised
        over the descriptors a stock has), restandardised and clipped, then orthogonalised to
        its configured styles (OLS residual, Neutralizer) and restandardised; a style with raw
        coverage below `min_coverage` of the session's names is dropped for that session.
        Missing exposures of a kept style are filled with the prediction of an OLS of the style
        on Shenwan L1 dummies and size (is_filled = 1). Industry rows: factor "ind_<l1_code>",
        exposure 1, is_filled = industry_backfilled (D-071). Monitor styles (D-130) are built
        the same way after the model styles.

    Contract:
        Input:
            settings: RiskModelSettings; standardizer: Standardizer; neutralizer: Neutralizer
        Output:
            instance; `compute(descriptors) -> DataFrame (RISK_EXPOSURE)`
        Raises:
            (none at construction)

    Used by:
        risk.RiskModel  -- exposures step
        risk.RiskModelFactory  -- injected type or call

    Test cases:
        TC-EXS-001  every kept style has circ_mv-weighted mean 0 and sd ~1 per session before
                   filling, and |exposure| <= winsor_sd + tolerance
        TC-EXS-002  an orthogonalised style has zero sample covariance with its targets
        TC-EXS-003  a missing descriptor renormalises the weights; a missing style is filled from
                   industry and size and flagged; a style under min_coverage is dropped
        TC-EXS-004  one industry row per stock with exposure 1; output validates RISK_EXPOSURE
    """

    def __init__(
        self, settings: RiskModelSettings, standardizer: Standardizer, neutralizer: Neutralizer
    ) -> None:
        self._settings = settings
        self._standardizer = standardizer
        self._neutralizer = neutralizer

    def compute(self, descriptors: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Style and industry exposures for every row of the descriptor table.

        Contract:
            Input:
                descriptors: DataFrame  -- DescriptorBuilder.compute output (any subset of
                                           descriptor columns; missing ones count as NaN)
            Output:
                DataFrame  -- RISK_EXPOSURE sorted by key: styles (exposure_raw = the weighted
                              descriptor z-score mean, or the raw descriptor for one-descriptor
                              styles) and industries; no NaN exposure
            Raises:
                KeyError  -- base columns missing
        """
        base = descriptors[["trade_date", "ts_code", "l1_code", "circ_mv"]].copy()
        styles = base.copy()
        raws: dict[str, pd.Series] = {}
        specs = [*self._settings.styles, *self._settings.monitor_styles]
        for spec in specs:
            raw, z = self._compute_style(descriptors, spec)
            raws[spec.name] = raw
            styles[spec.name] = z
            if spec.orthogonalize_to:
                styles[spec.name] = self._compute_orthogonal(styles, spec)
        long = [self._build_filled(styles, raws, spec.name) for spec in specs]
        long.append(self._build_industry(descriptors))
        out = pd.concat(long, ignore_index=True).sort_values(["trade_date", "ts_code", "factor"])
        out = out.reset_index(drop=True)
        return RISK_EXPOSURE.validate(RISK_EXPOSURE.normalize(out, strict=True))

    def _compute_style(self, frame: pd.DataFrame, spec: StyleSpec) -> tuple[pd.Series, pd.Series]:
        weighted, weights = pd.Series(0.0, index=frame.index), pd.Series(0.0, index=frame.index)
        single = None
        for name, weight in spec.descriptors.items():
            raw = frame[name] if name in frame else pd.Series(np.nan, index=frame.index)
            single = raw if len(spec.descriptors) == 1 else None
            z = self._compute_clipped_z(frame, raw.replace([np.inf, -np.inf], np.nan))
            weighted += (z * weight).fillna(0.0)
            weights += z.notna() * weight
        combined = (weighted / weights).where(weights > 0)
        coverage = combined.notna().groupby(frame["trade_date"]).transform("mean")
        combined = combined.where(coverage >= self._settings.min_coverage)
        raw_out = single if single is not None else combined
        return raw_out.where(combined.notna()), self._compute_clipped_z(frame, combined)

    def _compute_clipped_z(self, frame: pd.DataFrame, values: pd.Series) -> pd.Series:
        """z-score, then clip at +-winsor_sd and re-standardise until no value exceeds the bound."""
        work = pd.DataFrame({"trade_date": frame["trade_date"], "v": values, "w": frame["circ_mv"]})
        clip = self._settings.winsor_sd
        z = self._standardizer.compute(work, column="v", weight_column="w")["v"]
        for _ in range(MAX_CLIP_ROUNDS):
            if not (z.abs() > clip + CLIP_TOLERANCE).any():
                break
            z = self._standardizer.compute(
                work.assign(v=z.clip(-clip, clip)), column="v", weight_column="w"
            )["v"]
        return z

    def _compute_orthogonal(self, styles: pd.DataFrame, spec: StyleSpec) -> pd.Series:
        resid = self._neutralizer.compute(styles, column=spec.name, numeric=spec.orthogonalize_to)[
            spec.name
        ]
        return self._compute_clipped_z(styles, resid)

    def _build_filled(
        self, styles: pd.DataFrame, raws: dict[str, pd.Series], name: str
    ) -> pd.DataFrame:
        value = styles[name].copy()
        filled = pd.Series(0.0, index=styles.index)
        size = styles["size"] if "size" in styles and name != "size" else None
        for _, part in styles.groupby("trade_date"):
            missing = part[name].isna()
            if not missing.any() or missing.all() or (~missing).sum() < MIN_FILL_NAMES:
                continue
            design = self._build_design(part, size)
            known = missing.to_numpy() == False  # noqa: E712 -- numpy bool mask
            ok = known & np.isfinite(design).all(axis=1)
            coef, *_ = np.linalg.lstsq(design[ok], part[name].to_numpy()[ok], rcond=None)
            target = missing.to_numpy() & np.isfinite(design).all(axis=1)
            value.loc[part.index[target]] = design[target] @ coef
            filled.loc[part.index[target]] = 1.0
        out = styles[["trade_date", "ts_code"]].assign(
            factor=name, exposure=value, exposure_raw=raws[name], is_filled=filled
        )
        return out.dropna(subset=["exposure"])

    @staticmethod
    def _build_design(part: pd.DataFrame, size: pd.Series | None) -> np.ndarray:
        dummies = pd.get_dummies(part["l1_code"], dtype=float).to_numpy()
        columns = [dummies]
        if size is not None:
            columns.append(size.loc[part.index].to_numpy(float)[:, None])
        return np.hstack(columns)

    @staticmethod
    def _build_industry(descriptors: pd.DataFrame) -> pd.DataFrame:
        rows = descriptors.dropna(subset=["l1_code"])
        return pd.DataFrame(
            {
                "trade_date": rows["trade_date"],
                "ts_code": rows["ts_code"],
                "factor": INDUSTRY_PREFIX + rows["l1_code"].astype(str),
                "exposure": 1.0,
                "exposure_raw": 1.0,
                "is_filled": rows["industry_backfilled"].astype(float),
            }
        )
