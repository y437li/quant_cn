"""国家新闻出版署 网络游戏审批信息 (版号), game by game, from the monthly lists (plan 31)."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.base_html_list_client import BaseHtmlListClient, PageLink

logger = logging.getLogger(__name__)
BASE_URL = "https://www.nppa.gov.cn/bsfw/jggs/yxspjg/"
CHANNELS = {"gcwlyxspxx": "domestic", "jkwlyxspxx": "imported"}
COLUMNS = [
    "approval_no", "name", "category", "publisher", "operator", "isbn",
    "approved_on", "published", "origin", "list_title", "source_url",
]  # fmt: skip
HEADER = ["序号", "名称", "申报类别", "出版单位", "运营单位", "批复文号", "出版物号", "批准时间"]
MAX_PAGES = 30
_DATE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
_CATEGORY = re.compile(r"var\s+_sblb\s*=\s*['\"]([^'\"]*)['\"]")


class NppaGameClient(BaseHtmlListClient):
    """
    Purpose:
        Game approvals (版号, plan 31 ph1) from the 国家新闻出版署 lists 国产网络游戏审批信息 and
        进口网络游戏审批信息. For each channel it walks the channel list, keeps the lists
        published (url date) on or after `start_date`, and reads the one table whose header
        is HEADER: one row per game with 名称, 出版单位, 运营单位, 批复文号, 出版物号 and 批准时间
        (YYYYMMDD), `published` the list's date from its url (when the approval became
        public). 申报类别 is filled by a page script (`var _sblb = '移动'` once per row, in
        row order) and is read from there. `origin` is domestic / imported by channel.

    Contract:
        Input:
            BaseHtmlListClient dependencies
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "nppa"

    Test cases:
        TC-NGC-001  a list gives one row per game: names, units, approval number, date
                    YYYYMMDD, category from the page script, origin from the channel
        TC-NGC-002  lists published before start_date skipped; an unknown channel or a list
                    without the approval table raises DataSourceError
    """

    def get_vendor_name(self) -> str:
        """
        Purpose:
            Vendor name for messages.

        Contract:
            Input:
                (none)
            Output:
                str  -- "nppa"
            Raises:
                (none)
        """
        return "nppa"

    def is_wanted(self, title: str) -> bool:
        """
        Purpose:
            A game approval list.

        Contract:
            Input:
                title: str
            Output:
                bool
            Raises:
                (none)
        """
        return "审批信息" in title

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Every approval of the lists published from `start_date` on.

        Contract:
            Input:
                api_name: str                -- ignored ("game_license")
                params:   Mapping[str, str]  -- start_date YYYYMMDD (default "20230101"),
                                                channels (comma-separated CHANNELS keys,
                                                default all), base_url (default BASE_URL)
                fields:   Sequence[str]      -- ignored; output columns are COLUMNS
            Output:
                DataFrame  -- COLUMNS, text, sorted by approved_on and approval_no; one row
                              per approval number
            Raises:
                DataSourceError  -- unknown channel, a list without the approval table, or a
                                    network failure after retries
        """
        start = params.get("start_date", "20230101")
        channels = [c for c in params.get("channels", ",".join(CHANNELS)).split(",") if c]
        if any(c not in CHANNELS for c in channels):
            raise DataSourceError(f"nppa: channels must be in {sorted(CHANNELS)}")
        rows: list[dict[str, Any]] = []
        for channel in channels:
            for link in self.list_links(f"{params.get('base_url', BASE_URL)}{channel}/",
                                        MAX_PAGES, start):  # fmt: skip
                rows += self._read_list(link, CHANNELS[channel])
        out = pd.DataFrame(rows, columns=COLUMNS).astype("string")
        out = out.drop_duplicates("approval_no", keep="first")
        return out.sort_values(["approved_on", "approval_no"]).reset_index(drop=True)

    def _read_list(self, link: PageLink, origin: str) -> list[dict[str, Any]]:
        url, title = link.url, link.title
        page = self.fetch_text(url)
        table = next((t for _, t in self.build_tables(page) if t and t[0][:8] == HEADER), None)
        if table is None:
            raise DataSourceError(f"nppa: {url} has no approval table")
        categories = _CATEGORY.findall(page)
        rows = []
        for i, cells in enumerate(table[1:]):
            # the category cell is written by a script, so a row may hold an extra cell:
            # read the units, number and date from the end of the row
            if len(cells) < len(HEADER) or not cells[1]:
                continue
            date = _DATE.search(cells[-1])
            rows.append({
                "approval_no": cells[-3], "name": cells[1],
                "category": categories[i] if i < len(categories) else None,
                "publisher": cells[-5], "operator": cells[-4], "isbn": cells[-2],
                "approved_on": (f"{date.group(1)}{int(date.group(2)):02d}"
                                f"{int(date.group(3)):02d}") if date else None,
                "published": link.published, "origin": origin, "list_title": title,
                "source_url": url,
            })  # fmt: skip
        logger.info("nppa %s: %d games", title, len(rows))
        return rows
