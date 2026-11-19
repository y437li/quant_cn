"""国家统计局 70 个大中城市住宅销售价格指数, city by city, from the monthly releases (plan 31)."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.base_html_list_client import BaseHtmlListClient

logger = logging.getLogger(__name__)
LIST_URL = "https://www.stats.gov.cn/sj/zxfb/"
COLUMNS = ["month", "city", "house_type", "mom", "yoy", "published", "source_url"]
TEXT = ["month", "city", "house_type", "published", "source_url"]
HOUSE_TYPES = {"新建商品住宅销售价格指数": "new", "二手住宅销售价格指数": "second_hand"}
MAX_PAGES = 120  # the list holds every release since 2023 within about 60 pages
_MONTH = re.compile(r"(\d{4})年(\d{1,2})月份?")
_DATE = re.compile(r"/t(\d{8})_")
CITY_CELLS = 3  # city, 环比, 同比 (the 平均 cell is not read)
_NUMBER = re.compile(r"^\d+(\.\d+)?$")


class NbsHousePriceClient(BaseHtmlListClient):
    """
    Purpose:
        The 70-city new-home and second-hand home price indices (plan 31 ph1) from the 国家统计局
        monthly release "YYYY年M月份70个大中城市商品住宅销售价格变动情况". It walks the 最新发布
        list, keeps the releases of months from `start_date`, and reads tables 1 (新建商品住宅)
        and 2 (二手住宅): each row holds two cities as (city, 环比, 同比[, 平均]); January
        releases have no 平均 column, so a city is any name followed by two numbers. Output rows are
        one per (month, city, house_type) with mom / yoy as indices (previous month / same month
        last year = 100), `month` YYYYMM, `published` the release date from the url (YYYYMMDD).
        Tables 3 / 4 (by floor area) are not read. Tier averages are not computed here (plan 31
        ph4, `config/sector_monitors.yaml`).

    Contract:
        Input:
            BaseHtmlListClient dependencies
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "nbs"

    Test cases:
        TC-NHP-001  a release gives 2 house types times the cities of the tables; mom / yoy floats;
                    month from the title, published from the url
        TC-NHP-002  list pages walked until a page has no link; releases before start_date and
                    other releases skipped; duplicate (PC / mobile) tables read once
        TC-NHP-003  a release without tables 1 / 2 raises DataSourceError naming the url
        TC-NHP-004  a January table without the average column gives both cities of a row
    """

    def get_vendor_name(self) -> str:
        """
        Purpose:
            Vendor name for messages.

        Contract:
            Input:
                (none)
            Output:
                str  -- "nbs"
            Raises:
                (none)
        """
        return "nbs"

    def is_wanted(self, title: str) -> bool:
        """
        Purpose:
            The 70-city price release, not its 解读 or other releases.

        Contract:
            Input:
                title: str
            Output:
                bool
            Raises:
                (none)
        """
        return "70个大中城市" in title and "销售价格变动情况" in title and "解读" not in title

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Every city index of the releases from `start_date` on.

        Contract:
            Input:
                api_name: str                -- ignored ("house_price_70")
                params:   Mapping[str, str]  -- start_date YYYYMMDD (default "20230101"),
                                                list_url (default LIST_URL)
                fields:   Sequence[str]      -- ignored; output columns are COLUMNS
            Output:
                DataFrame  -- COLUMNS, sorted by month, house_type, city; zero rows allowed
            Raises:
                DataSourceError  -- network failure after retries, or a release without tables
        """
        start = params.get("start_date", "20230101")[:6]
        rows: list[dict[str, Any]] = []
        for link in self.list_links(params.get("list_url", LIST_URL), MAX_PAGES, start + "01"):
            month = self._get_month(link.title)
            if month is None or month < start:
                continue
            rows += self._read_release(link.url, month)
        out = pd.DataFrame(rows, columns=COLUMNS)
        out[["mom", "yoy"]] = out[["mom", "yoy"]].astype("float64")
        out[TEXT] = out[TEXT].astype("string")
        return out.sort_values(["month", "house_type", "city"]).reset_index(drop=True)

    def _read_release(self, url: str, month: str) -> list[dict[str, Any]]:
        date = _DATE.search(url)
        published = date.group(1) if date else None
        rows: list[dict[str, Any]] = []
        found = set()
        for caption, table in self.read_tables(url):
            kind = next((v for k, v in HOUSE_TYPES.items() if k in caption and "分类" not in
                         caption), None)  # fmt: skip
            if kind is None or kind in found:
                continue
            found.add(kind)
            for cells in table:
                rows += [{"month": month, "city": city, "house_type": kind, "mom": mom,
                          "yoy": yoy, "published": published, "source_url": url}
                         for city, mom, yoy in self._list_cities(cells)]  # fmt: skip
        if found != set(HOUSE_TYPES.values()):
            raise DataSourceError(f"nbs: {url} has no 70-city tables 1 / 2")
        logger.info("nbs %s: %d rows", month, len(rows))
        return rows

    @staticmethod
    def _list_cities(cells: list[str]) -> list[tuple[str, float, float]]:
        """(city, 环比, 同比) of one table row: a name followed by two numbers. A row holds two
        cities, with or without the year-to-date average column (January has none)."""
        out = []
        for i in range(len(cells) - CITY_CELLS + 1):
            name, mom, yoy = cells[i : i + CITY_CELLS]
            if name and not _NUMBER.match(name) and _NUMBER.match(mom) and _NUMBER.match(yoy):
                out.append((name, float(mom), float(yoy)))
        return out

    @staticmethod
    def _get_month(title: str) -> str | None:
        found = _MONTH.search(title)
        return f"{found.group(1)}{int(found.group(2)):02d}" if found else None
