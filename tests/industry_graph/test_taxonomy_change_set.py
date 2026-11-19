from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.industry_graph.taxonomy_change_set import TaxonomyChangeSet

GOOD = """
version: {v}
effective_period: "20251231"
changes:
  - {{op: upsert, kind: new, node: {{id: PROD_X, type: product, name: 新品}}}}
  - {{op: retire, kind: merge, id: SEG_A, successor: SEG_B}}
"""


# TC-TCS-001
def test_tc_tcs_001_read_all(tmp_path: Path) -> None:
    assert TaxonomyChangeSet.read_all(tmp_path) == []
    folder = tmp_path / "_changes"
    folder.mkdir()
    (folder / "v2.yaml").write_text(GOOD.format(v="v2"), encoding="utf-8")
    (folder / "v1.yaml").write_text(GOOD.format(v="v1"), encoding="utf-8")
    sets = TaxonomyChangeSet.read_all(tmp_path)
    assert [s.version for s in sets] == ["v1", "v2"]
    assert [c.node_id for c in sets[0].changes] == ["PROD_X", "SEG_A"]


# TC-TCS-002
@pytest.mark.parametrize(
    "change",
    ["{op: upsert, node: {id: PROD_X}}", "{op: retire, id: SEG_A}", "{op: drop, id: SEG_A}"],
)
def test_tc_tcs_002_bad_change(tmp_path: Path, change: str) -> None:
    folder = tmp_path / "_changes"
    folder.mkdir()
    text = f'version: v1\neffective_period: "20251231"\nchanges:\n  - {change}\n'
    (folder / "v1.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match=r"v1\.yaml"):
        TaxonomyChangeSet.read_all(tmp_path)
