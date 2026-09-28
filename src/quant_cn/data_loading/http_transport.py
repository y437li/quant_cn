"""JSON-over-HTTP POST used by the Tushare client; the seam tests replace."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Mapping
from typing import Any, cast


class HttpTransport:
    """
    Purpose:
        Send one JSON POST and return the decoded JSON object.

    Contract:
        Input:
            (none)
        Output:
            instance; `post`
        Raises:
            (none at construction)

    Used by:
        data_loading.TushareClient       -- default transport

    Test cases:
        TC-TC-001  (via fake transport subclass) client pages until a short page
    """

    def fetch_json(self, url: str, payload: Mapping[str, Any], timeout: float) -> dict[str, Any]:
        """
        Purpose:
            POST `payload` as JSON to `url`.

        Contract:
            Input:
                url: str; payload: Mapping (JSON-serialisable); timeout: float seconds
            Output:
                dict  -- decoded response body
            Raises:
                OSError     -- network failure or timeout (urllib.error.URLError is an OSError)
                ValueError  -- body is not a JSON object
        """
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise ValueError("response is not a JSON object")
        return cast(dict[str, Any], data)
