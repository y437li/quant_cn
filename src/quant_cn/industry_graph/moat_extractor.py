"""DeepSeek reads 核心竞争力分析: the moat a company claims, by type, with quotes (§4.4)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quote_checker import QuoteChecker

PROMPT = Path(__file__).with_name("prompts") / "moat_extraction.txt"
MOAT_TYPES = ("cost", "switching", "intangible", "network", "efficient_scale")


class MoatClaim(BaseModel):
    """
    Purpose:
        One claimed advantage: its moat type, a short statement, the figure the company gives (if
        any) and the evidence.

    Contract:
        Input:
            type: str (MOAT_TYPES); claim: str; figure: str | None; quote: str | None;
            page: int | None
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.MoatReply  -- claims

    Test cases:
        TC-ME-002  (via MoatExtractor) unknown type or absent quote dropped
    """

    model_config = ConfigDict(extra="ignore")
    type: str
    claim: str = ""
    figure: str | None = None
    quote: str | None = None
    page: int | None = None


class MoatReply(BaseModel):
    """
    Purpose:
        The LLM reply before validation.

    Contract:
        Input:
            claims: list[MoatClaim]; summary: str | None
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.MoatExtractor  -- validates every reply

    Test cases:
        TC-ME-003  (via MoatExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    claims: list[MoatClaim] = []
    summary: str | None = None


@dataclass(frozen=True)
class MoatResult:
    """
    Purpose:
        The quote-checked claims of one report.

    Contract:
        Input:
            claims: list[dict] -- type, claim, figure, evidence; summary: str; dropped: int;
            tokens: int; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.MoatExtractor  -- returned by fetch_claims

    Test cases:
        TC-ME-001  (via MoatExtractor) fields from a valid reply
    """

    claims: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class MoatExtractor:
    """
    Purpose:
        Read the 核心竞争力分析 pages of one annual report and list the advantages the company
        claims, each classified as one of MOAT_TYPES (cost, switching costs, intangibles, network
        effects, efficient scale) with the figure it cites. These are claims, not proof: the rule
        layer tests them against ROIC, margins and share (§4.4). Kept: claims with an allowed type
        and a verbatim quote on a sent page.

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0      -- page text sent
            system:    str | None   -- prompt; default prompts/moat_extraction.txt
        Output:
            instance; `fetch_claims`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/moat_claims.py (§4.4 run)

    Test cases:
        TC-ME-001  valid reply: claims kept with type, figure and evidence; summary kept
        TC-ME-002  dropped: type outside MOAT_TYPES, quote absent or not on a sent page
        TC-ME-003  malformed reply raises DataSourceError
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 12000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_claims(self, company: str, pages: Sequence[tuple[int, str]]) -> MoatResult:
        """
        Purpose:
            Ask the model about one report and validate the answer against the text.

        Contract:
            Input:
                company: str; pages: Sequence[tuple[int, str]] -- 核心竞争力 pages
            Output:
                MoatResult
            Raises:
                DataSourceError  -- LLM failure or a reply not fitting the shape
        """
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        reply = self._llm.fetch_json(self._system, f"公司：{company}\n\n年报原文（按页）：\n{text}")
        try:
            parsed = MoatReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        checker = QuoteChecker(used)
        claims, dropped = [], 0
        for c in parsed.claims:
            ev = checker.find_evidence(c.quote, c.page or 0) if c.quote else None
            if ev is None or c.type not in MOAT_TYPES:
                dropped += 1
                continue
            claims.append({"type": c.type, "claim": c.claim, "figure": c.figure, "evidence": ev})
        tokens = reply.prompt_tokens + reply.completion_tokens
        return MoatResult(claims, parsed.summary or "", dropped, tokens, reply.cached)
