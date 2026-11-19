from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.industry_graph.node_stats_builder import (
    DIFF_COLUMNS,
    STAT_COLUMNS,
    UNMAPPED_COLUMNS,
    NodeStatsBuilder,
)

COLS = ["ts_code", "period", "item", "segment", "sector", "sales", "how"]


def build_members(*rows: tuple[object, ...]) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=COLS)


MEMBERS = build_members(
    ("A", "20231231", "电池", "SEG_BAT", "630000", 100.0, "exact"),
    ("B", "20231231", "电池", "SEG_BAT", "630000", 50.0, "exact"),
    ("A", "20251231", "电池", "SEG_BAT", "630000", 150.0, "exact"),
    ("C", "20251231", "电池", "SEG_BAT", "630000", 30.0, "exact"),
    ("C", "20251231", "固态电池", "SEG_SSB", "630000", 10.0, "exact"),
    ("A", "20251231", "储能系统集成服务", None, None, 20.0, "none"),
    ("C", "20251231", "储能系统集成服务", None, None, 5.0, "none"),
    ("D", "20251231", "其他", None, None, 9.0, "generic"),
)


# TC-NSB-001
def test_tc_nsb_001_stats() -> None:
    stats = NodeStatsBuilder().build_stats(MEMBERS, "20251231")
    assert list(stats.columns) == STAT_COLUMNS
    assert stats[["segment", "n_companies", "sales", "top_companies"]].values.tolist() == [
        ["SEG_BAT", 2, 180.0, "A,C"],
        ["SEG_SSB", 1, 10.0, "C"],
    ]


# TC-NSB-002
def test_tc_nsb_002_diff() -> None:
    diff = NodeStatsBuilder().build_diff(MEMBERS, "20231231", "20251231").set_index("segment")
    assert list(diff.reset_index().columns) == DIFF_COLUMNS
    bat = diff.loc["SEG_BAT"]
    assert (bat["n_before"], bat["n_after"], bat["joined"], bat["left"]) == (2, 2, "C", "B")
    assert bat["sales_change"] == pytest.approx(0.2)
    assert diff.loc["SEG_SSB", "n_before"] == 0 and pd.isna(diff.loc["SEG_SSB", "sales_change"])


# TC-NSB-003
def test_tc_nsb_003_unmapped_and_empty() -> None:
    builder = NodeStatsBuilder()
    lost = builder.build_unmapped(MEMBERS, "20251231")
    assert list(lost.columns) == UNMAPPED_COLUMNS
    assert lost[["sector", "item", "sales", "n_companies"]].values.tolist() == [
        ["630000", "储能系统集成服务", 25.0, 2]
    ]
    empty = MEMBERS.iloc[0:0]
    assert builder.build_stats(empty, "20251231").empty
    assert list(builder.build_diff(empty, "a", "b").columns) == DIFF_COLUMNS
    assert list(builder.build_unmapped(empty, "20251231").columns) == UNMAPPED_COLUMNS
