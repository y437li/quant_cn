"""Extension point for run monitoring events (D-022)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRunLog(ABC):
    """
    Purpose:
        Abstract append-only log of runs and per-key events; the source of truth for
        "what happened".

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance with `open_run`, `record_event`, `close_run`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        lake.RunLog                      -- production subclass
        core.BaseFetcher.run             -- one event per key
        pipeline.LocalRunner             -- run start/finish, blocked steps
        data_loading.FetcherFactory      -- injected type

    Test cases:
        TC-RL-001  start/event/finish rows are queryable
    """

    @abstractmethod
    def open_run(self, kind: str) -> str:
        """
        Purpose:
            Open a run and return its id.

        Contract:
            Input:
                kind: str  -- e.g. "download", "compact"
            Output:
                str  -- unique run id
            Raises:
                LakeError  -- storage unwritable
        """

    @abstractmethod
    def record_event(
        self,
        run_id: str,
        dataset: str,
        key: str,
        status: str,
        n_rows: int = 0,
        duration_ms: int = 0,
        message: str = "",
    ) -> None:
        """
        Purpose:
            Append one event (fetched | skipped | empty | failed | blocked).

        Contract:
            Input:
                run_id: str; dataset: str; key: str; status: str
                n_rows: int >= 0; duration_ms: int >= 0; message: str
            Output:
                None
            Raises:
                LakeError  -- storage unwritable
        """

    @abstractmethod
    def close_run(self, run_id: str, status: str, message: str = "") -> None:
        """
        Purpose:
            Close a run with its final status.

        Contract:
            Input:
                run_id: str; status: str ("ok" | "failed"); message: str
            Output:
                None
            Raises:
                LakeError  -- storage unwritable
        """
