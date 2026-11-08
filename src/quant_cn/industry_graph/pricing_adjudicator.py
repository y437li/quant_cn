"""DeepSeek adjudicates pricing power and archetype where the rules leave it open (D-118)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError

PROMPT = Path(__file__).with_name("prompts") / "pricing_adjudication.txt"
LABELS = ("maker", "lean_maker", "middle", "lean_taker", "taker")
CONFIDENCE = ("high", "medium", "low")


class Reason(BaseModel):
    """
    Purpose:
        One reason for the verdict with the evidence keys it rests on.

    Contract:
        Input:
            point: str; sources: list[str] -- keys of the supplied evidence (P1..P6, T1, A1.., B)
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.AdjudicationReply   -- reasons
        industry_graph.PricingAdjudicator  -- citation check of each reason

    Test cases:
        TC-PAD-002  (via PricingAdjudicator) reasons citing unknown keys dropped
    """

    model_config = ConfigDict(extra="ignore")
    point: str
    sources: list[str] = []


class AdjudicationReply(BaseModel):
    """
    Purpose:
        The LLM reply before validation.

    Contract:
        Input:
            label, confidence: str; archetype_ok: bool | None; archetype: str | None;
            variant_note: str | None; reasons: list[Reason]
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.PricingAdjudicator  -- validates every reply

    Test cases:
        TC-PAD-003  (via PricingAdjudicator) malformed reply raises DataSourceError
    """

    model_config = ConfigDict(extra="ignore")
    label: str
    confidence: str = "low"
    archetype_ok: bool | None = None
    archetype: str | None = None
    variant_note: str | None = None
    reasons: list[Reason] = []


@dataclass(frozen=True)
class Adjudication:
    """
    Purpose:
        The validated verdict.

    Contract:
        Input:
            label: str (LABELS); confidence: str (CONFIDENCE); archetype_ok: bool | None;
            archetype: str | None (one of the allowed ids); variant_note: str | None;
            reasons: list[dict]; dropped: int; tokens: int; cached: bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.PricingAdjudicator  -- returned by fetch_verdict

    Test cases:
        TC-PAD-001  (via PricingAdjudicator) fields from a valid reply
    """

    label: str
    confidence: str
    archetype_ok: bool | None = None
    archetype: str | None = None
    variant_note: str | None = None
    reasons: list[dict[str, Any]] = field(default_factory=list)
    dropped: int = 0
    tokens: int = 0
    cached: bool = False


class PricingAdjudicator:
    """
    Purpose:
        For a company whose rule-based pricing-power label is insufficient or whose archetype check
        is inconsistent (BUSINESS_MODEL_DESIGN §4.5, §4b.7), give the model every measured signal,
        the annual-report claims and the broker-view summary, each under a key, and ask for one
        label, a confidence, whether the default archetype holds (or which allowed archetype fits)
        and the reasons. The citation check: reasons must cite supplied keys (unknown keys
        removed; a reason left with none is dropped); a label, confidence or archetype outside the
        allowed values raises (label) or is cleared (archetype) so nothing unverifiable is stored.

    Contract:
        Input:
            llm:    BaseLlmClient
            system: str | None  -- prompt; default prompts/pricing_adjudication.txt
        Output:
            instance; `fetch_verdict`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/pricing_adjudication.py (D-118 run)

    Test cases:
        TC-PAD-001  valid reply: label, confidence, archetype verdict and cited reasons kept
        TC-PAD-002  unknown source keys removed, reason without keys dropped, archetype outside
                   the allowed ids cleared, unknown confidence becomes low
        TC-PAD-003  malformed reply or a label outside LABELS raises DataSourceError
    """

    def __init__(self, llm: BaseLlmClient, system: str | None = None) -> None:
        self._llm = llm
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_verdict(
        self,
        company: str,
        archetype: str,
        allowed_archetypes: Mapping[str, str],
        evidence: Mapping[str, str],
    ) -> Adjudication:
        """
        Purpose:
            Ask for the verdict and validate it.

        Contract:
            Input:
                company: str; archetype: str -- default id, e.g. "A1";
                allowed_archetypes: Mapping[str, str] -- id -> name;
                evidence: Mapping[str, str] -- key -> text (P1..P6, T1, A1.., B)
            Output:
                Adjudication
            Raises:
                DataSourceError  -- LLM failure, malformed reply, label outside LABELS
        """
        lines = "\n".join(f"[{k}] {v}" for k, v in evidence.items())
        arch = "；".join(f"{k} {v}" for k, v in allowed_archetypes.items())
        user = (
            f"公司：{company}\n默认原型：{archetype} {allowed_archetypes.get(archetype, '')}\n"
            f"可选原型：{arch}\n\n证据：\n{lines}"
        )
        reply = self._llm.fetch_json(self._system, user)
        try:
            parsed = AdjudicationReply.model_validate(reply.content)
        except ValidationError as exc:
            raise DataSourceError(f"{company}: reply does not fit the shape: {exc}") from exc
        if parsed.label not in LABELS:
            raise DataSourceError(f"{company}: label {parsed.label!r} not allowed")
        reasons, dropped = self._list_kept_reasons(parsed.reasons, set(evidence))
        archetype_id = parsed.archetype if parsed.archetype in allowed_archetypes else None
        confidence = parsed.confidence if parsed.confidence in CONFIDENCE else "low"
        return Adjudication(
            parsed.label, confidence, parsed.archetype_ok, archetype_id, parsed.variant_note,
            reasons, dropped, reply.prompt_tokens + reply.completion_tokens, reply.cached,
        )  # fmt: skip

    @staticmethod
    def _list_kept_reasons(
        reasons: Sequence[Reason], known: set[str]
    ) -> tuple[list[dict[str, Any]], int]:
        kept, dropped = [], 0
        for r in reasons:
            refs = [s for s in r.sources if s in known]
            if not refs:
                dropped += 1
                continue
            kept.append({"point": r.point, "sources": refs})
        return kept, dropped
