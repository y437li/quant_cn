from __future__ import annotations

import http.client
import urllib.request
from typing import Any

import pytest

from quant_cn.data_loading.http_transport import HttpTransport


class CutResponse:
    """Context-managed response whose read() fails mid-body."""

    def __enter__(self) -> CutResponse:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self) -> bytes:
        raise http.client.IncompleteRead(b"partial")


# TC-HT-001
def test_tc_ht_001_incomplete_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: CutResponse())
    transport = HttpTransport()
    with pytest.raises(OSError, match="incomplete response"):
        transport.fetch_bytes("http://example.invalid/a.pdf", 5)
    with pytest.raises(OSError, match="incomplete response"):
        transport.fetch_form_json("http://example.invalid/q", {"a": "1"}, 5)
