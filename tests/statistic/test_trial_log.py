from __future__ import annotations

import pytest

from quant_cn.statistic.trial_log import TrialLog


# TC-TL-001
def test_tc_tl_001_sequential() -> None:
    log = TrialLog("c01")
    assert log.add_trial("ep_ttm", {"lag": 1}, 20, 0.05, 0.03) == "c01-00001"
    assert log.add_trial("ep_ttm", {"lag": 2}, 20, None, 0.01) == "c01-00002"
    frame = log.build_frame()
    assert log.n_trials == 2 and frame["params"].tolist() == ['{"lag": 1}', '{"lag": 2}']
    with pytest.raises(ValueError):
        TrialLog("")


# TC-TL-002
def test_tc_tl_002_append_only() -> None:
    log = TrialLog("c01")
    log.add_trial("mom", {}, 20, 0.1, 0.02)
    frame = log.build_frame()
    frame.loc[0, "factor"] = "tampered"
    assert log.build_frame().loc[0, "factor"] == "mom"
    assert not hasattr(log, "remove_trial") and not hasattr(log, "remove")


# TC-TL-003
def test_tc_tl_003_resume() -> None:
    log = TrialLog("c01")
    log.add_trial("mom", {}, 20, 0.1, 0.02)
    resumed = TrialLog.from_frame("c01", log.build_frame())
    assert resumed.add_trial("rev", {}, 5, None, -0.01) == "c01-00002"
    with pytest.raises(ValueError):
        TrialLog.from_frame("c02", log.build_frame())
