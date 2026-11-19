"""Run one make target as a subprocess, echo its output, keep its tail (plan 38, D-181)."""

from __future__ import annotations

import subprocess
import sys
import threading
from collections import deque
from pathlib import Path
from typing import TextIO


class MakeTargetRunner:
    """
    Purpose:
        Run `make <target>` in the repo root, echo every output line (stdout and stderr merged)
        to `echo` as it arrives, and return the exit code and the last output lines. A target
        that runs past its time limit is killed.

    Contract:
        Input:
            repo_root: Path
            make:      str              -- make executable (default "make")
            echo:      TextIO | None    -- where lines are echoed (default sys.stdout)
        Output:
            instance; `run_target(target, timeout_s, tail_lines) -> (exit_code | None, tail)`
        Raises:
            (none at construction)

    Used by:
        cli.UpdateCommands  -- injected into UpdateAllRunner (one call per step attempt)

    Test cases:
        TC-MKR-001  a target that succeeds returns 0 and its last lines; a failing target returns
                    its exit code; a target past its limit is killed and returns None
    """

    def __init__(self, repo_root: Path, make: str = "make", echo: TextIO | None = None) -> None:
        self._root = repo_root
        self._make = make
        self._echo = echo or sys.stdout

    def run_target(
        self, target: str, timeout_s: int, tail_lines: int
    ) -> tuple[int | None, list[str]]:
        """
        Purpose:
            Run one target to completion or until its time limit.

        Contract:
            Input:
                target:     str  -- make target
                timeout_s:  int  -- seconds before the process is killed
                tail_lines: int  -- output lines kept
            Output:
                tuple  -- (exit code, or None when killed at the limit; last output lines)
            Raises:
                (none; a make that cannot start returns exit code 127 and the error text)
        """
        tail: deque[str] = deque(maxlen=tail_lines)
        try:
            proc = subprocess.Popen(  # fixed argv, no shell
                [self._make, target], cwd=self._root, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
            )  # fmt: skip
        except OSError as exc:
            return 127, [f"cannot start {self._make} {target}: {exc}"]
        killed = threading.Event()

        def _kill() -> None:
            killed.set()
            proc.kill()

        timer = threading.Timer(timeout_s, _kill)
        timer.start()
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                self._echo.write(line)
                tail.append(line.rstrip("\n"))
            code = proc.wait()
        finally:
            timer.cancel()
        if killed.is_set():
            tail.append(f"killed after {timeout_s} s")
            return None, list(tail)
        return code, list(tail)
