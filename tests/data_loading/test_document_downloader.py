from __future__ import annotations

import hashlib
import urllib.error

import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import ConfigError, DataSourceError
from quant_cn.data_loading.document_classifier import DocumentClassifier
from quant_cn.data_loading.document_downloader import DocumentDownloader
from quant_cn.data_loading.http_transport import HttpTransport
from quant_cn.data_loading.request_pacer import RequestPacer
from tests.support import FakeClock, MiniLake

PDF = b"%PDF-1.7 body"


class FakeFileTransport(HttpTransport):
    """Bytes per URL; an Exception value is raised; records requested URLs."""

    def __init__(self, bodies: dict[str, bytes | Exception]) -> None:
        self.bodies = bodies
        self.urls: list[str] = []

    def fetch_bytes(self, url: str, timeout: float) -> bytes:
        self.urls.append(url)
        body = self.bodies.get(url, PDF)
        if isinstance(body, Exception):
            raise body
        return body


def build_announcements() -> pd.DataFrame:
    rows = [
        ("1", "300750", "2025年年度报告", "20260310", "finalpage/2026-03-10/1.PDF"),
        ("2", "300750", "2025年年度报告摘要", "20260310", "finalpage/2026-03-10/2.PDF"),
        ("3", "600000", "2025年半年度报告", "20250828", "finalpage/2025-08-28/3.PDF"),
        ("3", "110059", "2025年半年度报告", "20250828", "finalpage/2025-08-28/3.PDF"),
        ("4", "123456", "2025年年度报告", "20260301", "finalpage/2026-03-01/4.PDF"),
        ("5", "600000", "关于召开股东大会的通知", "20260301", "finalpage/2026-03-01/5.PDF"),
    ]
    return pd.DataFrame(rows, columns=["ann_id", "sec_code", "title", "ann_date", "adjunct_url"])


def build_downloader(
    config: Config, lake: MiniLake, clock: FakeClock, transport: HttpTransport
) -> DocumentDownloader:
    con = lake.catalog.connection
    con.register("ann_frame", build_announcements())
    con.register("basic_frame", pd.DataFrame({"symbol": ["300750", "600000"]}))
    con.execute("CREATE VIEW curated.cninfo_announcements AS SELECT * FROM ann_frame")
    con.execute("CREATE VIEW curated.stock_basic AS SELECT * FROM basic_frame")
    return DocumentDownloader(
        lake.lake_root,
        lake.query,
        config.documents,
        clock,
        transport,
        workers_override=2,
        retries=1,
    )


# TC-RP-001
def test_tc_rp_001_retry_then_fail(clock: FakeClock) -> None:
    calls = {"n": 0}

    def fail() -> bytes:
        calls["n"] += 1
        raise OSError("reset")

    pacer = RequestPacer(clock, "v", min_interval_s=0.0, retries=2, retry_sleep_s=3.0)
    with pytest.raises(DataSourceError, match="v x: failed after 3 attempts"):
        pacer.run("x", fail)
    assert calls["n"] == 3 and clock.sleeps == [3.0, 3.0]


# TC-RP-002
def test_tc_rp_002_spacing(clock: FakeClock) -> None:
    pacer = RequestPacer(clock, "v", min_interval_s=1.0)
    assert [pacer.run("a", lambda: 1), pacer.run("b", lambda: 2)] == [1, 2]
    assert len(clock.sleeps) == 1 and clock.sleeps[0] == pytest.approx(1.0, abs=0.01)


# TC-DCL-001
def test_tc_dcl_001_rule_order(config: Config) -> None:
    titles = pd.Series(
        ["2025年半年度报告", "2025年年度报告", "2025年年度报告摘要", "2025年年度报告(英文版)",
         "2026年第一季度报告", "投资者关系活动记录表", "关于召开股东大会的通知", None]
    )  # fmt: skip
    out = DocumentClassifier(config.documents["cninfo"]).compute_doc_types(titles)
    assert out.tolist() == [
        "semiannual", "annual", None, None, "q1", "ir_record", None, None,
    ]  # fmt: skip


# TC-DCL-002
def test_tc_dcl_002_fixed_type(config: Config) -> None:
    classifier = DocumentClassifier(config.documents["em_industry"])
    assert classifier.compute_doc_types(pd.Series(["a", "b"])).tolist() == ["industry_report"] * 2
    assert classifier.compute_doc_types(pd.Series([], dtype=object)).empty


# TC-DD-001
def test_tc_dd_001_candidates(config: Config, lake: MiniLake, clock: FakeClock) -> None:
    out = build_downloader(config, lake, clock, FakeFileTransport({})).list_candidates("cninfo")
    assert out["doc_id"].tolist() == ["cninfo:1", "cninfo:3"]
    first = out.iloc[0]
    assert first["url"] == "http://static.cninfo.com.cn/finalpage/2026-03-10/1.PDF"
    assert first["local_path"] == "documents/cninfo/annual/2026/03/300750_1.pdf"
    assert out.iloc[1]["doc_type"] == "semiannual" and out.iloc[1]["code"] == "600000"


# TC-DD-002
def test_tc_dd_002_download_then_skip(config: Config, lake: MiniLake, clock: FakeClock) -> None:
    transport = FakeFileTransport({})
    downloader = build_downloader(config, lake, clock, transport)
    report = downloader.run(downloader.list_todo("cninfo"))
    assert (report.keys_total, report.fetched, report.empty) == (2, 2, 0)
    path = lake.lake_root / "documents/cninfo/annual/2026/03/300750_1.pdf"
    assert path.read_bytes() == PDF
    manifest = pd.read_parquet(next((lake.lake_root / "meta/document_manifest").glob("*.parquet")))
    assert set(manifest["status"]) == {"ok"}
    assert manifest["sha256"].iloc[0] == hashlib.sha256(PDF).hexdigest()
    assert downloader.list_todo("cninfo").empty and len(transport.urls) == 2
    lake.catalog.refresh_views()
    assert len(lake.query.sql("SELECT * FROM meta.documents")) == 2


# TC-DD-003
def test_tc_dd_003_not_pdf_and_failure(config: Config, lake: MiniLake, clock: FakeClock) -> None:
    bodies: dict[str, bytes | Exception] = {
        "http://static.cninfo.com.cn/finalpage/2026-03-10/1.PDF": b"<html>",
        "http://static.cninfo.com.cn/finalpage/2025-08-28/3.PDF": OSError("timeout"),
    }
    downloader = build_downloader(config, lake, clock, FakeFileTransport(bodies))
    report = downloader.run(downloader.list_todo("cninfo"))
    assert (report.fetched, report.empty) == (0, 2)
    assert not list((lake.lake_root / "documents").rglob("*.pdf"))
    manifest = pd.concat(
        pd.read_parquet(p) for p in (lake.lake_root / "meta/document_manifest").glob("*.parquet")
    )
    assert sorted(manifest["status"]) == ["failed", "not_pdf"]
    bodies.clear()
    assert downloader.run(downloader.list_todo("cninfo")).fetched == 2


# TC-DD-004
def test_tc_dd_004_unknown_source_and_filters(
    config: Config, lake: MiniLake, clock: FakeClock
) -> None:
    downloader = build_downloader(config, lake, clock, FakeFileTransport({}))
    with pytest.raises(ConfigError, match="unknown document source"):
        downloader.list_candidates("nope")
    assert downloader.list_candidates("cninfo", ["semiannual"])["doc_id"].tolist() == ["cninfo:3"]
    after = downloader.list_candidates("cninfo", start="20260101")
    assert after["doc_id"].tolist() == ["cninfo:1"]
    assert downloader.run(downloader.list_todo("cninfo"), limit=1).fetched == 1


# TC-DD-005
def test_tc_dd_005_source_spacing(config: Config, lake: MiniLake, clock: FakeClock) -> None:
    slow = config.documents["cninfo"].model_copy(update={"min_interval_s": 2.0})
    downloader = build_downloader(config, lake, clock, FakeFileTransport({}))
    DocumentDownloader(
        lake.lake_root,
        lake.query,
        {**config.documents, "cninfo": slow},
        clock,
        FakeFileTransport({}),
        workers_override=1,
        retries=0,
    ).run(downloader.list_todo("cninfo"))
    assert any(s == pytest.approx(2.0, abs=0.01) for s in clock.sleeps)


# TC-RP-003
def test_tc_rp_003_throttle_pause(clock: FakeClock) -> None:
    pacer = RequestPacer(clock, "v", min_interval_s=0.0)
    pacer.run("a", lambda: 1)
    pacer.record_throttle(300.0)
    pacer.run("b", lambda: 2)
    assert any(s == pytest.approx(300.0, abs=0.01) for s in clock.sleeps)


# TC-DD-006
def test_tc_dd_006_throttle_cooldown(config: Config, lake: MiniLake, clock: FakeClock) -> None:
    class ThrottleOnce(FakeFileTransport):
        def fetch_bytes(self, url: str, timeout: float) -> bytes:
            self.urls.append(url)
            if len(self.urls) == 1:
                raise urllib.error.HTTPError(url, 567, "Unknown Status", None, None)  # type: ignore[arg-type]
            return PDF

    source = config.documents["cninfo"].model_copy(update={"cooldown_s": 120.0})
    lister = build_downloader(config, lake, clock, FakeFileTransport({}))
    downloader = DocumentDownloader(
        lake.lake_root,
        lake.query,
        {**config.documents, "cninfo": source},
        clock,
        ThrottleOnce({}),
        workers_override=1,
        retries=2,
    )
    report = downloader.run(lister.list_todo("cninfo"))
    assert report.fetched == 2 and report.empty == 0
    assert any(s == pytest.approx(120.0, abs=0.5) for s in clock.sleeps)
