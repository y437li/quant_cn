from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quant_cn.core.frames import IC_TEST
from quant_cn.statistic.multiple_testing_adjuster import MultipleTestingAdjuster

BH1995 = [
    0.0001,
    0.0004,
    0.0019,
    0.0095,
    0.0201,
    0.0278,
    0.0298,
    0.0344,
    0.0459,
    0.3240,
    0.4262,
    0.5719,
    0.6528,
    0.7590,
    1.0000,
]


# TC-MTA-001
def test_tc_mta_001_hand_example() -> None:
    adj, p = MultipleTestingAdjuster(), [0.01, 0.04, 0.03, 0.005]
    assert adj.compute_holm(p) == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert adj.compute_bh(p) == pytest.approx([0.02, 0.04, 0.04, 0.02])
    c4 = 1 + 1 / 2 + 1 / 3 + 1 / 4
    assert adj.compute_bhy(p) == pytest.approx([0.02 * c4, 0.04 * c4, 0.04 * c4, 0.02 * c4])


# TC-MTA-002
def test_tc_mta_002_bh1995() -> None:
    adj = MultipleTestingAdjuster()
    assert int((adj.compute_bh(BH1995) <= 0.05).sum()) == 4
    assert int((adj.compute_holm(BH1995) <= 0.05).sum()) == 3


# TC-MTA-003
def test_tc_mta_003_null_family() -> None:
    rng, adj, sims = np.random.default_rng(2), MultipleTestingAdjuster(), 400
    holm_any = bhy_any = 0
    for _ in range(sims):
        p = rng.uniform(size=200)  # every hypothesis true
        holm_any += (adj.compute_holm(p) <= 0.05).any()
        bhy_any += (adj.compute_bhy(p) <= 0.05).any()
    assert holm_any / sims <= 0.05 + 0.02 and bhy_any / sims <= 0.05 + 0.02


# TC-MTA-004
def test_tc_mta_004_romano_wolf() -> None:
    rng = np.random.default_rng(4)
    t_boot = rng.standard_normal((2000, 5))
    t = np.array([6.0, 0.3, -2.2, 1.1, 2.0])
    rw = MultipleTestingAdjuster().compute_romano_wolf(t, t_boot)
    order = np.argsort(-np.abs(t))
    assert np.all(np.diff(rw[order]) >= 0)  # monotone in |t|
    raw = (np.abs(t_boot) >= np.abs(t)).mean(axis=0)
    assert np.all(rw >= raw - 1e-12) and rw[0] < 0.01
    with pytest.raises(ValueError):
        MultipleTestingAdjuster().compute_romano_wolf(t, t_boot[:, :4])


# TC-MTA-005
def test_tc_mta_005_build_adjusted() -> None:
    rows = []
    for factor, t in [("a", 3.5), ("b", 1.0), ("c", -3.1)]:
        base = {c: None for c in IC_TEST.columns}
        rows.append(
            base
            | {
                "factor": factor,
                "horizon": 20.0,
                "metric": "ic_mean",
                "window": "full",
                "t": t,
                "p": float(2 * stats.norm.sf(abs(t))),
            }
        )
        rows.append(
            base
            | {
                "factor": factor,
                "horizon": 20.0,
                "metric": "icir",
                "window": "full",
                "t": t,
                "p": 0.5,
            }
        )
    out = MultipleTestingAdjuster().build_adjusted(pd.DataFrame(rows))
    main = out[out["metric"] == "ic_mean"].set_index("factor")
    assert main["hlz_pass"].tolist() == [1.0, 0.0, 1.0]
    assert main.loc["a", "p_adj_holm"] >= main.loc["a", "p"]
    assert out[out["metric"] == "icir"]["p_adj_holm"].isna().all()
