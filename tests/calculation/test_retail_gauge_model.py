"""Contract tests for calculation.RetailGaugeModel (plan 21 ph3, D-142)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.retail_gauge_model import RetailGaugeModel
from quant_cn.core.exceptions import LakeError
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings

SETTINGS = RetailGaugeSettings(
    model={"n_estimators": 50, "learning_rate": 0.1, "num_leaves": 7, "min_child_samples": 5}
)


def build_panel(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 200
    parts = []
    for q in ("20250331", "20250630", "20250930"):
        x = rng.normal(size=n)
        noise = rng.normal(size=n)
        parts.append(pd.DataFrame({"q": q, "x": x, "noise": noise, "y": 0.1 * x + 0.01 * noise}))
    frame = pd.concat(parts, ignore_index=True)
    frame.loc[0, "y"] = 5.0  # |y| >= 2: dropped
    frame.loc[1, "x"] = np.nan  # filled with the median
    return frame


# TC-RGMD-001
def test_tc_rgmd_001_fit_predict() -> None:
    model = RetailGaugeModel(SETTINGS)
    model.build(build_panel(), ["x", "noise"])
    test = build_panel(seed=1)
    pct = model.compute_pct(test)
    assert pct.between(0, 1).all() and pct.max() == 1.0
    assert pct.corr(test["x"], method="spearman") > 0.9


# TC-RGMD-002
def test_tc_rgmd_002_save_load(tmp_path: Path) -> None:
    with pytest.raises(LakeError):
        RetailGaugeModel(SETTINGS).compute_pct(build_panel())
    model = RetailGaugeModel(SETTINGS)
    model.build(build_panel(), ["x", "noise"])
    model.save(tmp_path / "m")
    again = RetailGaugeModel(SETTINGS)
    again.load(tmp_path / "m")
    test = build_panel(seed=2)
    pd.testing.assert_series_equal(model.compute_pct(test), again.compute_pct(test))
    with pytest.raises(LakeError):
        RetailGaugeModel(SETTINGS).load(tmp_path / "missing")
