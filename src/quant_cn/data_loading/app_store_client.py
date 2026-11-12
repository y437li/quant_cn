"""Apple App Store top charts from the public iTunes RSS feeds (D-137)."""

from __future__ import annotations

import functools
import logging
import urllib.error
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.base_web_client import BaseWebClient
from quant_cn.data_loading.http_transport import HttpTransport

logger = logging.getLogger(__name__)
FEED_URL = "https://itunes.apple.com/{country}/rss/{chart}/limit={limit}/genre={genre}/json"
CHART_NAMES = {"topgrossingapplications": "grossing", "topfreeapplications": "free",
               "toppaidapplications": "paid"}  # fmt: skip
COLUMNS = [
    "country", "chart", "rank", "app_id", "name", "artist", "artist_id",
    "bundle_id", "category_id", "release_date", "price", "currency", "captured_at",
]  # fmt: skip
TEXT = [c for c in COLUMNS if c not in ("rank", "price")]


class AppStoreClient(BaseWebClient):
    """
    Purpose:
        One country's App Store top charts as rows. For each chart in `charts` it GETs the
        legacy iTunes RSS JSON feed (`FEED_URL`; Apple caps it at 100 entries whatever the
        limit) and flattens every entry to COLUMNS: rank = 1-based position in the feed,
        app_id = `im:id`, artist_id from the artist link, release_date YYYYMMDD, price as a
        float with its currency. `captured_at` is the Clock time "YYYYMMDD HH:MM:SS" (charts move
        within the day). There is no `capture_date` column: the fetcher adds it as its key_field
        (BaseFetcher fills a key_field only when the column is absent). A market with
        no store (HTTP 400 / 404) or an empty feed gives zero rows for that chart and a log line.

    Contract:
        Input:
            BaseWebClient dependencies (clock, transport, min_interval_s, retries, ...)
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "apple"

    Test cases:
        TC-ASC-001  two charts flattened to COLUMNS: rank order, ids, release date, price
        TC-ASC-002  a single-entry feed (dict, not list) and an empty feed both parse
        TC-ASC-003  HTTP 404 market gives zero rows; a network failure after retries raises
                    DataSourceError; a missing country or unknown chart raises DataSourceError
    """

    def __init__(
        self,
        clock: Clock,
        transport: HttpTransport | None = None,
        min_interval_s: float = 1.0,
        retries: int = 3,
        retry_sleep_s: float = 10.0,
    ) -> None:
        super().__init__(clock, transport, min_interval_s, retries, retry_sleep_s)
        self._clock = clock

    def get_vendor_name(self) -> str:
        """
        Purpose:
            Vendor name for messages.

        Contract:
            Input:
                (none)
            Output:
                str  -- "apple"
            Raises:
                (none)
        """
        return "apple"

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Every chart in `params["charts"]` for one country, flattened.

        Contract:
            Input:
                api_name: str                -- ignored ("rss")
                params:   Mapping[str, str]  -- country (two-letter store code), charts
                                                (comma-separated CHART_NAMES keys), genre
                                                (default "6014" games), limit (default "200")
                fields:   Sequence[str]      -- ignored; output columns are COLUMNS
            Output:
                DataFrame  -- COLUMNS; rank int, price float, the rest text; zero rows allowed
            Raises:
                DataSourceError  -- no country, unknown chart, or failure after retries
        """
        country = params.get("country", "")
        charts = [c for c in params.get("charts", "").split(",") if c]
        if not country or not charts or any(c not in CHART_NAMES for c in charts):
            raise DataSourceError(f"apple: need a country and charts from {sorted(CHART_NAMES)}")
        stamp = self._clock.get_now().strftime("%Y%m%d %H:%M:%S")
        rows: list[dict[str, Any]] = []
        for chart in charts:
            url = FEED_URL.format(country=country, chart=chart, limit=params.get("limit", "200"),
                                  genre=params.get("genre", "6014"))  # fmt: skip
            entries = self._pacer.run(f"{country} {chart}", functools.partial(self._fetch, url))
            if not entries:
                logger.info("apple %s %s: empty chart", country, chart)
            for rank, entry in enumerate(entries, start=1):
                rows.append(self._to_row(entry, rank, country, CHART_NAMES[chart], stamp))
        return self._to_frame(rows)

    def _fetch(self, url: str) -> list[dict[str, Any]]:
        try:
            reply = self._transport.fetch_get_json(url, self._timeout_s)
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 404):
                logger.info("apple %s: HTTP %s, no store or chart", url, exc.code)
                return []
            raise
        entries = reply.get("feed", {}).get("entry", [])
        return [entries] if isinstance(entries, dict) else list(entries)

    @staticmethod
    def _to_row(
        entry: Mapping[str, Any], rank: int, country: str, chart: str, stamp: str
    ) -> dict[str, Any]:
        def label(key: str) -> Any:
            return (entry.get(key) or {}).get("label")

        ident = (entry.get("id") or {}).get("attributes") or {}
        artist = entry.get("im:artist") or {}
        artist_url = str((artist.get("attributes") or {}).get("href") or "")
        tail = artist_url.rsplit("/id", 1)[1] if "/id" in artist_url else ""
        artist_id = tail.split("?", maxsplit=1)[0] or None
        price = (entry.get("im:price") or {}).get("attributes") or {}
        category = (entry.get("category") or {}).get("attributes") or {}
        release = str(label("im:releaseDate") or "")[:10].replace("-", "")
        return {
            "country": country, "chart": chart, "rank": rank,
            "app_id": ident.get("im:id"), "name": label("im:name"), "artist": artist.get("label"),
            "artist_id": artist_id, "bundle_id": ident.get("im:bundleId"),
            "category_id": category.get("im:id"), "release_date": release or None,
            "price": price.get("amount"), "currency": price.get("currency"), "captured_at": stamp,
        }  # fmt: skip

    @staticmethod
    def _to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
        out = pd.DataFrame(rows, columns=COLUMNS)
        out["rank"] = out["rank"].astype("int64")
        out["price"] = pd.to_numeric(out["price"], errors="coerce").astype("float64")
        out[TEXT] = out[TEXT].astype("string")
        return out
