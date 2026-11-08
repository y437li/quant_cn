from __future__ import annotations

from quant_cn.core.docs.base_checker import Finding


# TC-BCH-001
def test_tc_bch_001_sort_and_text() -> None:
    items = [
        Finding("b.py", 1, "size", "x"),
        Finding("a.py", 9, "names", "y"),
        Finding("a.py", 2, "index", "z"),
    ]
    assert [f.to_text() for f in sorted(items)] == [
        "a.py:2 [index] z",
        "a.py:9 [names] y",
        "b.py:1 [size] x",
    ]
