"""LightGBM ranking model of the RetailGauge: build, score, save, load (plan 21 ph3, D-142)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import lightgbm as lgb
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings

_BOOSTER = "model.txt"
_META = "meta.json"


class RetailGaugeModel:
    """
    Purpose:
        The v5 RetailGauge model (D-142): missing features are filled with the training
        medians, every feature becomes its percentile rank within its quarter (training) or
        within the scored set (prediction), and a LightGBM regressor learns the within-quarter
        percentile rank of y = ln(holders_q / holders_{q-1}). `compute_pct` returns the
        percentile rank of the model score among the scored rows (pct, 1 = retail entering
        most). Saved as a LightGBM text model plus a JSON of features and medians.

    Contract:
        Input:
            settings: RetailGaugeSettings  -- model params, label_abs_max
        Output:
            instance; `build(rows, features)`, `compute_pct(rows)` -> Series pct in (0, 1];
            `save(folder)`, `load(folder)`; `is_fitted`
        Raises:
            LakeError  -- compute_pct / save before build, or an unreadable saved model

    Used by:
        cli.GaugeCommands  -- model factory
        calculation.RetailGaugeNowcaster  -- training and daily readings

    Test cases:
        TC-RGMD-001  build on a synthetic panel where one feature drives y: predicted pct ranks
                     follow that feature (rank corr > 0.9); |y| >= label_abs_max rows dropped
        TC-RGMD-002  save / load round trip gives identical scores; compute_pct before build
                     raises LakeError
    """

    def __init__(self, settings: RetailGaugeSettings) -> None:
        self._s = settings
        self._booster: lgb.Booster | None = None
        self._features: list[str] = []
        self._medians: dict[str, float] = {}

    @property
    def is_fitted(self) -> bool:
        """
        Purpose:
            Whether build or load has run.

        Contract:
            Input:
                (none)
            Output:
                bool
            Raises:
                (none)
        """
        return self._booster is not None

    def build(self, rows: pd.DataFrame, features: Sequence[str]) -> None:
        """
        Purpose:
            Train on labelled quarter-end rows.

        Contract:
            Input:
                rows:     DataFrame  -- q, y and the features; rows with NaN y or
                                        |y| >= label_abs_max are dropped
                features: Sequence[str]
            Output:
                None (state)
            Raises:
                LakeError  -- no usable rows
        """
        tr = rows[rows["y"].notna() & (rows["y"].abs() < self._s.label_abs_max)].copy()
        if tr.empty:
            raise LakeError("RetailGaugeModel: no labelled rows to train on")
        self._features = list(features)
        med = tr[self._features].median()
        self._medians = {str(k): float(v) for k, v in med.items()}
        x = tr[self._features].fillna(med).groupby(tr["q"]).rank(pct=True)
        target = tr.groupby("q")["y"].rank(pct=True)
        params: dict[str, Any] = dict(self._s.model)
        model = lgb.LGBMRegressor(verbose=-1, random_state=0, **params)
        model.fit(x, target)
        self._booster = model.booster_

    def compute_pct(self, rows: pd.DataFrame) -> pd.Series:
        """
        Purpose:
            Percentile rank of the model score among `rows`.

        Contract:
            Input:
                rows: DataFrame  -- the model's features (missing columns count as NaN)
            Output:
                Series  -- pct in (0, 1], rows' index
            Raises:
                LakeError  -- not fitted
        """
        if self._booster is None:
            raise LakeError("RetailGaugeModel: compute_pct before build")
        x = rows.reindex(columns=self._features).astype(float)
        x = x.fillna(pd.Series(self._medians)).rank(pct=True)
        score = pd.Series(self._booster.predict(x), index=rows.index)
        return score.rank(pct=True)

    def save(self, folder: Path) -> None:
        """
        Purpose:
            Write the booster and the feature medians to folder.

        Contract:
            Input:
                folder: Path  -- created if missing
            Output:
                None
            Raises:
                LakeError  -- not fitted or write failed
        """
        if self._booster is None:
            raise LakeError("RetailGaugeModel: save before build")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            self._booster.save_model(str(folder / _BOOSTER))
            meta = {"features": self._features, "medians": self._medians}
            (folder / _META).write_text(json.dumps(meta), encoding="utf-8")
        except OSError as exc:
            raise LakeError(f"RetailGaugeModel: cannot write {folder}: {exc}") from exc

    def load(self, folder: Path) -> None:
        """
        Purpose:
            Read a model written by `save`.

        Contract:
            Input:
                folder: Path
            Output:
                None (state)
            Raises:
                LakeError  -- missing or unreadable files
        """
        try:
            meta = json.loads((folder / _META).read_text(encoding="utf-8"))
            self._booster = lgb.Booster(model_file=str(folder / _BOOSTER))
        except (OSError, ValueError, lgb.basic.LightGBMError) as exc:
            raise LakeError(f"RetailGaugeModel: cannot read {folder}: {exc}") from exc
        self._features = list(meta["features"])
        self._medians = {k: float(v) for k, v in meta["medians"].items()}
