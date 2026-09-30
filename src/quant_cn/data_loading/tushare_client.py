"""Tushare Pro over raw HTTP: paging, retries, rate-limit waits, permission errors (D-003)."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.clock import Clock
from quant_cn.core.config import TushareConfig
from quant_cn.core.exceptions import ConfigError, DataSourceError, PermissionDeniedError
from quant_cn.data_loading.http_transport import HttpTransport

CAP_STEP = 100  # per-call caps seen: 400 (stk_surv), 2000, 4000, 5500 (stk_holdernumber), 6000

logger = logging.getLogger(__name__)


class TushareClient(BaseApiClient):
    """
    Purpose:
        Query Tushare Pro: one logical query follows limit/offset paging until a short page and
        returns all rows; rate-limit replies wait and retry without spending retries; permission
        replies fail fast as PermissionDeniedError; other failures retry up to `retries`.

    Contract:
        Input:
            tushare_config: TushareConfig   -- url, token, paging and retry settings
            clock:     Clock                -- sleeps
            transport: HttpTransport | None -- default HttpTransport()
        Output:
            instance; `query`
        Raises:
            (none at construction; an empty token fails at query time so dry runs need no token)

    Used by:
        cli.ServiceBuilder  -- injected type or call

    Test cases:
        TC-TC-001  pages until a short page and concatenates pages in order
        TC-TC-002  rate-limit reply sleeps rate_limit_sleep_s then succeeds, retries not spent
        TC-TC-003  non-zero code on every attempt raises DataSourceError after `retries` retries
        TC-TC-004  permission reply raises PermissionDeniedError without retrying
        TC-TC-005  network error retried with retry_sleep_s, then succeeds
        TC-TC-006  empty result returns zero rows with the requested columns
        TC-TC-007  query with an empty token raises ConfigError
        TC-TC-008  a short page of a round size (endpoint cap < limit) keeps paging by rows received
        TC-TC-009  a page identical to the previous one raises DataSourceError (offset ignored)
    """

    def __init__(
        self, tushare_config: TushareConfig, clock: Clock, transport: HttpTransport | None = None
    ) -> None:
        self._config = tushare_config
        self._clock = clock
        self._transport = transport or HttpTransport()

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Fetch every page of one query.

        Contract:
            Input:
                api_name: str; params: Mapping[str, str] (no limit/offset); fields: Sequence[str]
            Output:
                DataFrame  -- vendor column names, pages concatenated in order; zero rows allowed
            Raises:
                ConfigError            -- TUSHARE_TOKEN not set
                PermissionDeniedError  -- account lacks the endpoint
                DataSourceError        -- failure after retries or too many rate-limit waits
        """
        if not self._config.token:
            raise ConfigError("TUSHARE_TOKEN is not set (put it in .env)")
        page = self._config.page_size
        rows: list[list[Any]] = []
        columns: list[str] = list(fields)
        offset = 0
        previous: list[Any] = []
        while True:
            data = self._fetch_page(api_name, {**params, "limit": page, "offset": offset}, fields)
            columns = list(data.get("fields") or columns)
            items = data.get("items") or []
            if items and items == previous:
                # share_float ignores offset and repeats the page forever (D-081): never loop
                raise DataSourceError(
                    f"{api_name}: offset ignored (page {offset} repeats); narrow the query"
                )
            rows.extend(items)
            if not self._has_more(len(items), page):
                break
            previous = items
            offset += len(items)
        return pd.DataFrame(rows, columns=columns)

    @staticmethod
    def _has_more(n_items: int, page: int) -> bool:
        # A full page means more; so does a short page of a round size: several endpoints cap a
        # call below `limit` (fut_holding 4000, fund_share 2000) and look finished otherwise (D-076)
        return n_items > 0 and (n_items >= page or n_items % CAP_STEP == 0)

    def _fetch_page(
        self, api_name: str, params: Mapping[str, object], fields: Sequence[str]
    ) -> dict[str, Any]:
        payload = {
            "api_name": api_name,
            "token": self._config.token,
            "params": dict(params),
            "fields": ",".join(fields),
        }
        failures = 0
        waits = 0
        while True:
            message = self._fetch_once(payload)
            if isinstance(message, dict):
                return message
            if self._is_match(message, self._config.permission_markers):
                raise PermissionDeniedError(f"{api_name}: {message}")
            if self._is_match(message, self._config.rate_limit_markers):
                waits += 1
                if waits > self._config.max_rate_limit_waits:
                    raise DataSourceError(f"{api_name}: rate limited {waits} times: {message}")
                logger.info(
                    "%s rate limited, sleeping %ss", api_name, self._config.rate_limit_sleep_s
                )
                self._clock.sleep(self._config.rate_limit_sleep_s)
                continue
            failures += 1
            if failures > self._config.retries:
                raise DataSourceError(f"{api_name}: failed after {failures} attempts: {message}")
            logger.warning("%s attempt %s failed: %s", api_name, failures, message)
            self._clock.sleep(self._config.retry_sleep_s)

    def _fetch_once(self, payload: dict[str, Any]) -> dict[str, Any] | str:
        """Return the `data` object on success, else the error message."""
        try:
            response = self._transport.fetch_json(self._config.url, payload, self._config.timeout_s)
        except (OSError, ValueError) as exc:
            return f"transport error: {exc}"
        if response.get("code") != 0:
            return str(response.get("msg") or f"code {response.get('code')}")
        data = response.get("data")
        if not isinstance(data, dict):
            return "response has no data object"
        return data

    @staticmethod
    def _is_match(message: str, markers: Sequence[str]) -> bool:
        return any(marker in message for marker in markers)
