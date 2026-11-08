"""Top-5 customer and supplier tables of an annual report, parsed without the LLM (D-102)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

UNITS = {"元": 1.0, "千元": 1e3, "万元": 1e4, "百万元": 1e6, "亿元": 1e8}
_NUM = r"-?[\d,]+(?:\.\d+)?"
_ANONYMOUS = re.compile(r"^(客户|供应商|第)\s*[一二三四五六七八九十\dA-Za-z]{1,3}\s*名?$")
# where the supplier part begins (searched after the customer totals); "及/和主要供应商情况" is the
# joint heading over both tables and must not match
SUPPLIER_MARK = re.compile(r"前[五5](?:名|大)(?:主要)?(?:供应商|供货商)|(?<![及和])主要供应商情况")
# a line wrap inside a Chinese word ("前五名客 户") leaves a space between two CJK characters
CJK_GAP = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
BSE_CUSTOMER = re.compile(r"主要客户情况")
BSE_GROUPS = 3  # the BSE body pattern also captures the 合计 amount and share
BLOCK_END = re.compile(r"\s3\s*[、.]\s*费用|研发投入")  # the next MD&A item after the block
SUM_TOLERANCE_PCT = 0.05  # rounding of five two-decimal shares
# rank, name (lazy), amount, share with optional %, optional 是/否 related-party flag, next rank
ROW_PATTERN = (
    rf"(?:^|\s)([1-5])\s+(.+?)\s+({_NUM})\s+({_NUM})\s*%?(?:\s+[是否])?(?=\s+[1-5]\s|\s*$)"
)


@dataclass(frozen=True)
class CounterpartyRow:
    """
    Purpose:
        One ranked customer or supplier of a top-5 table.

    Contract:
        Input:
            rank:      int 1..5
            name:      str    -- as printed ("江西铜业股份有限公司", "客户A", "第一名")
            amount:    float  -- CNY (unit converted)
            share_pct: float  -- % of annual sales (customers) or purchases (suppliers)
        Output:
            frozen dataclass; `is_anonymous`
        Raises:
            (none)

    Used by:
        industry_graph.CounterpartyTable        -- rows
        industry_graph.CounterpartyTableParser  -- builds the rows

    Test cases:
        TC-CTP-001  (via CounterpartyTableParser) rows of the SZSE layout
    """

    rank: int
    name: str
    amount: float
    share_pct: float

    @property
    def is_anonymous(self) -> bool:
        """
        Purpose:
            True when the report hides the name ("客户一", "供应商A", "第三名").

        Contract:
            Input:
                (none)
            Output:
                bool
            Raises:
                (none)
        """
        return bool(_ANONYMOUS.match(self.name))


@dataclass(frozen=True)
class CounterpartyTable:
    """
    Purpose:
        The top-5 customers or suppliers of one report: stated totals and the ranked rows
        (empty when only the totals sentence is disclosed, as on the SSE main board).

    Contract:
        Input:
            kind:            "customer" | "supplier"
            total_amount:    float | None  -- CNY
            total_share_pct: float | None
            rows:            list[CounterpartyRow]
        Output:
            frozen dataclass; `is_consistent`
        Raises:
            (none)

    Used by:
        industry_graph.CounterpartyTableParser  -- returned by parse_tables
        industry_graph.ParsedReport             -- customers and suppliers

    Test cases:
        TC-CTP-004  is_consistent: row shares sum to the stated total within 0.05 pp
    """

    kind: str
    total_amount: float | None = None
    total_share_pct: float | None = None
    rows: list[CounterpartyRow] = field(default_factory=list)

    @property
    def is_consistent(self) -> bool:
        """
        Purpose:
            Rows complete and their shares add up to the stated total.

        Contract:
            Input:
                (none)
            Output:
                bool  -- False without rows or without a stated total share
            Raises:
                (none)
        """
        if not self.rows or self.total_share_pct is None:
            return False
        return abs(sum(r.share_pct for r in self.rows) - self.total_share_pct) <= SUM_TOLERANCE_PCT


class CounterpartyTableParser:
    """
    Purpose:
        Parse the "主要销售客户和主要供应商情况" block into a customer and a supplier
        CounterpartyTable. Four layouts are covered (10-report prototype, then all FY2025):
        SZSE (totals as label + value, table in 元 or 千元 with % signs), STAR (totals
        sentence in 万元, table in 万元 without % and with a related-party column), SSE main
        board (totals sentence only, no table), BSE (numbered 主要客户情况 tables whose 合计 row
        holds the totals), plus the A+H sentence wording (百万元, 本集团, 前五大供货商). Amounts
        are converted to CNY. Text is expected without running headers (PdfTextExtractor), so a
        table crossing a page break reads as one block.

    Contract:
        Input:
            (none)
        Output:
            instance; `parse_tables`
        Raises:
            (none)

    Used by:
        industry_graph.AnnualReportParser  -- third step

    Test cases:
        TC-CTP-001  SZSE layout: totals, five rows, unit 千元 converted, names with spaces kept
        TC-CTP-002  STAR layout: 万元 rows without % and with 是/否 column
        TC-CTP-003  SSE main board: totals from the sentence, no rows; heading containing
                    主要供应商情况 does not cut the customer part
        TC-CTP-004  is_consistent and is_anonymous
        TC-CTP-005  text without the block: both tables empty
        TC-CTP-006  BSE layout: (3) 主要客户情况 / (4) 主要供应商情况 tables in 元, totals from
                    the 合计 row
        TC-CTP-007  sentence variants: 百万元 with 本集团 (A+H), 前五大供货商 / 前五名主要客户的
                    销售额为人民币 ... 亿元
        TC-CTP-008  joint heading 主要销售客户及主要供应商情况 and a "前五名供应商中" note
                    before the customer table do not cut the customer part
        TC-CTP-009  前5名 with a digit, a line wrap inside 前五名客 户, 占境内年度销售总额 and
                    占年度主营业务销售收入总额 wording
        TC-CTP-010  BSE: a 研发投入 mention before the table does not cut it; shares without %
    """

    def parse_tables(self, text: str) -> tuple[CounterpartyTable, CounterpartyTable]:
        """
        Purpose:
            Customer and supplier tables from the block text. The supplier part starts at the
            first supplier marker after the customer totals (or the customer heading), so a
            "主要销售客户及主要供应商情况" heading or a "前五名供应商中..." note before the
            customer table never cuts the customer part.

        Contract:
            Input:
                text: str  -- the counterparty section (may run into the next section)
            Output:
                tuple[CounterpartyTable, CounterpartyTable]  -- (customers, suppliers)
            Raises:
                (none)
        """
        flat = CJK_GAP.sub("", re.sub(r"\s+", " ", text))
        anchor = self._find_customer_anchor(flat)
        end = BLOCK_END.search(flat, anchor)  # BSE business text before the table cites 研发投入
        flat = flat[: end.start()] if end else flat
        split = SUPPLIER_MARK.search(flat, anchor)
        if split is None:
            return self._parse_one(flat, "customer"), CounterpartyTable("supplier")
        cut = split.start()
        return self._parse_one(flat[:cut], "customer"), self._parse_one(flat[cut:], "supplier")

    def _find_customer_anchor(self, flat: str) -> int:
        for regex in (
            self._build_label("客户", "销售"),
            self._build_sentence("客户", "销售"),
            BSE_CUSTOMER,
        ):
            found = regex.search(flat)
            if found:
                return found.end()
        return 0

    def _parse_one(self, text: str, kind: str) -> CounterpartyTable:
        who, verb = ("客户", "销售") if kind == "customer" else ("供应商", "采购")
        total, share, unit = self._find_totals(text, who, verb)
        table_unit = re.search(rf"{verb}额（(千元|万元|元)）", text) or re.search(
            r"单位：(百万元|千元|万元|元)", text
        )
        scale = UNITS[table_unit[1] if table_unit else unit]
        rows: list[CounterpartyRow] = []
        body = re.search(rf"{who}名称(.*?)合计", text) or re.search(
            rf"{verb}占比\s*%?.*?联\s*关\s*系(.*?)合计\s*({_NUM})\s*({_NUM})\s*%?", text
        )
        if body:
            for m in re.finditer(ROW_PATTERN, body[1]):
                rows.append(
                    CounterpartyRow(
                        int(m[1]), m[2].strip(), self._to_float(m[3]) * scale, self._to_float(m[4])
                    )
                )
            if total is None and body.lastindex == BSE_GROUPS:  # BSE: totals only in the 合计 row
                total, share = self._to_float(body[2]) * scale, self._to_float(body[3])
        return CounterpartyTable(kind, total, share, rows)

    @staticmethod
    def _build_label(who: str, verb: str) -> re.Pattern[str]:
        return re.compile(
            rf"前[五5]名{who}合计{verb}金额（(千元|万元|元)）\s*({_NUM})\s*"
            rf"前[五5]名{who}合计{verb}金额占年度{verb}总额比例\s*({_NUM})\s*%"
        )

    @staticmethod
    def _build_sentence(who: str, verb: str) -> re.Pattern[str]:
        names = "(?:供应商|供货商)" if who == "供应商" else who
        return re.compile(
            rf"前[五5](?:名|大)(?:主要)?{names}(?:合计)?的?{verb}(?:金)?额(?:合计)?(?:为|是)?(?:人民币)?"
            rf"\s*({_NUM})\s*(百万元|千元|万元|亿元|元)\s*[，,;；]?\s*"
            rf"占(?:本公司|本集团|公司)?(?:境内)?(?:年度)?(?:主营业务)?{verb}(?:收入)?总额(?:的|比例)?(?:为)?(?:近)?\s*({_NUM})\s*%"
        )

    def _find_totals(
        self, text: str, who: str, verb: str
    ) -> tuple[float | None, float | None, str]:
        label = self._build_label(who, verb).search(text)
        if label:
            return self._to_float(label[2]) * UNITS[label[1]], self._to_float(label[3]), label[1]
        sentence = self._build_sentence(who, verb).search(text)
        if sentence:
            amount = self._to_float(sentence[1]) * UNITS[sentence[2]]
            return amount, self._to_float(sentence[3]), sentence[2]
        return None, None, "元"

    @staticmethod
    def _to_float(value: str) -> float:
        return float(value.replace(",", ""))
