from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quant_cn.statistic.block_bootstrap import BlockBootstrap
from quant_cn.statistic.hac_variance import HacVariance
from quant_cn.statistic.ic_significance import IcSignificance


def build_tester() -> IcSignificance:
    return IcSignificance(HacVariance(), BlockBootstrap(resamples=300, seed=1))


def build_ic(values: np.ndarray, start: str = "2019-01-02") -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=len(values)).strftime("%Y%m%d")
    return pd.DataFrame(
        {"trade_date": dates, "factor": "f", "horizon": 20.0, "ic": values, "n": 3000.0}
    )


# TC-ICS-001
def test_tc_ics_001_rows() -> None:
    ic = 0.03 + 0.1 * np.random.default_rng(3).standard_normal(1600)
    out = build_tester().compute(build_ic(ic))
    full = out[out["window"] == "full"].set_index("metric")
    assert set(full.index) == {"ic_mean", "icir", "fisher_z"}
    assert (
        full.loc["ic_mean", "ci_lo"] < full.loc["ic_mean", "value"] < full.loc["ic_mean", "ci_hi"]
    )
    assert full.loc["ic_mean", "t"] == pytest.approx(HacVariance().compute_t(ic, 20)["t"])
    assert set(out["window"]) == {"full", "2019-2021", "2022-2024", "2025-"}
    mixed = pd.concat([build_ic(np.zeros(5)), build_ic(np.zeros(5)).assign(factor="g")])
    with pytest.raises(ValueError):
        build_tester().compute(mixed)


# TC-ICS-002
def test_tc_ics_002_break() -> None:
    rng = np.random.default_rng(5)
    shifted = np.r_[0.05 + 0.05 * rng.standard_normal(300), 0.05 * rng.standard_normal(200)]
    res = build_tester().compute_break(build_ic(shifted), horizon=1)
    dates = build_ic(shifted)["trade_date"].tolist()
    assert res["significant"] and abs(dates.index(res["break_date"]) - 300) <= 15
    stable = sum(
        build_tester().compute_break(
            build_ic(0.05 * np.random.default_rng(s).standard_normal(300))
        )["significant"]
        for s in range(20)
    )
    assert stable <= 4


# TC-ICS-003
def test_tc_ics_003_pesaran_timmermann() -> None:
    rng, tester = np.random.default_rng(9), build_tester()
    p_values = [
        tester.compute_pesaran_timmermann(rng.standard_normal(400), rng.standard_normal(400))[
            "p_2009"
        ]
        for _ in range(300)
    ]
    assert stats.kstest(p_values, "uniform").pvalue > 0.01
    assert 0.02 <= np.mean(np.array(p_values) <= 0.05) <= 0.09
    f = rng.standard_normal(400)
    skilled = tester.compute_pesaran_timmermann(f, f + rng.standard_normal(400))
    assert skilled["p_2009"] < 1e-6 and skilled["p_1992"] < 1e-6 and skilled["hit_rate"] > 0.6


# TC-ICS-004
def test_tc_ics_004_decay() -> None:
    profile = {h: 0.05 * 0.5 ** (h / 10) for h in (1, 5, 10, 20, 60)}
    res = IcSignificance.compute_decay(profile)
    assert res["half_life"] == pytest.approx(10.0) and res["r2"] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        IcSignificance.compute_decay({5: 0.01})


# TC-ICS-005
def test_tc_ics_005_decay_profiles() -> None:
    rising = IcSignificance.compute_decay({1: 0.01, 5: 0.02, 10: 0.03, 20: 0.04, 60: 0.06})
    assert math.isnan(rising["half_life"]) and rising["rising"] == 1.0
    assert rising["peak_horizon"] == 60.0 and rising["accumulation_ratio"] == pytest.approx(1.5)
    hump = {1: 0.01, 5: 0.04, 10: 0.04 * 0.5**0.25, 20: 0.04 * 0.5**0.75, 60: 0.04 * 0.5**2.75}
    res = IcSignificance.compute_decay(hump)
    assert res["peak_horizon"] == 5.0 and res["half_life"] == pytest.approx(20.0)
    assert res["n"] == 4.0 and res["rising"] == 0.0
    neg = IcSignificance.compute_decay({h: -v for h, v in hump.items()})
    assert neg["peak_horizon"] == 5.0 and neg["half_life"] == pytest.approx(20.0)
    assert neg["accumulation_ratio"] == pytest.approx(0.5**2)
