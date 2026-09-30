"""In-memory cache of read panels (SRC_DESIGN §2.2b): repeated notebook reads skip DuckDB."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Hashable

import pandas as pd

DEFAULT_MAX_BYTES = 2 * 1024**3


class PanelCache:
    """
    Purpose:
        Keep recently read panels in memory, keyed by (method, arguments), least recently used
        evicted first once the total size exceeds `max_bytes`. Frames are stored and returned as
        shallow copies: with pandas copy-on-write, a caller modifying its frame never changes the
        cached one. On by default in notebooks, off in pipelines (LakeReader decides).

    Contract:
        Input:
            max_bytes: int > 0  -- cap on the summed DataFrame.memory_usage(deep=True)
        Output:
            instance; `find`, `add`, `remove_all`; `hits`, `misses`, `size_bytes`
        Raises:
            ValueError  -- max_bytes <= 0

    Used by:
        lake.LakeReader     -- optional, injected
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-PCH-001  find after add is a hit and returns an equal frame; unknown key is a miss (None)
        TC-PCH-002  exceeding max_bytes evicts least recently used entries; one oversized frame
                   is not cached
        TC-PCH-003  modifying a returned frame does not change the cached frame
    """

    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self._max_bytes = max_bytes
        self._entries: OrderedDict[Hashable, tuple[pd.DataFrame, int]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    @property
    def size_bytes(self) -> int:
        """
        Purpose:
            Bytes held by cached frames.

        Contract:
            Input:
                (none)
            Output:
                int
            Raises:
                (none)
        """
        return sum(size for _, size in self._entries.values())

    def find(self, key: Hashable) -> pd.DataFrame | None:
        """
        Purpose:
            The cached frame for `key`, marking it most recently used.

        Contract:
            Input:
                key: Hashable  -- e.g. ("read_panel", "daily", "20260101", "20260930", ...)
            Output:
                DataFrame | None  -- a shallow copy, or None on a miss
            Raises:
                (none)
        """
        entry = self._entries.get(key)
        if entry is None:
            self.misses += 1
            return None
        self._entries.move_to_end(key)
        self.hits += 1
        return entry[0].copy(deep=False)

    def add(self, key: Hashable, frame: pd.DataFrame) -> None:
        """
        Purpose:
            Cache `frame` under `key`, evicting least recently used entries to stay under the cap.

        Contract:
            Input:
                key: Hashable; frame: DataFrame
            Output:
                None  -- a frame larger than max_bytes on its own is not cached
            Raises:
                (none)
        """
        size = int(frame.memory_usage(deep=True).sum())
        self._entries.pop(key, None)
        if size > self._max_bytes:
            return
        while self._entries and self.size_bytes + size > self._max_bytes:
            self._entries.popitem(last=False)
        self._entries[key] = (frame.copy(deep=False), size)

    def remove_all(self) -> None:
        """
        Purpose:
            Empty the cache (e.g. after a curate run changed the lake).

        Contract:
            Input:
                (none)
            Output:
                None
            Raises:
                (none)
        """
        self._entries.clear()
