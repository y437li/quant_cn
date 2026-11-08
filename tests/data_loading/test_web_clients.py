from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.cninfo_client import COLUMNS as CNINFO_COLUMNS
from quant_cn.data_loading.cninfo_client import CninfoClient
from quant_cn.data_loading.eastmoney_report_client import COLUMNS as EM_COLUMNS
from quant_cn.data_loading.eastmoney_report_client import EastmoneyReportClient
from quant_cn.data_loading.http_transport import HttpTransport
from tests.support import FakeClock

# 2026-11-06 09:30:00 Beijing = 01:30:00 UTC
STAMP = 1793928600000


class FakeWebTransport(HttpTransport):
    """Scripted replies (dict or exception) in order; records every request."""

    def __init__(self, replies: list[Any]) -> None:
        self.replies = list(replies)
        self.forms: list[dict[str, str]] = []
        self.urls: list[str] = []

    def fetch_form_json(self, url: str, form: Mapping[str, str], timeout: float) -> dict[str, Any]:
        self.forms.append(dict(form))
        return self._read_reply()

    def fetch_get_json(self, url: str, timeout: float) -> dict[str, Any]:
        self.urls.append(url)
        return self._read_reply()

    def _read_reply(self) -> dict[str, Any]:
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return dict(reply)


def build_announcement(
    ann_id: str, code: str = "300750", title: str = "2025年年度报告"
) -> dict[str, Any]:
    return {
        "announcementId": ann_id, "secCode": code, "secName": "宁德时代", "orgId": "gssz0300750",
        "announcementTitle": title, "announcementTime": STAMP,
        "adjunctUrl": f"finalpage/2026-11-06/{ann_id}.PDF", "adjunctSize": 1997,
        "adjunctType": "PDF", "columnId": "09020202", "announcementType": "01030101",
        "pageColumn": "SZCY",
    }  # fmt: skip


def build_report(code: str) -> dict[str, Any]:
    return {
        "infoCode": code, "publishDate": "2026-10-31 00:00:00.000", "title": "行业深度",
        "stockCode": "", "stockName": "", "orgCode": "1", "orgSName": "国元证券",
        "researcher": "李典", "industryCode": "482", "industryName": "一般零售",
        "emIndustryCode": "101018", "emRatingName": "增持", "ratingChange": 3,
        "attachPages": 32, "attachSize": 2214,
    }  # fmt: skip


# TC-BWC-001
def test_tc_bwc_001_retry_then_fail(clock: FakeClock) -> None:
    transport = FakeWebTransport([OSError("reset")] * 3)
    client = CninfoClient(clock, transport, retries=2, retry_sleep_s=7.0)
    with pytest.raises(DataSourceError, match="failed after 3 attempts"):
        client.query("hisAnnouncement", {"ann_date": "20261106"}, [])
    assert 7.0 in clock.sleeps and clock.sleeps.count(7.0) == 2


# TC-BWC-002
def test_tc_bwc_002_requests_spaced(clock: FakeClock) -> None:
    page = {"totalpages": 2, "announcements": [build_announcement("1")]}
    transport = FakeWebTransport([page, {**page, "announcements": [build_announcement("2")]}])
    client = CninfoClient(clock, transport, min_interval_s=0.5)
    client.query("hisAnnouncement", {"ann_date": "20261106"}, [])
    assert len(clock.sleeps) == 1 and clock.sleeps[0] == pytest.approx(0.5, abs=0.01)


# TC-CNC-001
def test_tc_cnc_001_pages_and_columns(clock: FakeClock) -> None:
    transport = FakeWebTransport(
        [
            {"totalpages": 2, "announcements": [build_announcement("1")]},
            {"totalpages": 2, "announcements": [build_announcement("2")]},
        ]
    )
    out = CninfoClient(clock, transport).query("x", {"ann_date": "20261106"}, [])
    assert [f["pageNum"] for f in transport.forms] == ["1", "2"]
    assert transport.forms[0]["seDate"] == "2026-11-06~2026-11-06"
    assert list(out.columns) == CNINFO_COLUMNS
    assert out["ann_id"].tolist() == ["1", "2"]
    assert out["adjunct_url"].iloc[0] == "finalpage/2026-11-06/1.PDF"
    assert out["adjunct_size"].iloc[0] == 1997


# TC-CNC-002
def test_tc_cnc_002_dedup_tags_time(clock: FakeClock) -> None:
    first = build_announcement("1", title="<em>投资者</em>关系活动记录表")
    transport = FakeWebTransport(
        [
            {"totalpages": 2, "announcements": [first]},
            {"totalpages": 2, "announcements": [first, build_announcement("1", code="123456")]},
        ]
    )
    out = CninfoClient(clock, transport).query(
        "x", {"start_date": "20261101", "end_date": "20261106", "category": "c"}, []
    )
    assert transport.forms[0]["category"] == "c"
    assert len(out) == 2
    assert out["title"].iloc[0] == "投资者关系活动记录表"
    assert out["ann_time"].iloc[0] == "20261106 09:30:00"
    assert out["ann_date"].iloc[0] == "20261106"


# TC-CNC-003
def test_tc_cnc_003_empty_and_missing_date(clock: FakeClock) -> None:
    transport = FakeWebTransport([{"totalpages": 0, "announcements": None}])
    out = CninfoClient(clock, transport).query("x", {"ann_date": "20261107"}, [])
    assert out.empty and list(out.columns) == CNINFO_COLUMNS
    with pytest.raises(DataSourceError, match="needs ann_date"):
        CninfoClient(clock, FakeWebTransport([])).query("x", {}, [])


# TC-EMR-001
def test_tc_emr_001_pages_and_columns(clock: FakeClock) -> None:
    transport = FakeWebTransport(
        [
            {"TotalPage": 2, "data": [build_report("A1")]},
            {"TotalPage": 2, "data": [build_report("A2")]},
        ]
    )
    out = EastmoneyReportClient(clock, transport).query(
        "report_list", {"start_date": "20261001", "end_date": "20261031", "q_type": "1"}, []
    )
    assert "beginTime=2026-10-01" in transport.urls[0] and "pageNo=2" in transport.urls[1]
    assert "qType=1" in transport.urls[0]
    assert list(out.columns) == EM_COLUMNS
    assert out["info_code"].tolist() == ["A1", "A2"]
    assert out["publish_date"].iloc[0] == "20261031"
    assert out["report_kind"].iloc[0] == "industry"
    assert out["stock_code"].iloc[0] is None
    assert out["rating_change"].iloc[0] == "3" and out["attach_pages"].iloc[0] == 32


# TC-EMR-002
def test_tc_emr_002_empty_and_bad_kind(clock: FakeClock) -> None:
    transport = FakeWebTransport([{"TotalPage": 0, "data": []}])
    out = EastmoneyReportClient(clock, transport).query(
        "report_list", {"start_date": "20261101", "end_date": "20261107", "q_type": "0"}, []
    )
    assert out.empty and list(out.columns) == EM_COLUMNS
    with pytest.raises(DataSourceError, match="q_type"):
        EastmoneyReportClient(clock, FakeWebTransport([])).query(
            "report_list", {"start_date": "20261101", "end_date": "20261107"}, []
        )


class SplittingTransport(FakeWebTransport):
    """Answers by (seDate, plate): a 2-day range is too big, so is the single busy day."""

    def __init__(self) -> None:
        super().__init__([])

    def fetch_form_json(self, url: str, form: Mapping[str, str], timeout: float) -> dict[str, Any]:
        self.forms.append(dict(form))
        key = (form["seDate"], form["plate"])
        if key in (("2026-04-28~2026-04-29", ""), ("2026-04-29~2026-04-29", "")):
            return {"totalAnnouncement": 5000, "totalpages": 167, "announcements": []}
        ann = build_announcement(f"{form['seDate'][:10]}-{form['plate'] or 'all'}")
        return {"totalAnnouncement": 1, "totalpages": 1, "announcements": [ann]}


# TC-CNC-004
def test_tc_cnc_004_split_over_cap(clock: FakeClock) -> None:
    transport = SplittingTransport()
    out = CninfoClient(clock, transport, min_interval_s=0.0).query(
        "x", {"start_date": "20260428", "end_date": "20260429"}, []
    )
    asked = [(f["seDate"], f["plate"]) for f in transport.forms]
    assert ("2026-04-28~2026-04-28", "") in asked
    assert {p for d, p in asked if d == "2026-04-29~2026-04-29" and p} == {
        "szmb",
        "szcy",
        "shmb",
        "shkcp",
        "bj",
    }
    assert len(out) == 6  # one row for the 28th plus one per board on the 29th
