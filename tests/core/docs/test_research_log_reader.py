from __future__ import annotations

from pathlib import Path

from quant_cn.core.docs.markdown_table import MarkdownTableReader
from quant_cn.core.docs.research_log_reader import ResearchLogReader, ResearchRun

RUN = "research_space/runs/20261113_washout_study/"
OUT = "meta/runs/research/20261113_washout_study/"
PROTO = "research_space/prototypes/holder_nowcast/"
LOG = (
    "# Research log\n\nIntro text.\n\n"
    "| Date | Slug | Question | Scripts | Outputs | Conclusion | Follow-up |\n"
    "|---|---|---|---|---|---|---|\n"
    f"| 2026-11-13 | 20261113_washout_study | 怎么判断是否洗干净了筹码 | `{RUN}` | `{OUT}` "
    "| 获利盘 ≤ 10% helps | plan 21 |\n"
    f"| 2026-11-12 | 20261112_retail_gauge_v5 | 预测散户人数 | `{PROTO}` "
    "| `meta/runs/holder_nowcast/` | v5 IC 0.686 | D-142 |\n"
)


# TC-RLR-001
def test_tc_rlr_001_rows(tmp_path: Path) -> None:
    path = tmp_path / "RESEARCH_LOG.md"
    path.write_text(LOG, encoding="utf-8")
    runs = ResearchLogReader(MarkdownTableReader()).read(path)
    assert [r.slug for r in runs] == ["20261113_washout_study", "20261112_retail_gauge_v5"]
    first = runs[0]
    assert isinstance(first, ResearchRun)
    assert first.scripts == RUN
    assert first.outputs == OUT
    assert (first.question, first.follow_up) == ("怎么判断是否洗干净了筹码", "plan 21")
    assert [r.line for r in runs] == [7, 8]


# TC-RLR-002
def test_tc_rlr_002_missing(tmp_path: Path) -> None:
    reader = ResearchLogReader(MarkdownTableReader())
    assert reader.read(tmp_path / "absent.md") == []
    other = tmp_path / "other.md"
    other.write_text("| A | B |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
    assert reader.read(other) == []
