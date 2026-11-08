from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_cn.factor.factor_preprocessor import FactorPreprocessor
from quant_cn.statistic.neutralizer import Neutralizer
from quant_cn.statistic.standardizer import Standardizer
from quant_cn.statistic.winsorizer import Winsorizer


def build_panels(n: int = 90) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(1)
    codes = [f"{i:06d}.SH" for i in range(n)]
    rows, exp = [], []
    for day in ("20260105", "20260106"):
        size = rng.standard_normal(n)
        industry = np.array(["801010.SI", "801020.SI", "801030.SI"])[np.arange(n) % 3]
        raw = 2.0 * size + (industry == "801020.SI") * 3 + rng.standard_normal(n)
        raw[0] = 1e6  # outlier
        rows += [
            {"trade_date": day, "ts_code": c, "factor": "f", "value": v, "value_raw": v}
            for c, v in zip(codes, raw, strict=True)
        ]
        exp += [
            {
                "trade_date": day,
                "ts_code": c,
                "l1_code": ind,
                "industry_backfilled": float(i < 9),
                "log_mcap": s,
            }
            for i, (c, ind, s) in enumerate(zip(codes, industry, size, strict=True))
        ]
    return pd.DataFrame(rows), pd.DataFrame(exp)


# TC-FPP-001
def test_tc_fpp_001_full_chain() -> None:
    factors, exposures = build_panels()
    pre = FactorPreprocessor(Winsorizer(k=5), Standardizer(), Neutralizer())
    out = pre.compute(factors, exposures).merge(exposures, on=["trade_date", "ts_code"])
    for _, day in out.groupby("trade_date"):
        assert day["value"].mean() == pytest.approx(0, abs=1e-9) and day[
            "value"
        ].std() == pytest.approx(1)
        assert np.corrcoef(day["value"], day["log_mcap"])[0, 1] == pytest.approx(0, abs=1e-9)
        assert day.groupby("l1_code")["value"].mean().abs().max() < 1e-9
    assert out["value_raw"].max() == 1e6


# TC-FPP-002
def test_tc_fpp_002_skip_and_log() -> None:
    factors, exposures = build_panels()
    pre = FactorPreprocessor(None, Standardizer(), None)
    out = pre.compute(factors)
    assert out["value"].abs().max() < 10  # standardised, not neutralised
    assert pre.build_log()["step"].tolist() == ["standardize"]
    full = FactorPreprocessor(Winsorizer(), Standardizer(), Neutralizer())
    full.compute(factors, exposures)
    log = full.build_log().set_index("step")
    assert list(log.index) == [
        "winsorize",
        "standardize",
        "backfilled_share",
        "neutralize",
        "restandardize",
    ]
    assert log.loc["backfilled_share", "value"] == pytest.approx(9 / 90)
    with pytest.raises(ValueError):
        full.compute(factors)
