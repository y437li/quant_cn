from __future__ import annotations

from quant_cn.core.clock import Clock


# TC-CL-001
def test_tc_cl_001_today_str_matches_now() -> None:
    clock = Clock()
    today = clock.get_today()
    assert len(today) == 8 and today.isdigit()
    assert today == clock.get_now().strftime("%Y%m%d")


# TC-CL-002
def test_tc_cl_002_sleep_zero_and_monotonic() -> None:
    clock = Clock()
    first = clock.get_monotonic()
    clock.sleep(0)
    assert clock.get_monotonic() >= first
