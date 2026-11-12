"""Tests of ExposureStandardizer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.frames import RISK_EXPOSURE
from quant_cn.core.risk_model_settings import RiskModelSettings, StyleSpec
from quant_cn.risk.exposure_standardizer import ExposureStandardizer
from quant_cn.statistic.neutralizer import Neutralizer
from quant_cn.statistic.standardizer import Standardizer

STYLES = [
    StyleSpec(name="size", descriptors={"lncap": 1.0}),
    StyleSpec(name="beta", descriptors={"beta": 1.0}),
    StyleSpec(
        name="residual_volatility",
        descriptors={"dastd": 0.74, "cmra": 0.26},
        orthogonalize_to=["size", "beta"],
    ),
    StyleSpec(name="growth", descriptors={"egro": 1.0}),
]


def build_table(n: int = 200, days: int = 2, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frames = []
    for d in range(days):
        lncap = rng.normal(23, 1, n)
        frames.append(
            pd.DataFrame(
                {
                    "trade_date": f"2025010{d + 2}",
                    "ts_code": [f"{i:06d}.SZ" for i in range(n)],
                    "l1_code": [f"80{i % 4}" for i in range(n)],
                    "industry_backfilled": [i % 7 == 0 for i in range(n)],
                    "circ_mv": np.exp(lncap),
                    "lncap": lncap,
                    "beta": rng.normal(1, 0.3, n),
                    "dastd": rng.lognormal(-4, 0.3, n) + 0.002 * lncap,
                    "cmra": rng.lognormal(-1, 0.3, n),
                    "egro": rng.normal(0, 1, n),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def build(**kw: float) -> ExposureStandardizer:
    return ExposureStandardizer(
        RiskModelSettings(styles=STYLES, **kw), Standardizer(), Neutralizer()
    )


def build_wide(out: pd.DataFrame) -> pd.DataFrame:
    return out.pivot(index=["trade_date", "ts_code"], columns="factor", values="exposure")


# TC-EXS-001
def test_tc_exs_001_standardised_and_clipped() -> None:
    table = build_table()
    table.loc[0, "beta"] = 50.0
    out = build().compute(table)
    x = build_wide(out).join(table.set_index(["trade_date", "ts_code"])["circ_mv"])
    for _, day in x.groupby(level="trade_date"):
        for style in ("size", "beta"):
            mean = (day[style] * day["circ_mv"]).sum() / day["circ_mv"].sum()
            assert mean == pytest.approx(0.0, abs=1e-9)
            assert day[style].std() == pytest.approx(1.0, abs=1e-9)
    assert out[out["factor"] == "beta"]["exposure"].abs().max() <= 3.5


# TC-EXS-002
def test_tc_exs_002_orthogonalised() -> None:
    x = build_wide(build().compute(build_table()))
    for _, day in x.groupby(level="trade_date"):
        for target in ("size", "beta"):
            c = np.cov(day["residual_volatility"], day[target])[0, 1]
            assert abs(c) < 0.05


# TC-EXS-003
def test_tc_exs_003_renormalise_fill_and_coverage() -> None:
    table = build_table()
    table.loc[5, "cmra"] = np.nan  # renormalised: dastd alone
    table.loc[7, "beta"] = np.nan  # filled from industry + size
    first = table["trade_date"] == table["trade_date"].iloc[-1]
    table.loc[first & (table.index % 4 != 0), "egro"] = np.nan  # 25% coverage -> dropped
    out = build().compute(table)
    row = out[
        (out["ts_code"] == table.loc[7, "ts_code"])
        & (out["trade_date"] == table.loc[7, "trade_date"])
    ]
    beta = row[row["factor"] == "beta"].iloc[0]
    assert beta["is_filled"] == 1.0 and np.isfinite(beta["exposure"])
    assert np.isnan(beta["exposure_raw"])
    rv = row = out[
        (out["ts_code"] == table.loc[5, "ts_code"]) & (out["factor"] == "residual_volatility")
    ]
    assert np.isfinite(rv["exposure"]).all()
    late = out[(out["factor"] == "growth") & (out["trade_date"] == table["trade_date"].iloc[-1])]
    assert late.empty


# TC-EXS-004
def test_tc_exs_004_industry_rows_and_schema() -> None:
    table = build_table()
    out = build().compute(table)
    ind = out[out["factor"].str.startswith("ind_")]
    assert len(ind) == len(table)
    assert (ind["exposure"] == 1.0).all()
    assert ind["is_filled"].sum() == table["industry_backfilled"].sum()
    RISK_EXPOSURE.validate(out)
    assert out["exposure"].notna().all()
