"""DeepSeek groups counterparty names that mean the same entity (plan 28 ph3)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from quant_cn.core.base_llm_client import BaseLlmClient
from quant_cn.core.exceptions import DataSourceError

PROMPT = Path(__file__).with_name("prompts") / "entity_alias.txt"
KINDS = (
    "company",
    "government",
    "university",
    "institute",
    "hospital",
    "person",
    "generic",
    "unknown",
)
CODE = re.compile(r"^(?:\d{6}\.(?:SH|SZ|BJ)|\d{4,5}\.HK|[A-Z][A-Z.\-]{0,9}\.US)$")


class AliasItem(BaseModel):
    """
    Purpose:
        One reply row of EntityAliasExtractor, before the checks.

    Contract:
        Input:
            name: str; canonical: str; kind: str; is_member: bool; listed: str | None;
            parent: str | None
        Output:
            pydantic model (unknown keys ignored)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.EntityAliasExtractor  -- validates reply items

    Test cases:
        TC-EAX-001  (via EntityAliasExtractor) rows kept and dropped
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    canonical: str
    kind: str
    is_member: bool = False
    listed: str | None = None
    parent: str | None = None


@dataclass(frozen=True)
class EntityAlias:
    """
    Purpose:
        The entity one name stands for, as the model proposed it.

    Contract:
        Input:
            name: str (as asked); canonical: str; kind: str (KINDS); is_member: bool;
            listed: str | None (security code, format-checked only); parent: str | None
            (short name of the parent or group when is_member)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.EntityAliasExtractor  -- returned by fetch_aliases

    Test cases:
        TC-EAX-001  (via EntityAliasExtractor) fields of a kept row
    """

    name: str
    canonical: str
    kind: str
    is_member: bool
    listed: str | None
    parent: str | None = None


class EntityAliasExtractor:
    """
    Purpose:
        Ask the model which entity each of a batch of counterparty names stands for (plan 28
        ph3, D-161 update 9): its common short name (宁德时代, 华为, LG新能源), its kind (company,
        government, university …, generic, unknown), whether the name is a subsidiary or
        branch of it (with the parent's short name), and its security code when listed. Each
        name is sent with a line of context (who mentioned it, role, product). A row is kept
        when its name is one that was asked, its kind is known and its canonical name is not
        empty; a security code not of the form 600941.SH / 0700.HK / TSLA.US is set to None.
        The code is only a hint: the caller resolves the canonical name (or the parent's
        short name) against the A-share list itself.

    Contract:
        Input:
            llm: BaseLlmClient; system: str | None (default prompts/entity_alias.txt)
        Output:
            instance; `fetch_aliases(names) -> list[EntityAlias]`
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/plan28_entities.py (plan 28 phase 3)

    Test cases:
        TC-EAX-001  valid reply: rows kept; a name not asked, an unknown kind, an empty
                    canonical and a malformed row dropped; a bad code becomes None
        TC-EAX-002  a reply without an items list raises DataSourceError; no names, no call
    """

    def __init__(self, llm: BaseLlmClient, system: str | None = None) -> None:
        self._llm = llm
        self._system = system if system is not None else PROMPT.read_text(encoding="utf-8")

    def fetch_aliases(self, names: Sequence[tuple[str, str]]) -> list[EntityAlias]:
        """
        Purpose:
            The entity of every name in one batch.

        Contract:
            Input:
                names: Sequence[tuple[str, str]]  -- (name, context line)
            Output:
                list[EntityAlias]  -- at most one per asked name, in reply order
            Raises:
                DataSourceError  -- LLM failure or a reply without an items list
        """
        if not names:
            return []
        user = "\n".join(f"{n}｜{ctx}" for n, ctx in names)
        reply = self._llm.fetch_json(self._system, f"名称｜上下文：\n{user}")
        raw = reply.content.get("items")
        if not isinstance(raw, list):
            raise DataSourceError("entity alias reply has no items list")
        asked = {n for n, _ in names}
        out: dict[str, EntityAlias] = {}
        for entry in raw:
            alias = self._build_alias(entry, asked)
            if alias is not None and alias.name not in out:
                out[alias.name] = alias
        return list(out.values())

    @staticmethod
    def _build_alias(entry: object, asked: set[str]) -> EntityAlias | None:
        try:
            item = AliasItem.model_validate(entry)
        except ValidationError:
            return None
        canonical = item.canonical.strip()
        if item.name not in asked or item.kind not in KINDS or not canonical:
            return None
        code = (item.listed or "").strip().upper()
        listed = code if CODE.match(code) else None
        parent = (item.parent or "").strip() or None
        return EntityAlias(item.name, canonical, item.kind, item.is_member, listed, parent)
