"""Screenshots of app cards for phone alerts, through the Playwright script (plan 22, D-153)."""

from __future__ import annotations

import json
import logging
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from quant_cn.visualization.alert_message_builder import CardShot

logger = logging.getLogger(__name__)
Runner = Callable[[Sequence[str], Path], "subprocess.CompletedProcess[str]"]


class CardScreenshotter:
    """
    Purpose:
        Save one PNG per CardShot by running `apps/chain_web/tests/shot_cards.mjs` with Node
        (Playwright against the running app at `base_url`, phone style, 3x scale). Pictures are
        optional: a failed shot is logged and left out, never raised, so the text still goes.

    Contract:
        Input:
            node:     Path  -- node executable
            script:   Path  -- shot_cards.mjs inside a folder with playwright-core installed
            out_dir:  Path  -- where PNGs go (under ~/Pictures so Messages can read them)
            base_url: str   -- the app, e.g. "http://127.0.0.1:8787/"
            runner:   Runner | None  -- runs (args, cwd); default subprocess.run, 120 s timeout
        Output:
            instance; `run(shots) -> list[Path]`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `notify` command

    Test cases:
        TC-CSS-001  one spec per shot passed as JSON; saved files returned in order, failed and
                    missing ones left out
        TC-CSS-002  a runner error or a non-zero exit gives no pictures, no exception
    """

    def __init__(
        self,
        node: Path,
        script: Path,
        out_dir: Path,
        base_url: str,
        runner: Runner | None = None,
    ) -> None:
        self._node, self._script, self._out = node, script, out_dir
        self._base = base_url
        self._runner = runner or self._run

    def run(self, shots: Sequence[CardShot]) -> list[Path]:
        """
        Purpose:
            Screenshot every card; return the files that exist afterwards.

        Contract:
            Input:
                shots: Sequence[CardShot]  -- may be empty
            Output:
                list[Path]  -- saved PNGs in the order of `shots`; [] on any failure
            Raises:
                (none)
        """
        if not shots:
            return []
        self._out.mkdir(parents=True, exist_ok=True)
        files = [self._out / f"{s.stem}.png" for s in shots]
        for f in files:
            f.unlink(missing_ok=True)
        spec = [{"page": s.page, "selector": s.selector, "out": str(f), "title": s.title}
                for s, f in zip(shots, files, strict=True)]  # fmt: skip
        args = [str(self._node), str(self._script), self._base, json.dumps(spec)]
        try:
            done = self._runner(args, self._script.parent.parent)
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("card screenshots failed: %s", exc)
            return []
        if done.returncode != 0:
            logger.warning("card screenshots exit %d: %s", done.returncode, done.stderr[:200])
            return []
        return [f for f in files if f.is_file()]

    @staticmethod
    def _run(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args), cwd=cwd, capture_output=True, text=True, timeout=120, check=False
        )
