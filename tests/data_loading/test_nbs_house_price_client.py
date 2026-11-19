"""Contract tests for data_loading.NbsHousePriceClient and BaseHtmlListClient (plan 31 ph1)."""

from __future__ import annotations

import urllib.error
from email.message import Message

import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.http_transport import HttpTransport
from quant_cn.data_loading.nbs_house_price_client import COLUMNS, LIST_URL, NbsHousePriceClient
from tests.support import FakeClock

LIST_0 = """
<a href="./202611/t20261116_1.html" title='2026年10月份70个大中城市商品住宅销售价格变动情况'>x</a>
<a href="./202611/t20261116_2.html" title='2026年10月份国民经济运行情况'>x</a>
<a href="./202610/t20261019_3.html" title='2026年9月份70个大中城市商品住宅销售价格变动情况'>x</a>
"""
LIST_1 = """
<a href="./202609/t20260915_4.html" title='2026年8月份70个大中城市商品住宅销售价格变动情况'>x</a>
"""
TABLE = """<p>表{n}\uff1a2026年{m}月70个大中城市{kind}销售价格指数</p>
<table><tr><td>城市</td><td>环比</td><td>同比</td><td>平均</td>
<td>城市</td><td>环比</td><td>同比</td><td>平均</td></tr>
<tr><td>北 京</td><td>{a}</td><td>97.4</td><td>97.7</td>
<td>唐 山</td><td>99.7</td><td>94.7</td><td>94.0</td></tr></table>"""


def build_release(month: int, a: str = "99.9") -> str:
    new = TABLE.format(n=1, m=month, kind="新建商品住宅", a=a)
    used = TABLE.format(n=2, m=month, kind="二手住宅", a=a)
    return new + used + new + used  # PC and mobile copies


class FakeTransport(HttpTransport):
    """Pages by url; a missing url raises HTTP 404. Records every url."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.urls: list[str] = []

    def fetch_bytes(self, url: str, timeout: float) -> bytes:
        self.urls.append(url)
        if url not in self.pages:
            raise urllib.error.HTTPError(url, 404, "not found", Message(), None)
        return self.pages[url].encode("utf-8")


def build_client(pages: dict[str, str]) -> tuple[NbsHousePriceClient, FakeTransport]:
    transport = FakeTransport(pages)
    client = NbsHousePriceClient(FakeClock(), transport, min_interval_s=0, retries=0,
                                 retry_sleep_s=0)  # fmt: skip
    return client, transport


# TC-NHP-001
def test_tc_nhp_001_release_rows() -> None:
    client, _ = build_client({LIST_URL: LIST_0, LIST_URL + "202611/t20261116_1.html":
                              build_release(10, "100.2")})  # fmt: skip
    out = client.query("house_price_70", {"start_date": "20261001"}, [])
    assert list(out.columns) == COLUMNS
    assert len(out) == 4  # 2 cities x 2 house types
    row = out[(out["city"] == "北京") & (out["house_type"] == "second_hand")].iloc[0]
    assert row["month"] == "202610" and row["published"] == "20261116"
    assert row["mom"] == pytest.approx(100.2) and row["yoy"] == pytest.approx(97.4)
    assert out["mom"].dtype == "float64"


# TC-NHP-002
def test_tc_nhp_002_paging_and_filter() -> None:
    pages = {
        LIST_URL: LIST_0, LIST_URL + "index_1.html": LIST_1,
        LIST_URL + "202611/t20261116_1.html": build_release(10),
        LIST_URL + "202610/t20261019_3.html": build_release(9),
        LIST_URL + "202609/t20260915_4.html": build_release(8),
    }  # fmt: skip
    client, transport = build_client(pages)
    out = client.query("house_price_70", {"start_date": "20260901"}, [])
    assert sorted(out["month"].unique()) == ["202609", "202610"]
    assert len(out) == 8  # duplicate tables read once
    assert not any("t20261116_2" in u for u in transport.urls)  # other release skipped
    assert LIST_URL + "index_2.html" in transport.urls  # 404 ends the list
    client, transport = build_client(pages)
    client.query("house_price_70", {"start_date": "20261001"}, [])
    assert LIST_URL + "index_2.html" not in transport.urls  # index_1 all older than start


# TC-NHP-003
def test_tc_nhp_003_no_tables() -> None:
    client, _ = build_client({LIST_URL: LIST_0, LIST_URL + "202611/t20261116_1.html": "<p/>"})
    with pytest.raises(DataSourceError, match="t20261116_1"):
        client.query("house_price_70", {"start_date": "20261001"}, [])


# TC-NHP-004
def test_tc_nhp_004_january_without_average() -> None:
    table = ("<p>表{n}\uff1a2026年1月70个大中城市{kind}销售价格指数</p><table>"
             "<tr><td>北 京</td><td>99.6</td><td>96.0</td><td>唐 山</td><td>99.7</td>"
             "<td>94.7</td></tr></table>")  # fmt: skip
    page = table.format(n=1, kind="新建商品住宅") + table.format(n=2, kind="二手住宅")
    title = "2026年1月份70个大中城市商品住宅销售价格变动情况"
    listing = f"<a href=\"./202602/t20260215_9.html\" title='{title}'>x</a>"
    client, _ = build_client({LIST_URL: listing, LIST_URL + "202602/t20260215_9.html": page})
    out = client.query("house_price_70", {"start_date": "20260101"}, [])
    assert len(out) == 4 and sorted(set(out["city"])) == ["北京", "唐山"]
    assert out[out["city"] == "唐山"]["yoy"].iloc[0] == pytest.approx(94.7)


# TC-BHL-001
def test_tc_bhl_001_links_resolved_and_filtered() -> None:
    client, _ = build_client({LIST_URL: LIST_0})
    links = client.list_links(LIST_URL, 5)
    assert [link.published for link in links] == ["20261116", "20261019"]
    assert links[0].url == LIST_URL + "202611/t20261116_1.html"


# TC-BHL-002
def test_tc_bhl_002_duplicate_tables_dropped() -> None:
    tables = NbsHousePriceClient.build_tables(build_release(10))
    assert len(tables) == 2
    assert tables[0][0].startswith("表1") and tables[1][0].startswith("表2")
