"""HTTP calls used by the vendor clients (JSON POST, form POST, GET); the seam tests replace."""

from __future__ import annotations

import http.client
import json
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any, cast

_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Accept": "*/*"}


class HttpTransport:
    """
    Purpose:
        Send one HTTP request and return the decoded JSON object or the raw bytes: a JSON POST
        (Tushare), a form POST (CNINFO, D-096), a GET returning JSON (Eastmoney report lists) and
        a GET returning bytes (PDF downloads). Browser-like User-Agent on every call.

    Contract:
        Input:
            (none)
        Output:
            instance; `fetch_json`, `fetch_form_json`, `fetch_get_json`, `fetch_bytes`
        Raises:
            (none at construction)

    Used by:
        data_loading.TushareClient         -- default transport
        data_loading.CninfoClient          -- default transport
        data_loading.EastmoneyReportClient -- default transport
        data_loading.BaseWebClient         -- default transport
        data_loading.DocumentDownloader    -- default transport
        data_loading.DeepSeekClient        -- default transport

    Test cases:
        TC-TC-001  (via fake transport subclass) client pages until a short page
        TC-HT-001  a body cut mid-read (IncompleteRead) surfaces as OSError
    """

    def fetch_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        timeout: float,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Purpose:
            POST `payload` as JSON to `url`.

        Contract:
            Input:
                url: str; payload: Mapping (JSON-serialisable); timeout: float seconds
                headers: Mapping[str, str] | None  -- extra headers (e.g. Authorization)
            Output:
                dict  -- decoded response body
            Raises:
                OSError     -- network failure or timeout (urllib.error.URLError is an OSError)
                ValueError  -- body is not a JSON object
        """
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", **dict(headers or {})},
            method="POST",
        )
        data = json.loads(self._read_body(request, timeout).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("response is not a JSON object")
        return cast(dict[str, Any], data)

    def fetch_form_json(self, url: str, form: Mapping[str, str], timeout: float) -> dict[str, Any]:
        """
        Purpose:
            POST `form` url-encoded to `url` and decode the JSON reply.

        Contract:
            Input:
                url: str; form: Mapping[str, str]; timeout: float seconds
            Output:
                dict  -- decoded response body
            Raises:
                OSError     -- network failure or timeout
                ValueError  -- body is not a JSON object
        """
        request = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(dict(form)).encode("utf-8"),
            headers={
                **_HEADERS,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            method="POST",
        )
        return self._read_json(request, timeout)

    def fetch_get_json(self, url: str, timeout: float) -> dict[str, Any]:
        """
        Purpose:
            GET `url` and decode the JSON reply.

        Contract:
            Input:
                url: str; timeout: float seconds
            Output:
                dict  -- decoded response body
            Raises:
                OSError     -- network failure or timeout
                ValueError  -- body is not a JSON object
        """
        return self._read_json(urllib.request.Request(url, headers=_HEADERS), timeout)

    def fetch_bytes(self, url: str, timeout: float) -> bytes:
        """
        Purpose:
            GET `url` and return the body (a PDF download).

        Contract:
            Input:
                url: str; timeout: float seconds
            Output:
                bytes  -- response body
            Raises:
                OSError  -- network failure, timeout or HTTP error status
        """
        request = urllib.request.Request(url, headers=_HEADERS)
        return self._read_body(request, timeout)

    @staticmethod
    def _read_body(request: urllib.request.Request, timeout: float) -> bytes:
        """The response body; a connection cut mid-body (http.client.IncompleteRead and other
        HTTPException) is re-raised as OSError so callers retry it like any network failure."""
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return cast(bytes, response.read())
        except http.client.HTTPException as exc:
            raise OSError(f"incomplete response: {exc!r}"[:300]) from exc

    @staticmethod
    def _read_json(request: urllib.request.Request, timeout: float) -> dict[str, Any]:
        data = json.loads(HttpTransport._read_body(request, timeout).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("response is not a JSON object")
        return cast(dict[str, Any], data)
