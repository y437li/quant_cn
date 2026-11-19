"""Contract tests for calculation.RetailGaugeNowcaster (plan 21 ph3, D-142, D-155, D-167)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.calculation.retail_gauge_feature_builder import RetailGaugeFeatureBuilder
from quant_cn.calculation.retail_gauge_model import RetailGaugeModel
from quant_cn.calculation.retail_gauge_nowcaster import RetailGaugeNowcaster
from quant_cn.core.exceptions import LakeError
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.dated_table_store import DatedTableStore
from tests.support import MiniLake

SETTINGS = RetailGaugeSettings(
    model={"n_estimators": 30, "learning_rate": 0.1, "num_leaves": 7, "min_child_samples": 5}
)
QUARTERS = ["20240331", "20240630", "20240930", "20241231", "20250331"]


class FakeFeatures(RetailGaugeFeatureBuilder):
    """Quarter-end rows with one informative feature."""

    def __init__(self, lake: MiniLake) -> None:
        tables = DatedTableStore(lake.writer)
        super().__init__(SETTINGS, lake.query, HolderCountPanel(lake.query), tables)
        rng = np.random.default_rng(0)
        parts = [
            pd.DataFrame(
                {
                    "ts_code": [f"{i:06d}.SZ" for i in range(100)],
                    "q": q,
                    "as_of": q,
                    "x": rng.normal(size=100),
                }
            )
            for q in QUARTERS
        ]
        self.rows = pd.concat(parts, ignore_index=True)

    def build_quarter_ends(self, end: str) -> pd.DataFrame:
        return self.rows[self.rows["q"] <= end].reset_index(drop=True)

    def build(self, as_ofs: Sequence[str]) -> pd.DataFrame:
        return self.rows[self.rows["as_of"].isin(list(as_ofs))].reset_index(drop=True)


class FakeHolders(HolderCountPanel):
    """y = x / 10, announced 30 days after the quarter (late: 20250510 for the last one)."""

    def __init__(self, lake: MiniLake, late_y: float | None = None) -> None:
        super().__init__(lake.query)
        self.late_y = late_y

    def compute_labels(self, rows: pd.DataFrame) -> pd.DataFrame:
        ann = rows["q"].map(
            lambda q: (
                f"{q[:4]}{int(q[4:6]) + 1:02d}28" if q[4:6] != "12" else f"{int(q[:4]) + 1}0128"
            )
        )
        y = rows["x"] / 10
        if self.late_y is not None:
            y = y.where(rows["q"] != "20250331", self.late_y)
        ann = ann.where(rows["q"] != "20250331", "20250510")
        return pd.DataFrame({"y": y, "ann_y": ann}, index=rows.index)


def build(lake: MiniLake, root: Path, late_y: float | None = None) -> RetailGaugeNowcaster:
    return RetailGaugeNowcaster(
        SETTINGS,
        FakeFeatures(lake),
        FakeHolders(lake, late_y),
        lake.writer,
        DatedTableStore(lake.writer),
        root,
        lambda: RetailGaugeModel(SETTINGS),
    )


# TC-RGN-001
def test_tc_rgn_001_retrain_key(lake: MiniLake, tmp_path: Path) -> None:
    now = build(lake, tmp_path)
    assert now.get_retrain_key("20250430") == "20241101"
    assert now.get_retrain_key("20250501") == "20250501"
    assert now.get_retrain_key("20250105") == "20241101"


# TC-RGN-002
def test_tc_rgn_002_streaks() -> None:
    sessions = [f"202501{d:02d}" for d in range(1, 13)]
    rows = [
        ("A", 0, "q1", 0.2),
        ("A", 3, "q1", 0.3),
        ("A", 6, "q1", 0.1),  # 3 in a row
        ("B", 0, "q1", 0.2),
        ("B", 3, "q1", 0.2),
        ("B", 9, "q1", 0.2),  # checkpoint 6 missing
        ("C", 0, "q1", 0.2),
        ("C", 3, "q1", 0.2),
        ("C", 6, "q2", 0.2),  # new quarter
        ("D", 0, "q1", 0.9),
        ("D", 3, "q1", 0.95),
        ("D", 6, "q1", 0.8999),
    ]
    frame = pd.DataFrame(
        [{"ts_code": c, "as_of": sessions[i], "q": q, "pct": p} for c, i, q, p in rows]
    )
    out = RetailGaugeNowcaster.compute_streaks(frame, sessions, SETTINGS).set_index(
        ["ts_code", "as_of"]
    )
    assert (
        out.loc[("A", sessions[6]), "lo_streak"] == 3
        and out.loc[("A", sessions[6]), "retail_leaving"]
    )
    assert (
        out.loc[("A", sessions[3]), "lo_streak"] == 2
        and not out.loc[("A", sessions[3]), "retail_leaving"]
    )
    assert out.loc[("B", sessions[9]), "lo_streak"] == 1
    assert out.loc[("C", sessions[6]), "lo_streak"] == 1
    assert out.loc[("D", sessions[0]), "avoid"] and not out.loc[("D", sessions[6]), "avoid"]
    assert (
        out.loc[("D", sessions[3]), "hi_streak"] == 2
        and out.loc[("D", sessions[6]), "hi_streak"] == 0
    )


# TC-RGN-003
def test_tc_rgn_003_train_pit(lake: MiniLake, tmp_path: Path) -> None:
    test = FakeFeatures(lake).rows.query("q == '20250331'")
    base = build(lake, tmp_path / "a").build_model("20250501").compute_pct(test)
    leaky = build(lake, tmp_path / "b", late_y=9.0).build_model("20250501").compute_pct(test)
    pd.testing.assert_series_equal(base, leaky)  # the 20250510 label is not used on 20250501
    with pytest.raises(LakeError):
        build(lake, tmp_path / "c").build_model("20240901")  # 2 quarters announced by then


# TC-RGN-004
def test_tc_rgn_004_calibration(lake: MiniLake, tmp_path: Path) -> None:
    pct = [(i + 0.5) / 20 for i in range(20)]
    back = pd.DataFrame(
        {
            "q": ["q1"] * 20 + ["q2"] * 20,
            "y": [p - 0.5 for p in pct] + [p + 0.5 for p in pct],
            "pct": pct * 2,
            "ann_y": ["20250101"] * 20 + ["20250901"] * 20,
        }
    )
    cal = build(lake, tmp_path).compute_calibration(back, "20250601")  # q2 not known yet
    assert list(cal.index) == list(range(10)) and (cal["n"] == 2).all()
    assert cal.loc[9, "exp_change"] == pytest.approx(0.95 - 0.5)  # y minus the quarter median (0)
    assert cal.loc[0, "iqr_lo"] < cal.loc[0, "exp_change"] < cal.loc[0, "iqr_hi"]
