"""DeepSeek reads contract, bid-win and operating-data announcements into rows (plan 18)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.lenient_item import LenientItem
from quant_cn.industry_graph.quote_checker import QuoteChecker

PROMPT = Path(__file__).with_name("prompts") / "contract_extraction.txt"
KINDS = ("contract", "period_total")
STATUSES = ("预中标", "中标", "签约", "进展", "终止")
# multiplier words in a money unit, longest first ("千万" before "万")
UNIT_SCALES = (("亿", 1e8), ("千万", 1e7), ("百万", 1e6), ("万", 1e4), ("千", 1e3))


class ContractItem(LenientItem):
    """
    Purpose:
        One contract, bid win or period order total the LLM found, before the checks.

    Contract:
        Input:
            kind: str; counterparty / project: str | None; amount / amount_high: float | None
            (a range is amount..amount_high);
            unit: str | None; currency: str | None; share_of_revenue: float | None (percent);
            term: str | None; status: str; segment: str | None; period: str | None;
            is_framework / is_related_party: bool; quote: str; page: int
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.ContractReply  -- items

    Test cases:
        TC-CEX-002  (via ContractExtractor) malformed reply raises DataSourceError
    """

    kind: str
    counterparty: str | None = None
    project: str | None = None
    amount: float | None = None
    amount_high: float | None = None
    unit: str | None = None
    currency: str | None = "CNY"
    share_of_revenue: float | None = None
    term: str | None = None
    status: str
    segment: str | None = None
    period: str | None = None
    is_framework: bool = False
    is_related_party: bool = False
    quote: str
    page: int


class ContractReply(BaseModel):
    """
    Purpose:
        The LLM reply for one announcement.

    Contract:
        Input:
            items: list[ContractItem]
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.ContractExtractor  -- validates every reply

    Test cases:
        TC-CEX-002  (via ContractExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    items: list[ContractItem] = []


@dataclass(frozen=True)
class ContractResult:
    """
    Purpose:
        The checked contract rows of one announcement.

    Contract:
        Input:
            items: list[dict] -- ContractItem fields plus amount_value / amount_high_value (amount
            times the unit's multiplier, in `currency`; None without one) and evidence in
            place of quote / page; dropped: int >= 0; tokens: int >= 0; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.ContractExtractor  -- returned by fetch_contracts

    Test cases:
        TC-CEX-001  (via ContractExtractor) kept and dropped items, amount_value
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class ContractExtractor:
    """
    Purpose:
        Turn a 重大合同 / 中标 / 经营数据 announcement into quote-checked contract rows (plan 18
        ph3): single contracts or bids (kind contract, with status 预中标 / 中标 / 签约 / 进展 /
        终止) and period order totals from operating-data announcements (kind period_total).
        The whole announcement is sent (they are short; max_chars caps long ones). A row is
        kept when its quote is on a sent page and its kind and status are known; the amount is
        scaled to currency units by the multiplier word in its unit (UNIT_SCALES), so 5,381.70
        万元 is 53,817,000. Framework agreements are kept with is_framework so the backlog can
        leave them out.

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0     -- text sent per announcement
            system:    str | None  -- prompt; default prompts/contract_extraction.txt
        Output:
            instance; `fetch_contracts`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/guidance_pilot.py (plan 18 phase 3 pilot)

    Test cases:
        TC-CEX-001  valid reply: rows kept with evidence and amount_value (万元, 亿元, 万美元,
                   no unit); absent quote, unknown kind and unknown status dropped
        TC-CEX-002  malformed reply raises DataSourceError
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 8000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_contracts(
        self, company: str, ann_date: str, pages: Sequence[tuple[int, str]]
    ) -> ContractResult:
        """
        Purpose:
            Ask the model about one announcement and check every row against the text.

        Contract:
            Input:
                company: str; ann_date: str YYYYMMDD; pages: Sequence[tuple[int, str]]
            Output:
                ContractResult
            Raises:
                DataSourceError  -- LLM failure or a reply that does not fit the JSON shape
        """
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        user = f"公司：{company}\n公告日期：{ann_date}\n\n原文（按页）：\n{text}"
        reply = self._llm.fetch_json(self._system, user)
        try:
            parsed = ContractReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        checker = QuoteChecker(used)
        items, dropped = [], 0
        for item in parsed.items:
            ev = checker.find_evidence(item.quote, item.page)
            if ev is None or item.kind not in KINDS or item.status not in STATUSES:
                dropped += 1
                continue
            row = item.model_dump(exclude={"quote", "page"})
            row["amount_value"] = self._compute_amount_value(item.amount, item.unit)
            row["amount_high_value"] = self._compute_amount_value(item.amount_high, item.unit)
            row["evidence"] = ev
            items.append(row)
        tokens = reply.prompt_tokens + reply.completion_tokens
        return ContractResult(items, dropped, tokens, reply.cached)

    @staticmethod
    def _compute_amount_value(amount: float | None, unit: str | None) -> float | None:
        if amount is None:
            return None
        scale = next((s for word, s in UNIT_SCALES if word in (unit or "")), 1.0)
        return amount * scale
