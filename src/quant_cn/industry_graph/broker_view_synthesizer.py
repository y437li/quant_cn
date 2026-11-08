"""DeepSeek turns many broker reports on one product, industry or company into one view."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError

PROMPT = Path(__file__).with_name("prompts") / "broker_view_synthesis.txt"
LIST_FIELDS = ("multiple_reasons", "drivers", "bull", "risks", "divergence", "recent_change")
SCOPES = ("product", "industry", "company")


@dataclass(frozen=True)
class ReportDigest:
    """
    Purpose:
        One broker report reduced to what the synthesis needs: the quote-checked fields of a
        ValuationExtractor result (plan 13), tagged with a short id the model must cite.

    Contract:
        Input:
            ref: str -- short id, e.g. "R3"; org, date, title, rating: str; target_price:
            str; methods, logic, assumptions, forecasts: str (already formatted; forecasts
            carry net profit per year so a loss year behind a later base year is visible)
        Output:
            frozen dataclass; `format_text`
        Raises:
            (none)

    Used by:
        industry_graph.BrokerViewSynthesizer  -- input

    Test cases:
        TC-BVS-001  (via BrokerViewSynthesizer) digests appear in the prompt with their refs
    """

    ref: str
    org: str
    date: str
    title: str
    rating: str = ""
    target_price: str = ""
    methods: str = ""
    logic: str = ""
    assumptions: str = ""
    forecasts: str = ""

    def format_text(self) -> str:
        """
        Purpose:
            The digest as one prompt block.

        Contract:
            Input:
                (none)
            Output:
                str
            Raises:
                (none)
        """
        return (
            f"[{self.ref}] {self.org} {self.date}《{self.title}》 评级：{self.rating or '—'}"
            f" 目标价：{self.target_price or '—'}\n估值方法：{self.methods or '—'}\n"
            f"盈利预测：{self.forecasts or '—'}\n逻辑：{self.logic or '—'}\n"
            f"假设：{self.assumptions or '—'}"
        )


class ViewPoint(BaseModel):
    """
    Purpose:
        One synthesized point with the report refs it rests on.

    Contract:
        Input:
            point: str; sources: list[str]; metric, unit: str | None (drivers only)
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BrokerViewReply  -- list fields

    Test cases:
        TC-BVS-002  (via BrokerViewSynthesizer) points citing unknown refs are dropped
    """

    model_config = ConfigDict(extra="ignore")
    point: str
    sources: list[str] = []
    metric: str | None = None
    unit: str | None = None


class BrokerViewReply(BaseModel):
    """
    Purpose:
        The LLM reply before the citation check.

    Contract:
        Input:
            summary, method_consensus: str; multiple_range: dict | None; list fields of
            ViewPoint (LIST_FIELDS)
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BrokerViewSynthesizer  -- validates every reply

    Test cases:
        TC-BVS-003  (via BrokerViewSynthesizer) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    summary: str = ""
    method_consensus: str = ""
    multiple_range: dict[str, Any] | None = None
    multiple_reasons: list[ViewPoint] = []
    drivers: list[ViewPoint] = []
    bull: list[ViewPoint] = []
    risks: list[ViewPoint] = []
    divergence: list[ViewPoint] = []
    recent_change: list[ViewPoint] = []


@dataclass(frozen=True)
class BrokerView:
    """
    Purpose:
        The synthesized view after the citation check.

    Contract:
        Input:
            scope: str; name: str; n_reports: int; summary, method_consensus: str;
            multiple_range: dict | None; points: dict[str, list[dict]] -- per LIST_FIELDS key,
            each {point, sources, metric?, unit?}; dropped: int; tokens: int; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.BrokerViewSynthesizer  -- returned by fetch_view

    Test cases:
        TC-BVS-001  (via BrokerViewSynthesizer) fields from a valid reply
    """

    scope: str
    name: str
    n_reports: int
    summary: str = ""
    method_consensus: str = ""
    multiple_range: dict[str, Any] | None = None
    points: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class BrokerViewSynthesizer:
    """
    Purpose:
        Synthesize the broker view of one product, Shenwan L3 industry or company from many
        report digests (user, 2026-11-08: the broker part must be the pattern across reports,
        not a list). The model may use only the digests; every point must cite digest refs, and
        refs not among the digests are removed; a point left without a valid ref is dropped
        (the citation check plays the role QuoteChecker plays for single documents). Digests
        are sent newest first within a character budget.

    Contract:
        Input:
            llm:       BaseLlmClient
            max_chars: int > 0      -- digest text sent
            system:    str | None   -- prompt; default prompts/broker_view_synthesis.txt
        Output:
            instance; `fetch_view`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/broker_views.py (plan 13 phase 4)

    Test cases:
        TC-BVS-001  valid reply: summary, method consensus, range and cited points kept;
                    digests in the prompt with refs
        TC-BVS-002  unknown refs removed; a point with no valid ref dropped and counted;
                    digests over the budget not sent and not citable
        TC-BVS-003  malformed reply or unknown scope raises DataSourceError
    """

    def __init__(
        self, llm: BaseLlmClient, max_chars: int = 14000, system: str | None = None
    ) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_view(self, scope: str, name: str, digests: Sequence[ReportDigest]) -> BrokerView:
        """
        Purpose:
            Ask the model for the synthesized view and check its citations.

        Contract:
            Input:
                scope: str -- one of SCOPES; name: str; digests: Sequence[ReportDigest],
                newest first
            Output:
                BrokerView
            Raises:
                DataSourceError  -- unknown scope, LLM failure, reply not fitting the shape
        """
        if scope not in SCOPES:
            raise DataSourceError(f"unknown scope {scope!r}")
        blocks: list[tuple[str, str]] = []
        size = 0
        for digest in digests:
            text = digest.format_text()
            if blocks and size + len(text) > self._max_chars:
                break
            blocks.append((digest.ref, text))
            size += len(text)
        known = {ref for ref, _ in blocks}
        user = f"范围：{scope}\n名称：{name}\n研报数：{len(blocks)}\n\n" + "\n\n".join(
            t for _, t in blocks
        )
        reply = self._llm.fetch_json(self._system, user)
        try:
            parsed = BrokerViewReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{name}: reply does not fit the shape: {exc}") from exc
        points: dict[str, list[dict[str, Any]]] = {}
        dropped = 0
        for key in LIST_FIELDS:
            kept = []
            for item in getattr(parsed, key):
                refs = [r for r in item.sources if r in known]
                if not refs:
                    dropped += 1
                    continue
                kept.append({**item.model_dump(exclude_none=True), "sources": refs})
            points[key] = kept
        return BrokerView(
            scope, name, len(blocks), parsed.summary, parsed.method_consensus,
            parsed.multiple_range, points, dropped,
            reply.prompt_tokens + reply.completion_tokens, reply.cached,
        )  # fmt: skip
