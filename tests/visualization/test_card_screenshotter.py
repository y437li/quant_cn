"""Contract tests for visualization.CardScreenshotter (plan 22, D-153)."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from quant_cn.visualization.alert_message_builder import CardShot
from quant_cn.visualization.card_screenshotter import CardScreenshotter

SHOTS = [CardShot("#a", ".x", "one"), CardShot("#b", ".y", "two")]


def _build(tmp_path: Path, runner: object) -> CardScreenshotter:
    return CardScreenshotter(Path("node"), tmp_path / "tests" / "s.mjs", tmp_path / "out",
                             "http://app/", runner)  # type: ignore[arg-type]  # fmt: skip


# TC-CSS-001
def test_tc_css_001_saved_in_order(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def runner(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        seen.append(list(args))
        Path(json.loads(args[3])[1]["out"]).write_bytes(b"png")  # only the second one saved
        return subprocess.CompletedProcess(list(args), 0, "", "")

    files = _build(tmp_path, runner).run(SHOTS)
    assert [f.name for f in files] == ["two.png"]
    spec = json.loads(seen[0][3])
    assert seen[0][2] == "http://app/" and [s["page"] for s in spec] == ["#a", "#b"]
    assert _build(tmp_path, runner).run([]) == []


# TC-CSS-002
def test_tc_css_002_failures(tmp_path: Path) -> None:
    def broken(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        raise OSError("no node")

    def failing(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(list(args), 1, "", "boom")

    assert _build(tmp_path, broken).run(SHOTS) == []
    assert _build(tmp_path, failing).run(SHOTS) == []
