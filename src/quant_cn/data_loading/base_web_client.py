"""Shared transport and pacing for clients that page public websites (D-096)."""

from __future__ import annotations

from abc import abstractmethod

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.clock import Clock
from quant_cn.data_loading.http_transport import HttpTransport
from quant_cn.data_loading.request_pacer import RequestPacer


class BaseWebClient(BaseApiClient):
    """
    Purpose:
        Base for vendor clients that page a public website's JSON API (CNINFO, Eastmoney). It holds
        the transport, the timeout and a RequestPacer. Every request is spaced by `min_interval_s`
        and transport failures are retried after `retry_sleep_s`, so a long sweep survives short
        outages without hammering the site.

    Contract:
        Input:
            clock:          Clock                -- sleeps and monotonic time
            transport:      HttpTransport | None -- default HttpTransport()
            min_interval_s: float >= 0           -- minimum gap between two requests
            retries:        int >= 0             -- retries after the first failure
            retry_sleep_s:  float >= 0           -- pause before each retry
            timeout_s:      float > 0            -- per-request timeout
        Output:
            instance; subclasses implement `query` and `get_vendor_name`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        data_loading.CninfoClient          -- subclass
        data_loading.EastmoneyReportClient -- subclass

    Test cases:
        TC-BWC-001  (via CninfoClient) a failing request is retried, then raises DataSourceError
        TC-BWC-002  (via CninfoClient) consecutive page requests are spaced by min_interval_s
    """

    def __init__(
        self,
        clock: Clock,
        transport: HttpTransport | None = None,
        min_interval_s: float = 0.5,
        retries: int = 4,
        retry_sleep_s: float = 10.0,
        timeout_s: float = 30.0,
    ) -> None:
        self._transport = transport or HttpTransport()
        self._timeout_s = timeout_s
        self._pacer = RequestPacer(
            clock, self.get_vendor_name(), min_interval_s, retries, retry_sleep_s
        )

    @abstractmethod
    def get_vendor_name(self) -> str:
        """
        Purpose:
            Short vendor name used in error messages.

        Contract:
            Input:
                (none)
            Output:
                str
            Raises:
                (none)
        """
