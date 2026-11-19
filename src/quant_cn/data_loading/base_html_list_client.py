"""Shared paging and table reading for government sites that publish monthly HTML tables."""

from __future__ import annotations

import functools
import html
import re
import urllib.error
from dataclasses import dataclass
from urllib.parse import urljoin

from quant_cn.core.clock import Clock
from quant_cn.data_loading.base_web_client import BaseWebClient
from quant_cn.data_loading.http_transport import HttpTransport

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
_TABLE = re.compile(r"(<table.*?</table>)", re.S | re.I)
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_LINK = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.S | re.I)
_HREF = re.compile(r"href=[\"']([^\"']+)[\"']", re.I)
NOT_FOUND = 404  # a list page past the last one
_TITLE = re.compile(r"title=[\"']([^\"']+)[\"']", re.I)


@dataclass(frozen=True)
class PageLink:
    """
    Purpose:
        One release linked from a list page: absolute url, its title text, and the
        publication date taken from the url (".../t20261116_123.html" -> "20261116").

    Contract:
        Input:
            url: str; title: str; published: str (YYYYMMDD)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        data_loading.BaseHtmlListClient  -- `list_links` output
        data_loading.NppaGameClient  -- reads lists, `published` per row

    Test cases:
        TC-BHL-001  (via NbsHousePriceClient) links resolved against the list url
    """

    url: str
    title: str
    published: str


class BaseHtmlListClient(BaseWebClient):
    """
    Purpose:
        Base for clients of sites that list monthly releases on paged HTML index pages
        (`<list_url>`, `<list_url>index_1.html`, ...) and publish each release as HTML tables
        (国家统计局 70 城房价, 国家新闻出版署 游戏审批, plan 31 ph1). It pages the index until a
        page gives no link or `max_pages` is reached, keeps the links whose title passes
        `is_wanted`, and reads a release into (caption, rows) pairs: the caption is the last
        "表N..." text before the table (or ""), rows are the stripped cell texts; tables that
        repeat an earlier one with the same caption (PC and mobile copies) are dropped.

    Contract:
        Input:
            BaseWebClient dependencies (clock, transport, min_interval_s, retries, ...)
        Output:
            instance; `list_links(list_url, max_pages)`, `read_tables(url)`, `fetch_text(url)`;
            subclasses implement `query`, `get_vendor_name` and `is_wanted`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        data_loading.NbsHousePriceClient  -- subclass
        data_loading.NppaGameClient       -- subclass

    Test cases:
        TC-BHL-001  (via NbsHousePriceClient) list pages walked until empty; titles filtered
        TC-BHL-002  (via NbsHousePriceClient) duplicate tables dropped; captions kept
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

    def is_wanted(self, title: str) -> bool:
        """
        Purpose:
            Whether a list-page link with this title is a release the client reads.

        Contract:
            Input:
                title: str
            Output:
                bool  -- default True; subclasses narrow it
            Raises:
                (none)
        """
        return bool(title)

    def fetch_text(self, url: str) -> str:
        """
        Purpose:
            GET one page as text (UTF-8, undecodable bytes replaced), paced and retried.

        Contract:
            Input:
                url: str
            Output:
                str
            Raises:
                DataSourceError  -- failure after retries
        """
        body = self._pacer.run(url, functools.partial(self._transport.fetch_bytes, url,
                                                      self._timeout_s))  # fmt: skip
        return body.decode("utf-8", errors="replace")

    def list_links(self, list_url: str, max_pages: int, since: str = "") -> list[PageLink]:
        """
        Purpose:
            Wanted release links of the list pages, newest page first, without duplicates.
            Paging stops at a page with no link, a page that answers HTTP 404, `max_pages`, or
            after the first page whose links are all published before `since`.

        Contract:
            Input:
                list_url: str  -- index url ending in "/"; max_pages: int >= 1;
                since: str  -- YYYYMMDD, "" for no limit
            Output:
                list[PageLink]
            Raises:
                DataSourceError  -- failure after retries
        """
        out: list[PageLink] = []
        seen: set[str] = set()
        for page in range(max_pages):
            url = list_url if page == 0 else f"{list_url}index_{page}.html"
            links = self._find_links(self._fetch_list_page(url), list_url)
            if not links:
                break
            for link in links:
                if link.url not in seen and self.is_wanted(link.title) and link.published >= since:
                    seen.add(link.url)
                    out.append(link)
            if since and all(link.published < since for link in links):
                break
        return out

    def _fetch_list_page(self, url: str) -> str:
        """A list page; "" when the site answers 404 (past the last page)."""
        try:
            return self._transport.fetch_bytes(url, self._timeout_s).decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code == NOT_FOUND:
                return ""
        except OSError:
            pass  # paced retries below
        return self.fetch_text(url)

    def read_tables(self, url: str) -> list[tuple[str, list[list[str]]]]:
        """
        Purpose:
            The tables of one release as (caption, rows), duplicates dropped.

        Contract:
            Input:
                url: str
            Output:
                list[tuple[str, list[list[str]]]]
            Raises:
                DataSourceError  -- failure after retries
        """
        return self.build_tables(self.fetch_text(url))

    @classmethod
    def build_tables(cls, page: str) -> list[tuple[str, list[list[str]]]]:
        """
        Purpose:
            Parse page text into (caption, rows) pairs (see the class Purpose).

        Contract:
            Input:
                page: str  -- HTML
            Output:
                list[tuple[str, list[list[str]]]]
            Raises:
                (none)
        """
        out: list[tuple[str, list[list[str]]]] = []
        seen: set[str] = set()
        caption = ""
        for part in _TABLE.split(page):
            if not part.lower().startswith("<table"):
                found = re.findall(r"表\s*\d+[^表]{0,80}", cls.get_text(part))
                caption = found[-1] if found else caption
                continue
            rows = [[cls.get_text(c) for c in _CELL.findall(r)] for r in _ROW.findall(part)]
            key = caption + repr(rows)
            if rows and key not in seen:
                seen.add(key)
                out.append((caption, rows))
        return out

    @staticmethod
    def get_text(fragment: str) -> str:
        """
        Purpose:
            Visible text of an HTML fragment with every whitespace removed (Chinese tables
            pad names such as 北 京 with spaces).

        Contract:
            Input:
                fragment: str
            Output:
                str
            Raises:
                (none)
        """
        return _SPACE.sub("", html.unescape(_TAG.sub("", fragment))).replace("　", "")

    @classmethod
    def _find_links(cls, page: str, base: str) -> list[PageLink]:
        out = []
        for attrs, inner in _LINK.findall(page):
            href = _HREF.search(attrs)
            if not href or not re.search(r"/t\d{8}_\d+\.html?$", href.group(1)):
                continue
            title = _TITLE.search(attrs)
            text = html.unescape(title.group(1)) if title else cls.get_text(inner)
            date = re.search(r"/t(\d{8})_", href.group(1))
            out.append(PageLink(urljoin(base, href.group(1)), _SPACE.sub("", text),
                                date.group(1) if date else ""))  # fmt: skip
        return out
