"""Contract tests for pipeline.UpdateAllRunner and pipeline.MakeTargetRunner (plan 38)."""

from __future__ import annotations

import datetime as dt
import io
import json
from pathlib import Path

from quant_cn.core.update_all_settings import UpdateAllSettings, UpdateStep
from quant_cn.lake.task_log import TaskLog
from quant_cn.pipeline.make_target_runner import MakeTargetRunner
from quant_cn.pipeline.update_all_runner import UpdateAllRunner


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def get_now(self) -> dt.datetime:
        self.t += 1
        return dt.datetime(2026, 11, 18, 6, 0) + dt.timedelta(seconds=self.t)

    def get_monotonic(self) -> float:
        self.t += 1
        return self.t


class FakeProcess:
    def __init__(self, codes: dict[str, list[int | None]]) -> None:
        self.codes = codes
        self.calls: list[str] = []

    def run_target(
        self, target: str, timeout_s: int, tail_lines: int
    ) -> tuple[int | None, list[str]]:
        self.calls.append(target)
        seq = self.codes.get(target, [0])
        code = seq.pop(0) if len(seq) > 1 else seq[0]
        return code, [f"{target} line", f"exit {code}"]


def _build(tmp_path: Path, codes: dict[str, list[int | None]], *steps: UpdateStep):  # type: ignore[no-untyped-def]
    settings = UpdateAllSettings(steps=list(steps))
    proc = FakeProcess(codes)
    runner = UpdateAllRunner(settings, TaskLog(tmp_path), proc, FakeClock(), tmp_path)  # type: ignore[arg-type]
    return settings, proc, runner


def _build_step(name: str, needs: list[str] | None = None, **kw: object) -> UpdateStep:
    return UpdateStep(name=name, target=name, needs=needs or [], **kw)


# TC-UAR-001
def test_tc_uar_001_failure_skips_dependents(tmp_path: Path) -> None:
    s, proc, runner = _build(tmp_path, {"a": [2]}, _build_step("a"), _build_step("b", ["a"]),
                             _build_step("c", ["b"]), _build_step("d"))  # fmt: skip
    rows = runner.run(s.list_steps(), "manual")
    assert [(r["task"], r["status"]) for r in rows] == [
        ("a", "failed"), ("b", "skipped"), ("c", "skipped"), ("d", "ok")]  # fmt: skip
    assert proc.calls == ["a", "d"]
    assert rows[0]["exit_code"] == 2 and "exit 2" in rows[0]["message"]
    assert rows[1]["message"] == "needs not ok: a" and rows[2]["message"] == "needs not ok: b"
    ledger = TaskLog(tmp_path).read_rows()
    assert list(ledger.seq) == [1, 2, 3, 4] and ledger.run_id.nunique() == 1
    # a need outside the selection counts as met
    assert runner.run(s.list_steps(only=["b"]), "manual")[0]["status"] == "ok"


# TC-UAR-002
def test_tc_uar_002_retry_and_timeout(tmp_path: Path) -> None:
    s, _proc, runner = _build(tmp_path, {"a": [1, 0], "b": [None]}, _build_step("a", retry=1),
                             _build_step("b"))  # fmt: skip
    rows = runner.run(s.list_steps(), "launchd")
    assert rows[0]["status"] == "ok" and rows[0]["attempts"] == 2 and rows[0]["message"] == ""
    assert rows[1]["status"] == "failed" and rows[1]["exit_code"] is None
    assert rows[1]["message"].startswith("timeout;") and rows[1]["trigger"] == "launchd"


# TC-UAR-003
def test_tc_uar_003_as_of(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text(json.dumps({"as_of": "20261118"}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    pairs = (("a", "a.json"), ("b", "b.json"), ("c", "x.json"))
    steps = [_build_step(n, output=f) for n, f in pairs]
    s, _, runner = _build(tmp_path, {}, *steps)
    assert [r["as_of"] for r in runner.run(s.list_steps(), "manual")] == ["20261118", None, None]


# TC-MKR-001
def test_tc_mkr_001_make_target_runner(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(
        "ok:\n\t@echo one\n\t@echo two\nbad:\n\t@echo oops\n\t@exit 3\nslow:\n\t@sleep 5\n",
        encoding="utf-8",
    )
    echo = io.StringIO()
    runner = MakeTargetRunner(tmp_path, echo=echo)
    assert runner.run_target("ok", 30, 1) == (0, ["two"])
    code, tail = runner.run_target("bad", 30, 5)
    assert code not in (0, None) and "oops" in tail
    assert runner.run_target("slow", 1, 5)[0] is None
    assert "one" in echo.getvalue()
