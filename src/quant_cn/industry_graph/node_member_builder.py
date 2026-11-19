"""Which taxonomy nodes a company sells into, by period and revenue weight (plan 28 ph3b / ph4)."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping
from typing import Any

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.industry_graph.product_matcher import ProductMatcher
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy

MEMBER_COLUMNS = [
    "ts_code",
    "period",
    "known_on",
    "item",
    "node_id",
    "segment",
    "sector",
    "sales",
    "weight",
    "how",
    "taxonomy_version",
]
SKIP = re.compile(r"^(产品|合计|其他业务|主营业务|小计|主营业务收入|营业收入)$")
ADJUST = re.compile(r"抵消|抵减|调整|^合计")
SUBLINE = re.compile(r"[：:]")
# a parent line that only wraps its sub-lines (持续经营业务): keep the sub-lines
WRAPPER = re.compile(r"^(持续经营业务|主营业务|分产品|产品|商品|业务|营业收入|主营业务收入)$")
TOTAL_GAP = 0.01  # a line within 1% of the sum of the other lines is their total
RELEASE_LAG_DAYS = 120  # 主营构成 has no date; annual reports are due by 30 April


class NodeMemberBuilder:
    """
    Purpose:
        Build `node_member` (plan 28 ph3b-1, D-161): for each company and period, the taxonomy
        product nodes its revenue lines (主营构成 by product, fina_mainbz type P) map to through
        ProductMatcher, with the node's segment and sector, the line's sales and its weight in
        the company's revenue. The lines kept are the ones the chain view prototype kept:
        totals (SKIP words, ADJUST words, a line within TOTAL_GAP of the sum of the other lines)
        and sub-lines of a reported parent line (利息净收入 + colon + 利息支出) are dropped,
        except when the parent only wraps them (WRAPPER: 持续经营业务, 主营业务 …): then the
        parent is dropped and the sub-lines kept;
        weight = sales / sum of the kept lines' sales; a compound line matched to several
        nodes splits its weight equally; a line ProductMatcher maps only to the company's sector
        segment (how "sector", D-115) has that segment as node and segment; a node without a
        segment (a shared material such as 生猪) takes the company's sector segment. Unmatched and
        generic lines are kept with node_id None (how "none" / "generic") so unmapped revenue
        can be measured. known_on is the
        announcement date given for (ts_code, period) (the annual report's), else period end
        + RELEASE_LAG_DAYS; taxonomy_version is the version of the taxonomy used.

    Contract:
        Input:
            matcher: ProductMatcher; taxonomy: ProductTaxonomy; date_codec: DateCodec
        Output:
            instance; `build_members(revenue, sw_codes, known_on=None) -> DataFrame`
            (MEMBER_COLUMNS)
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `build-graph` writes node_member

    Test cases:
        TC-NMB-001  matched lines get node, segment, sector and weight over the kept lines;
                    total lines, adjustments and sub-lines of a parent line are dropped
        TC-NMB-002  a compound line splits its weight over its nodes; a sector-fallback line
                    gets its segment; unmatched and generic lines are kept with node_id None
                    and their how
        TC-NMB-003  known_on comes from the given dates, else period end + 120 days; empty
                    revenue gives an empty frame with MEMBER_COLUMNS
        TC-NMB-004  a wrapper parent (持续经营业务) is replaced by its sub-lines
        TC-NMB-005  a material match without a segment takes the company's sector segment
    """

    def __init__(
        self, matcher: ProductMatcher, taxonomy: ProductTaxonomy, date_codec: DateCodec
    ) -> None:
        self._matcher = matcher
        self._taxonomy = taxonomy
        self._dates = date_codec

    def build_members(
        self,
        revenue: pd.DataFrame,
        sw_codes: Mapping[str, list[str]],
        known_on: Mapping[tuple[str, str], str] | None = None,
    ) -> pd.DataFrame:
        """
        Purpose:
            The node members of every company and period in a revenue table.

        Contract:
            Input:
                revenue:  DataFrame  -- ts_code, end_date, bz_item, bz_sales (fina_mainbz P)
                sw_codes: Mapping[str, list[str]]  -- ts_code -> Shenwan L2 / L3 codes
                known_on: Mapping[(ts_code, period), YYYYMMDD] | None
            Output:
                DataFrame  -- MEMBER_COLUMNS, sorted by ts_code, period, -weight, item
            Raises:
                (none)
        """
        dates = {k: v for k, v in (known_on or {}).items() if isinstance(v, str) and v}
        rows: list[dict[str, Any]] = []
        sales = revenue[revenue["bz_sales"].notna()]
        for (ts, period), group in sales.groupby(["ts_code", "end_date"], sort=True):
            kept = self._list_kept_lines(group)
            total = sum(s for _, s in kept) or 1.0
            day = dates.get((str(ts), str(period))) or self._build_release_date(str(period))
            for item, value in kept:
                rows += self._build_rows(str(ts), str(period), day, item, value, total, sw_codes)
        frame = pd.DataFrame(rows, columns=MEMBER_COLUMNS)
        order = frame.assign(_w=-frame["weight"])
        order = order.sort_values(["ts_code", "period", "_w", "item"], kind="stable")
        return order.drop(columns="_w").reset_index(drop=True)

    def _list_kept_lines(self, group: pd.DataFrame) -> list[tuple[str, float]]:
        lines = [
            (str(i), float(s)) for i, s in zip(group["bz_item"], group["bz_sales"], strict=True)
        ]
        whole = sum(s for _, s in lines if s > 0)
        names = {i for i, _ in lines}
        parents = {SUBLINE.split(i)[0] for i in names if SUBLINE.search(i)}
        wrappers = {p for p in parents if p in names and WRAPPER.match(p)}
        kept, seen = [], set()
        for item, value in lines:
            if item in seen or item in wrappers or value <= 0:
                continue
            if SKIP.match(item) or ADJUST.search(item):
                continue
            others = whole - value
            if others > 0 and abs(value - others) <= TOTAL_GAP * value:
                continue
            parent = SUBLINE.split(item)[0] if SUBLINE.search(item) else None
            if parent is not None and parent in names and parent not in wrappers:
                continue
            seen.add(item)
            kept.append((item, value))
        return kept

    def _build_rows(
        self,
        ts: str,
        period: str,
        day: str,
        item: str,
        value: float,
        total: float,
        sw_codes: Mapping[str, list[str]],
    ) -> list[dict[str, Any]]:
        weight = value / total
        found = self._matcher.find_matches(item, list(sw_codes.get(ts, [])))
        base = {"ts_code": ts, "period": period, "known_on": day, "item": item,
                "taxonomy_version": self._taxonomy.version}  # fmt: skip
        if not found:
            how = "generic" if self._matcher.is_generic(item) else "none"
            return [{**base, "node_id": None, "segment": None, "sector": None,
                     "sales": value, "weight": weight, "how": how}]  # fmt: skip
        out = []
        for match in found:
            node = self._taxonomy.get_node(match.node_id)
            segment = self._find_segment(match.node_id)
            if segment is None:  # a shared material (生猪, 焦炭): the company's own segment
                segment = self._matcher.find_sector_segment(list(sw_codes.get(ts, [])))
            out.append({**base, "node_id": match.node_id,
                        "segment": segment,
                        "sector": node.sector if node else None,
                        "sales": value / len(found), "weight": weight / len(found),
                        "how": match.how})  # fmt: skip
        return out

    def _find_segment(self, node_id: str) -> str | None:
        node = self._taxonomy.get_node(node_id)
        if node is None:
            return None
        return node.id if node.type == "segment" else node.segment

    def _build_release_date(self, period: str) -> str:
        day = self._dates.to_date(period) + dt.timedelta(days=RELEASE_LAG_DAYS)
        return self._dates.to_str(day)
