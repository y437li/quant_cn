"""Eastmoney research-report lists: broker stock and industry reports with PDF links (D-100)."""

from __future__ import annotations

import functools
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.base_web_client import BaseWebClient
from quant_cn.data_loading.http_transport import HttpTransport

LIST_URL = "https://reportapi.eastmoney.com/report/list"
PAGE_SIZE = 100
COLUMNS = [
    "info_code", "publish_date", "title", "report_kind", "stock_code", "stock_name", "org_code",
    "org_name", "researcher", "industry_code", "industry_name", "em_industry_code", "rating",
    "rating_change", "attach_pages", "attach_size",
]  # fmt: skip
_VENDOR = {
    "infoCode": "info_code", "stockCode": "stock_code", "stockName": "stock_name",
    "orgCode": "org_code", "orgSName": "org_name", "industryCode": "industry_code",
    "industryName": "industry_name", "emIndustryCode": "em_industry_code",
    "emRatingName": "rating", "ratingChange": "rating_change", "attachPages": "attach_pages",
    "attachSize": "attach_size",
}  # fmt: skip
NUMERIC = ("attach_pages", "attach_size")
KINDS = {"0": "stock", "1": "industry", "2": "strategy"}


class EastmoneyReportClient(BaseWebClient):
    """
    Purpose:
        List Eastmoney (东方财富) broker research reports published in a date range for one
        report kind (`q_type` "0" stock, "1" industry, "2" strategy), following `pageNo` until
        `TotalPage`. The PDF of a row is https://pdf.dfcfw.com/pdf/H3_<info_code>_1.pdf.
        `publishDate` carries no time of day, so `publish_date` is YYYYMMDD and the lake rule
        makes it usable from the next session.

    Contract:
        Input:
            BaseWebClient dependencies
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "eastmoney"

    Test cases:
        TC-EMR-001  pages until TotalPage; columns renamed; dates YYYYMMDD; kind from q_type
        TC-EMR-002  an empty range returns zero rows with COLUMNS; unknown q_type raises
    """

    def __init__(
        self,
        clock: Clock,
        transport: HttpTransport | None = None,
        min_interval_s: float = 0.5,
        retries: int = 4,
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
                str  -- "eastmoney"
            Raises:
                (none)
        """
        return "eastmoney"

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Every report of one kind published in [start_date, end_date].

        Contract:
            Input:
                api_name: str                -- ignored ("report_list")
                params:   Mapping[str, str]  -- start_date, end_date (YYYYMMDD), q_type
                fields:   Sequence[str]      -- ignored; output columns are COLUMNS
            Output:
                DataFrame  -- COLUMNS; attach_pages / attach_size numeric, others text
            Raises:
                DataSourceError  -- q_type not in KINDS, or failure after retries
        """
        q_type = params.get("q_type", "")
        if q_type not in KINDS:
            raise DataSourceError(f"eastmoney: q_type must be one of {sorted(KINDS)}")
        start, end = params["start_date"], params["end_date"]
        rows: list[dict[str, Any]] = []
        page, pages = 1, 1
        while page <= pages:
            url = self._build_url(start, end, q_type, page)
            reply = self._pacer.run(
                f"{start}-{end} page {page}", functools.partial(self._fetch, url)
            )
            pages = int(reply.get("TotalPage") or 0)
            rows.extend(reply.get("data") or [])
            page += 1
        return self._to_frame(rows, KINDS[q_type])

    def _fetch(self, url: str) -> dict[str, Any]:
        reply = self._transport.fetch_get_json(url, self._timeout_s)
        if "TotalPage" not in reply:
            raise ValueError("reply has no TotalPage")
        return reply

    @staticmethod
    def _build_url(start: str, end: str, q_type: str, page: int) -> str:
        query = {
            "industryCode": "*", "pageSize": str(PAGE_SIZE), "industry": "*", "rating": "*",
            "ratingChange": "*", "beginTime": f"{start[:4]}-{start[4:6]}-{start[6:8]}",
            "endTime": f"{end[:4]}-{end[4:6]}-{end[6:8]}", "pageNo": str(page), "qType": q_type,
        }  # fmt: skip
        return f"{LIST_URL}?{urllib.parse.urlencode(query)}"

    @staticmethod
    def _to_frame(rows: list[dict[str, Any]], kind: str) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame({c: pd.Series(dtype=object) for c in COLUMNS})
        df = pd.DataFrame(rows).rename(columns=_VENDOR)
        df["publish_date"] = df["publishDate"].astype(str).str[:10].str.replace("-", "")
        df["report_kind"] = kind
        for column in COLUMNS:
            if column not in df.columns:
                df[column] = None
        out = df[COLUMNS].drop_duplicates(subset=["info_code"]).reset_index(drop=True)
        text = [c for c in COLUMNS if c not in NUMERIC]
        out[text] = out[text].map(lambda v: None if v is None or v != v or v == "" else str(v))  # noqa: PLR0124 -- NaN
        for column in NUMERIC:
            out[column] = pd.to_numeric(out[column], errors="coerce")
        return out
