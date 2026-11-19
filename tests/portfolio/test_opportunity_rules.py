"""Contract tests for portfolio.OpportunityRules (plan 21 ph4)."""

from __future__ import annotations

import pandas as pd

from quant_cn.core.opportunity_settings import RULES, OpportunitySettings
from quant_cn.portfolio.opportunity_rules import HIT_COLUMNS, LIST_COLUMNS, OpportunityRules

SETTINGS = OpportunitySettings(top_n=2, near_n=1)
GOOD = {
    "pct": 0.1, "avoid": False, "retail_leaving": True, "lg_weeks_pos_4w": 3.0,
    "np_yoy": 0.2, "np_qoq": 0.0, "val_value": 1.0, "val_median": 1.01, "fit": 1.0,
}  # fmt: skip
TICK = 1e-9


def _build_frame(rows: dict[str, dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("ts_code")


# TC-OPR-001
def test_tc_opr_001_boundaries() -> None:
    inside = {
        "inflow": {"lg_weeks_pos_4w": 2.0},
        "earnings": {"np_yoy": 0.2 - TICK},
        "valuation": {"val_value": 1.01},
        "fit": {"fit": 0.0},
        "retail_leaving": {"retail_leaving": False},
    }
    rows = {"edge": GOOD} | {rule: GOOD | change for rule, change in inside.items()}
    rows["qoq"] = GOOD | {"np_qoq": -TICK}
    rows["loss"] = GOOD | {"val_value": 0.0}
    hits = OpportunityRules(SETTINGS).compute_hits(_build_frame(rows))
    assert list(hits.columns) == list(RULES) and hits.loc["edge"].all()
    for rule in inside:
        assert not hits.loc[rule, rule] and hits.loc[rule].sum() == len(RULES) - 1
    assert not hits.loc["qoq", "earnings"] and not hits.loc["loss", "valuation"]


# TC-OPR-002
def test_tc_opr_002_avoid_required_nan() -> None:
    rows = {
        "hot": GOOD | {"avoid": True},
        "stay": GOOD | {"retail_leaving": False},  # misses only a required rule
        "nan": GOOD | {"np_yoy": float("nan")},
    }
    out = OpportunityRules(SETTINGS).build_list(_build_frame(rows), set())
    assert list(out.index) == ["nan"]
    assert out.loc["nan", "status"] == "near" and out.loc["nan", "missing"] == "earnings"
    assert list(out.columns)[-len(LIST_COLUMNS) :] == LIST_COLUMNS


# TC-OPR-003
def test_tc_opr_003_ranking() -> None:
    rows = {
        "a": GOOD | {"pct": 0.2},
        "b": GOOD | {"pct": 0.05},
        "c": GOOD | {"pct": 0.1},
        "n1": GOOD | {"pct": 0.15, "fit": float("nan")},
        "n2": GOOD | {"pct": 0.01, "lg_weeks_pos_4w": 1.0},
    }
    out = OpportunityRules(SETTINGS).build_list(_build_frame(rows), {"c"})
    assert list(out.index) == ["b", "c", "n2"]
    assert list(out["rank"]) == [1, 2, 3] and list(out["status"]) == ["listed", "listed", "near"]
    assert list(out["is_new"]) == [True, False, True]
    assert out.loc["b", "rules_hit"] == ",".join(RULES) and out.loc["b", "missing"] == ""
    assert out.loc["n2", "n_hit"] == len(RULES) - 1 and out[HIT_COLUMNS].dtypes.eq(bool).all()
    empty = OpportunityRules(SETTINGS).build_list(
        _build_frame({"x": GOOD | {"avoid": True}}), set()
    )
    assert empty.empty and "missing" in empty.columns
