"""Extension point for resumable-download bookkeeping."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path


class BaseFetchLog(ABC):
    """
    Purpose:
        Abstract record of which (dataset, key) pairs are fully downloaded.

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            `read_done_keys`, `mark_done`, `save`; concrete `is_done`, `list_pending`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        lake.FetchLog                    -- production subclass
        core.BaseFetcher                 -- skip done keys, record finished ones
        data_loading.FetcherFactory      -- injected type
        pipeline.DownloadPipeline        -- pending counts in dry runs

    Test cases:
        TC-FL-001  mark_done then is_done round trip
        TC-FL-003  pending keeps input order and drops done keys
    """

    @abstractmethod
    def read_done_keys(self, dataset: str) -> set[str]:
        """
        Purpose:
            All keys recorded as done for a dataset.

        Contract:
            Input:
                dataset: str
            Output:
                set[str]  -- possibly empty
            Raises:
                LakeError  -- storage unreadable
        """

    @abstractmethod
    def mark_done(self, dataset: str, key: str, n_rows: int, path: Path | None) -> None:
        """
        Purpose:
            Record a finished key, replacing any earlier record for it.

        Contract:
            Input:
                dataset: str
                key:     str
                n_rows:  int >= 0
                path:    Path | None  -- file written, None for empty results
            Output:
                None
            Raises:
                LakeError  -- storage unwritable
        """

    @abstractmethod
    def save(self) -> Path | None:
        """
        Purpose:
            Make recorded keys durable (e.g. write the parquet mirror).

        Contract:
            Input:
                (none)
            Output:
                Path | None  -- file written, None if the store needs no file
            Raises:
                LakeError  -- write failed
        """

    def is_done(self, dataset: str, key: str) -> bool:
        """
        Purpose:
            True if the key is recorded as done.

        Contract:
            Input:
                dataset: str
                key:     str
            Output:
                bool
            Raises:
                LakeError  -- storage unreadable
        """
        return key in self.read_done_keys(dataset)

    def list_pending(self, dataset: str, keys: Sequence[str]) -> list[str]:
        """
        Purpose:
            The subset of `keys` not yet done, in input order.

        Contract:
            Input:
                dataset: str
                keys:    Sequence[str]
            Output:
                list[str]
            Raises:
                LakeError  -- storage unreadable
        """
        done = self.read_done_keys(dataset)
        return [k for k in keys if k not in done]
