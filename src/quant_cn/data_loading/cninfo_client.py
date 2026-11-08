"""CNINFO (巨潮资讯) announcement metadata, the industry-chain graph document source (D-096)."""

from __future__ import annotations

import datetime as dt
import functools
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.base_web_client import BaseWebClient
from quant_cn.data_loading.http_transport import HttpTransport

logger = logging.getLogger(__name__)
QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
PAGE_SIZE = 30  # the site ignores larger values
MAX_ROWS = (
    3000  # the site repeats page 101 for every later page: one query yields at most ~3,000 rows
)
PLATES = (
    "szmb",
    "szcy",
    "shmb",
    "shkcp",
    "bj",
)  # a partition of the market (sz = szmb + szcy, ...)
BEIJING = dt.timezone(dt.timedelta(hours=8))
_TAG = re.compile(r"</?em>")
COLUMNS = [
    "ann_id", "sec_code", "sec_name", "org_id", "title", "ann_time", "ann_date",
    "adjunct_url", "adjunct_size", "adjunct_type", "column_id", "ann_type", "page_column",
]  # fmt: skip
_VENDOR = {
    "announcementId": "ann_id", "secCode": "sec_code", "secName": "sec_name", "orgId": "org_id",
    "adjunctUrl": "adjunct_url", "adjunctSize": "adjunct_size", "adjunctType": "adjunct_type",
    "columnId": "column_id", "announcementType": "ann_type", "pageColumn": "page_column",
}  # fmt: skip


class CninfoClient(BaseWebClient):
    """
    Purpose:
        List CNINFO announcements for the whole A-share market (`column=szse` covers SZ, SH and
        BJ) over a date range, optionally one category (e.g. "category_ndbg_szsh" annual
        reports), following `pageNum` until `totalpages`. Rows are de-duplicated on
        (ann_id, sec_code) because the list can shift while a busy day is paged. One query
        reaches at most MAX_ROWS rows (later pages repeat), so a larger range is split in date
        halves down to one day and then by board (PLATES); what is still cut off is logged; `<em>`
        highlight tags are removed from titles; `announcementTime` (epoch ms) becomes
        `ann_time` "YYYYMMDD HH:MM:SS" and `ann_date` YYYYMMDD in Beijing time.

    Contract:
        Input:
            BaseWebClient dependencies (clock, transport, min_interval_s, retries, ...)
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "cninfo"

    Test cases:
        TC-CNC-001  a single day pages until totalpages; columns renamed; seDate from ann_date
        TC-CNC-002  duplicates across pages dropped; <em> tags stripped; time in Beijing
        TC-CNC-003  an empty day returns zero rows with COLUMNS; a missing date raises
        TC-CNC-004  a range above MAX_ROWS is split into halves; a single day by board
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
                str  -- "cninfo"
            Raises:
                (none)
        """
        return "cninfo"

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Every announcement in the date range (and category), all pages.

        Contract:
            Input:
                api_name: str                -- ignored ("hisAnnouncement")
                params:   Mapping[str, str]  -- ann_date (one day) or start_date + end_date
                                                (YYYYMMDD); optional category, searchkey
                fields:   Sequence[str]      -- ignored; output columns are COLUMNS
            Output:
                DataFrame  -- COLUMNS, text except adjunct_size (KB); zero rows allowed
            Raises:
                DataSourceError  -- no date given, or failure after retries
        """
        start = params.get("ann_date") or params.get("start_date")
        end = params.get("ann_date") or params.get("end_date")
        if not start or not end:
            raise DataSourceError("cninfo: query needs ann_date or start_date and end_date")
        rows = self._list_rows(start, end, params, plate="")
        return self._to_frame(rows)

    def _list_rows(
        self, start: str, end: str, params: Mapping[str, str], plate: str
    ) -> list[dict[str, Any]]:
        """All rows of [start, end] (and plate), splitting the query while it exceeds MAX_ROWS:
        first the date range in halves down to one day, then one day by board (PLATES)."""
        form = self._build_form(start, end, params, plate)
        first = self._pacer.run(f"{start}-{end} {plate} p1", functools.partial(self._fetch, form))
        total = int(first.get("totalAnnouncement") or 0)
        if total > MAX_ROWS and start != end:
            mid = self._to_day(
                self._to_date(start) + (self._to_date(end) - self._to_date(start)) // 2
            )
            after = self._to_day(self._to_date(mid) + dt.timedelta(days=1))
            return self._list_rows(start, mid, params, plate) + self._list_rows(
                after, end, params, plate
            )
        if total > MAX_ROWS and not plate:
            return [row for p in PLATES for row in self._list_rows(start, end, params, p)]
        if total > MAX_ROWS:
            logger.warning(
                "cninfo %s %s %s: %s rows, only %s reachable", start, plate, params, total, MAX_ROWS
            )
        rows: list[dict[str, Any]] = list(first.get("announcements") or [])
        pages = min(int(first.get("totalpages") or 0), MAX_ROWS // PAGE_SIZE)
        for page in range(2, pages + 1):
            form = {**form, "pageNum": str(page)}
            reply = self._pacer.run(
                f"{start}-{end} {plate} p{page}", functools.partial(self._fetch, form)
            )
            rows.extend(reply.get("announcements") or [])
        return rows

    def _build_form(
        self, start: str, end: str, params: Mapping[str, str], plate: str
    ) -> dict[str, str]:
        return {
            "pageNum": "1", "pageSize": str(PAGE_SIZE), "column": "szse", "tabName": "fulltext",
            "plate": plate, "stock": "", "searchkey": params.get("searchkey", ""), "secid": "",
            "category": params.get("category", ""), "trade": "",
            "seDate": f"{self._to_iso(start)}~{self._to_iso(end)}",
            "sortName": "", "sortType": "", "isHLtitle": "true",
        }  # fmt: skip

    @staticmethod
    def _to_date(day: str) -> dt.date:
        return dt.date(int(day[:4]), int(day[4:6]), int(day[6:8]))

    @staticmethod
    def _to_day(date: dt.date) -> str:
        return date.strftime("%Y%m%d")

    def _fetch(self, form: Mapping[str, str]) -> dict[str, Any]:
        reply = self._transport.fetch_form_json(QUERY_URL, form, self._timeout_s)
        if "totalpages" not in reply:
            raise ValueError("reply has no totalpages")
        return reply

    @staticmethod
    def _to_iso(day: str) -> str:
        return f"{day[:4]}-{day[4:6]}-{day[6:8]}"

    @staticmethod
    def _to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame({c: pd.Series(dtype=object) for c in COLUMNS})
        df = pd.DataFrame(rows).rename(columns=_VENDOR)
        stamp = pd.to_datetime(df["announcementTime"], unit="ms", utc=True).dt.tz_convert(BEIJING)
        df["ann_time"] = stamp.dt.strftime("%Y%m%d %H:%M:%S")
        df["ann_date"] = stamp.dt.strftime("%Y%m%d")
        df["title"] = df["announcementTitle"].fillna("").map(lambda t: _TAG.sub("", t).strip())
        for column in COLUMNS:
            if column not in df.columns:
                df[column] = None
        out = df[COLUMNS].drop_duplicates(subset=["ann_id", "sec_code"]).reset_index(drop=True)
        text = [c for c in COLUMNS if c != "adjunct_size"]
        out[text] = out[text].map(lambda v: None if v is None or v != v else str(v))  # noqa: PLR0124 -- NaN
        out["adjunct_size"] = pd.to_numeric(out["adjunct_size"], errors="coerce")
        return out
