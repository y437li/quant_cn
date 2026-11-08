"""DeepSeek reads 经营模式 text: variant, pricing mode, cost pass-through, price actions (D-118)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.quote_checker import QuoteChecker

PROMPT = Path(__file__).with_name("prompts") / "business_mode_extraction.txt"
PRICING = ("market", "spread", "negotiated", "bid", "brand", "regulated", "contract")
PASS_THROUGH = ("full", "lagged", "partial", "none")
DIRECTIONS = ("up", "down", "hold")


class ModeClaim(BaseModel):
    """
    Purpose:
        One quoted answer: a value (variant id, pricing mode, pass-through) with its evidence.

    Contract:
        Input:
            value: str | None; reason, quote: str | None; page: int | None -- all may be null when
            the model has no answer
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BusinessModeReply      -- variant, pricing, pass_through
        industry_graph.BusinessModeExtractor  -- checks each claim

    Test cases:
        TC-BME-003  (via BusinessModeExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    value: str | None = None
    reason: str | None = ""
    quote: str | None = None
    page: int | None = None


class PriceAction(BaseModel):
    """
    Purpose:
        A stated price move: direction, what, magnitude, evidence.

    Contract:
        Input:
            direction: str (DIRECTIONS); item: str; magnitude: str | None; quote: str; page: int
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BusinessModeReply  -- price_actions

    Test cases:
        TC-BME-002  (via BusinessModeExtractor) unknown direction dropped
    """

    model_config = ConfigDict(extra="ignore")
    direction: str
    item: str = ""
    magnitude: str | None = None
    quote: str
    page: int


class BusinessModeReply(BaseModel):
    """
    Purpose:
        The LLM reply for one report before validation.

    Contract:
        Input:
            variant, pricing, pass_through: ModeClaim | None; price_actions: list[PriceAction];
            proposed_variant: str | None
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BusinessModeExtractor  -- validates every reply

    Test cases:
        TC-BME-003  (via BusinessModeExtractor) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    variant: ModeClaim | None = None
    proposed_variant: str | None = None
    pricing: ModeClaim | None = None
    pass_through: ModeClaim | None = None
    price_actions: list[PriceAction] = []


@dataclass(frozen=True)
class BusinessModeResult:
    """
    Purpose:
        The quote-checked reading: each claim is a dict {value, reason, evidence} or None.

    Contract:
        Input:
            variant, pricing, pass_through: dict | None; proposed_variant: str | None;
            price_actions: list[dict]; dropped: int; tokens: int; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.BusinessModeExtractor  -- returned by fetch_mode

    Test cases:
        TC-BME-001  (via BusinessModeExtractor) fields from a valid reply
    """

    variant: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None
    pass_through: dict[str, Any] | None = None
    proposed_variant: str | None = None
    price_actions: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class BusinessModeExtractor:
    """
    Purpose:
        Read the business-section pages of one annual report for the business-model fields that
        only the text can give (BUSINESS_MODEL_DESIGN §4.5 T1, §4b.7): which candidate variant of
        the company's archetype fits (or a proposed new one), the pricing mode, the cost
        pass-through and the stated price actions. Kept: claims whose verbatim quote is on a sent
        page and whose value is allowed (variant among the candidates, pricing in PRICING,
        pass-through in PASS_THROUGH, direction in DIRECTIONS); the rest is dropped and counted.

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0      -- page text sent
            system:    str | None   -- prompt; default prompts/business_mode_extraction.txt
        Output:
            instance; `fetch_mode`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/business_modes.py (D-118 run)

    Test cases:
        TC-BME-001  valid reply: variant among candidates, pricing and pass-through kept with
                    evidence, price actions kept
        TC-BME-002  dropped: quote absent, variant not a candidate (moved to proposed only when
                    proposed_variant is set), value outside the allowed sets, bad direction
        TC-BME-003  malformed reply raises DataSourceError; null claims (no answer) are None, not
                    errors
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 15000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_mode(
        self,
        company: str,
        archetype: str,
        variants: Sequence[tuple[str, str, str]],
        pages: Sequence[tuple[int, str]],
    ) -> BusinessModeResult:
        """
        Purpose:
            Ask the model about one report and validate the answer against the text.

        Contract:
            Input:
                company: str; archetype: str -- e.g. "A10 医药产品组合";
                variants: Sequence[tuple[str, str, str]] -- (id, name, description) candidates;
                pages: Sequence[tuple[int, str]] -- business-section pages
            Output:
                BusinessModeResult
            Raises:
                DataSourceError  -- LLM failure or a reply not fitting the shape
        """
        text, used = QuoteChecker.build_prompt_text(pages, self._max_chars)
        cands = "\n".join(f"{i}: {n} — {d}" for i, n, d in variants)
        user = (
            f"公司：{company}\n默认原型：{archetype}\n候选经营模式变体：\n{cands}\n\n"
            f"年报原文（按页）：\n{text}"
        )
        reply = self._llm.fetch_json(self._system, user)
        try:
            parsed = BusinessModeReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        checker = QuoteChecker(used)
        claims, dropped = self._list_kept_claims(parsed, {i for i, _, _ in variants}, checker)
        actions, dropped_actions = self._list_kept_actions(parsed, checker)
        dropped += dropped_actions
        return BusinessModeResult(
            claims["variant"], claims["pricing"], claims["pass_through"], parsed.proposed_variant,
            actions, dropped, reply.prompt_tokens + reply.completion_tokens, reply.cached,
        )  # fmt: skip

    @staticmethod
    def _list_kept_claims(
        parsed: BusinessModeReply, variant_ids: set[str], checker: QuoteChecker
    ) -> tuple[dict[str, dict[str, Any] | None], int]:
        allowed = {
            "variant": variant_ids,
            "pricing": set(PRICING),
            "pass_through": set(PASS_THROUGH),
        }
        claims: dict[str, dict[str, Any] | None] = {}
        dropped = 0
        for key, ok in allowed.items():
            claim: ModeClaim | None = getattr(parsed, key)
            if claim is None or not claim.value:
                claims[key] = None
                continue
            ev = checker.find_evidence(claim.quote, claim.page or 0) if claim.quote else None
            if ev is None or claim.value not in ok:
                dropped += 1
                claims[key] = None
                continue
            claims[key] = {"value": claim.value, "reason": claim.reason or "", "evidence": ev}
        return claims, dropped

    @staticmethod
    def _list_kept_actions(
        parsed: BusinessModeReply, checker: QuoteChecker
    ) -> tuple[list[dict[str, Any]], int]:
        actions, dropped = [], 0
        for a in parsed.price_actions:
            ev = checker.find_evidence(a.quote, a.page)
            if ev is None or a.direction not in DIRECTIONS:
                dropped += 1
                continue
            actions.append(
                {"direction": a.direction, "item": a.item, "magnitude": a.magnitude, "evidence": ev}
            )
        return actions, dropped
