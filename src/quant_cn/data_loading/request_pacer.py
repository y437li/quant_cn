"""Polite, retried requests to public websites, shared by threads (D-096)."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TypeVar

from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError

T = TypeVar("T")
logger = logging.getLogger(__name__)


class RequestPacer:
    """
    Purpose:
        Run one request callable at a time-spaced rate with retries: request starts are at least
        `min_interval_s` apart across all threads sharing the pacer, and a call raising OSError,
        ValueError or KeyError is retried after `retry_sleep_s` up to `retries` times.

    Contract:
        Input:
            clock:          Clock       -- sleeps and monotonic time
            vendor:         str         -- name used in messages
            min_interval_s: float >= 0  -- minimum gap between request starts
            retries:        int >= 0    -- retries after the first failure
            retry_sleep_s:  float >= 0  -- pause before each retry
        Output:
            instance; `run`, `record_throttle`
        Raises:
            (none at construction)

    Used by:
        data_loading.BaseWebClient       -- paces list requests
        data_loading.DocumentDownloader  -- paces PDF downloads across worker threads
        data_loading.DeepSeekClient      -- paces LLM calls

    Test cases:
        TC-RP-001  a failing call is retried, then raises DataSourceError naming the attempts
        TC-RP-002  consecutive calls are spaced by at least min_interval_s
        TC-RP-003  record_throttle holds every later request start for the cooldown
    """

    def __init__(
        self,
        clock: Clock,
        vendor: str,
        min_interval_s: float = 0.5,
        retries: int = 4,
        retry_sleep_s: float = 10.0,
    ) -> None:
        self._clock = clock
        self._vendor = vendor
        self._min_interval_s = min_interval_s
        self._retries = retries
        self._retry_sleep_s = retry_sleep_s
        self._lock = threading.Lock()
        self._next_start: float | None = None

    def run(self, label: str, call: Callable[[], T]) -> T:
        """
        Purpose:
            Wait for this request's turn, run `call`, retry on transport errors.

        Contract:
            Input:
                label: str                -- what is fetched (for messages)
                call:  Callable[[], T]    -- performs one request
            Output:
                T  -- the call's result
            Raises:
                DataSourceError  -- every attempt failed
        """
        failures = 0
        while True:
            self._wait_turn()
            try:
                return call()
            except (OSError, ValueError, KeyError) as exc:
                failures += 1
                if failures > self._retries:
                    raise DataSourceError(
                        f"{self._vendor} {label}: failed after {failures} attempts: {exc}"
                    ) from exc
                logger.warning("%s %s attempt %s failed: %s", self._vendor, label, failures, exc)
                self._clock.sleep(self._retry_sleep_s)

    def record_throttle(self, cooldown_s: float) -> None:
        """
        Purpose:
            Record that the site throttled us: no request (from any thread) starts for
            `cooldown_s` seconds from now.

        Contract:
            Input:
                cooldown_s: float >= 0
            Output:
                None
            Raises:
                (none)
        """
        with self._lock:
            until = self._clock.get_monotonic() + cooldown_s
            self._next_start = until if self._next_start is None else max(self._next_start, until)
        logger.warning("%s throttled: pausing all requests for %.0f s", self._vendor, cooldown_s)

    def _wait_turn(self) -> None:
        with self._lock:
            now = self._clock.get_monotonic()
            start = now if self._next_start is None else max(now, self._next_start)
            self._next_start = start + self._min_interval_s
        if start > now:
            self._clock.sleep(start - now)
