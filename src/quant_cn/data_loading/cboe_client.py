"""CBOE volatility index history from the public daily-price CSV files (D-152)."""

from __future__ import annotations

import functools
import io
import logging
import re
from collections.abc import Mapping, Sequence

import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.base_web_client import BaseWebClient
from quant_cn.data_loading.http_transport import HttpTransport

logger = logging.getLogger(__name__)
CSV_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{index}_History.csv"
COLUMNS = ["index_code", "trade_date", "open", "high", "low", "close"]
PRICES = ["open", "high", "low", "close"]
US_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
INDEX_CODE = re.compile(r"^[A-Z0-9]{2,12}$")


class CboeClient(BaseWebClient):
    """
    Purpose:
        The full daily history of one CBOE index (VIX by default) from CBOE's public CSV
        (`CSV_URL`, columns DATE MM/DD/YYYY, OPEN, HIGH, LOW, CLOSE; no key needed). One GET
        returns every day since 1990, so the dataset is refreshed by overwrite. Dates become
        YYYYMMDD; prices are float. Rows with an unparseable date are dropped with a log line.

    Contract:
        Input:
            BaseWebClient dependencies (clock, transport, min_interval_s, retries, ...)
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "cboe"

    Test cases:
        TC-CBC-001  CSV parsed to COLUMNS: YYYYMMDD dates, float prices, index_code, sorted
        TC-CBC-002  a bad date row is dropped; an invalid index code, a CSV without the
                    expected header or a network failure after retries raises DataSourceError
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

    def get_vendor_name(self) -> str:
        """
        Purpose:
            Vendor name for messages.

        Contract:
            Input:
                (none)
            Output:
                str  -- "cboe"
            Raises:
                (none)
        """
        return "cboe"

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Every day of one index.

        Contract:
            Input:
                api_name: str                -- ignored ("daily_prices")
                params:   Mapping[str, str]  -- index (CBOE code, default "VIX")
                fields:   Sequence[str]      -- ignored; output columns are COLUMNS
            Output:
                DataFrame  -- COLUMNS; prices float64, index_code / trade_date text, sorted by
                              trade_date, unique trade_date
            Raises:
                DataSourceError  -- invalid index code, unexpected CSV, failure after retries
        """
        index = params.get("index", "VIX")
        if not INDEX_CODE.match(index):
            raise DataSourceError(f"cboe: invalid index code {index!r}")
        url = CSV_URL.format(index=index)
        body = self._pacer.run(f"cboe {index}", functools.partial(self._fetch, url))
        return self._to_frame(body, index)

    def _fetch(self, url: str) -> bytes:
        return self._transport.fetch_bytes(url, self._timeout_s)

    @staticmethod
    def _to_frame(body: bytes, index: str) -> pd.DataFrame:
        raw = pd.read_csv(io.BytesIO(body), dtype=str)
        raw.columns = [str(c).strip().upper() for c in raw.columns]
        if not {"DATE", "OPEN", "HIGH", "LOW", "CLOSE"} <= set(raw.columns):
            raise DataSourceError(f"cboe {index}: unexpected columns {list(raw.columns)[:8]}")
        parts = raw["DATE"].str.strip().str.extract(US_DATE)
        bad = parts.isna().any(axis=1)
        if bad.any():
            logger.info("cboe %s: %d rows with an unparseable date dropped", index, int(bad.sum()))
        out = pd.DataFrame({"index_code": index, "trade_date": parts[2] + parts[0] + parts[1]})
        for col in PRICES:
            out[col] = pd.to_numeric(raw[col.upper()], errors="coerce").astype("float64")
        out = out[~bad].drop_duplicates("trade_date", keep="last").sort_values("trade_date")
        out[["index_code", "trade_date"]] = out[["index_code", "trade_date"]].astype("string")
        return out[COLUMNS].reset_index(drop=True)
