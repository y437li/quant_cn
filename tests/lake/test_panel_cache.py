from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.lake.panel_cache import PanelCache


def build_frame(n: int) -> pd.DataFrame:
    return pd.DataFrame({"ts_code": [f"{i:06d}.SH" for i in range(n)], "close": [1.0] * n})


# TC-PCH-001
def test_tc_pch_001_hit_and_miss() -> None:
    cache = PanelCache()
    assert cache.find(("read_panel", "daily")) is None and cache.misses == 1
    cache.add(("read_panel", "daily"), build_frame(3))
    out = cache.find(("read_panel", "daily"))
    assert out is not None and out.equals(build_frame(3)) and cache.hits == 1
    with pytest.raises(ValueError):
        PanelCache(0)


# TC-PCH-002
def test_tc_pch_002_lru_eviction() -> None:
    one = int(build_frame(100).memory_usage(deep=True).sum())
    cache = PanelCache(max_bytes=int(one * 2.5))
    cache.add("a", build_frame(100))
    cache.add("b", build_frame(100))
    assert cache.find("a") is not None  # a becomes most recent
    cache.add("c", build_frame(100))  # evicts b, the least recently used
    assert cache.find("b") is None and cache.find("a") is not None and cache.find("c") is not None
    cache.add("huge", build_frame(1000))
    assert cache.find("huge") is None and cache.size_bytes <= int(one * 2.5)
    cache.remove_all()
    assert cache.size_bytes == 0


# TC-PCH-003
def test_tc_pch_003_isolation() -> None:
    cache = PanelCache()
    cache.add("k", build_frame(2))
    out = cache.find("k")
    assert out is not None
    out.loc[0, "close"] = 99.0
    again = cache.find("k")
    assert again is not None and again.loc[0, "close"] == 1.0
