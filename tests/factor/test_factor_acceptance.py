from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_cn.core.exceptions import SchemaError
from quant_cn.core.frames import IC_TEST
from quant_cn.factor.factor_acceptance import FactorAcceptance

BASE = {c: None for c in IC_TEST.columns}


def build_row(factor: str, horizon: float, metric: str, window: str, **values: object) -> dict:
    return (
        BASE | {"factor": factor, "horizon": horizon, "metric": metric, "window": window} | values
    )


def build_rows(
    factor: str,
    t: float = 4.0,
    p_bhy: float | None = 0.01,
    subs: tuple[float | None, ...] = (2.0, 2.0, 2.0),
    ci: tuple[float, float] = (0.1, 0.5),
) -> list[dict[str, object]]:
    sign = math.copysign(1.0, t)
    rows = [
        build_row(factor, 20.0, "ic_mean", "full", value=0.05 * sign, t=t, p_adj_bhy=p_bhy),
        build_row(factor, 20.0, "icir", "full", value=sum(ci) / 2, ci_lo=ci[0], ci_hi=ci[1]),
        build_row(factor, 5.0, "ic_mean", "full", value=0.01, t=9.0, p_adj_bhy=0.0),
    ]
    for w, st in zip(("2019-2021", "2022-2024", "2025-"), subs, strict=True):
        if st is not None:
            rows.append(
                build_row(factor, 20.0, "ic_mean", w, value=0.05 * math.copysign(1, st), t=st)
            )
    return rows


def build_frame(*groups: list[dict[str, object]]) -> pd.DataFrame:
    return IC_TEST.normalize(pd.DataFrame([r for g in groups for r in g]), strict=True)


# TC-FA-001
def test_tc_fa_001_criteria() -> None:
    frame = build_frame(
        build_rows("good"),
        build_rows("low_t", t=2.5),
        build_rows("unstable", subs=(2.0, 1.4, 2.0)),
        build_rows("ci", ci=(-0.1, 0.4)),
    )
    out = FactorAcceptance().compute(frame).set_index("factor")
    assert out.loc["good", "verdict"] == "pass" and out.loc["good", "failed"] == ""
    assert out.loc["low_t", "failed"] == "1"
    assert out.loc["unstable", "failed"] == "2"
    assert out.loc["ci", "failed"] == "3"
    assert out.index[0] == "good" and out.loc["unstable", "t_2022-2024"] == 1.4


# TC-FA-002
def test_tc_fa_002_sign_missing_and_notes() -> None:
    notes = [
        build_row("neg", 0.0, m, "full", value=v)
        for m, v in (("peak_horizon", 60.0), ("half_life", math.nan), ("accumulation_ratio", 1.4))
    ]
    frame = build_frame(
        build_rows("neg", t=-4.0, subs=(-2.0, -1.6, -3.0), ci=(-0.5, -0.1)) + notes,
        build_rows("gap", subs=(2.0, None, 2.0)),
        build_rows("nop", p_bhy=None),
    )
    out = FactorAcceptance().compute(frame).set_index("factor")
    assert out.loc["neg", "verdict"] == "pass"
    assert out.loc["neg", "peak_horizon"] == 60.0 and out.loc["neg", "accumulation_ratio"] == 1.4
    assert math.isnan(out.loc["neg", "half_life"]) and math.isnan(out.loc["gap", "peak_horizon"])
    assert out.loc["gap", "failed"] == "2" and out.loc["nop", "failed"] == "1"


# TC-FA-003
def test_tc_fa_003_errors() -> None:
    for kwargs in ({"horizon": 0}, {"alpha": 1.0}, {"t_min": 0.0}, {"windows": ()}):
        with pytest.raises(ValueError):
            FactorAcceptance(**kwargs)  # type: ignore[arg-type]
    assert FactorAcceptance(horizon=60).compute(build_frame(build_rows("good"))).empty
    with pytest.raises(SchemaError):
        FactorAcceptance().compute(pd.DataFrame({"factor": ["x"]}))
