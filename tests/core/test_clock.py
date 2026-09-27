from __future__ import annotations

from quant_cn.core.clock import Clock


# TC-CL-001
def test_tc_cl_001_today_str_matches_now() -> None:
    clock = Clock()
    today = clock.today_str()
    assert len(today) == 8 and today.isdigit()
    assert today == clock.now().strftime("%Y%m%d")


# TC-CL-002
def test_tc_cl_002_sleep_zero_and_monotonic() -> None:
    clock = Clock()
    first = clock.monotonic()
    clock.sleep(0)
    assert clock.monotonic() >= first
