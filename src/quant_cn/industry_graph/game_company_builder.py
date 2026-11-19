"""game_company: which listed company publishes or operates each approved game (plan 31 ph2)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from quant_cn.industry_graph.entity_resolver import EntityMatch, EntityResolver

GAME_COMPANY_COLUMNS = [
    "game", "approval_no", "role", "holder", "entity_id", "ts_code", "method", "is_member",
    "category", "origin", "approved_on", "known_on", "source",
]  # fmt: skip
UNRESOLVED_COLUMNS = ["holder", "games", "roles"]
ALIAS_COLUMNS = ["name", "canonical", "kind", "is_member", "listed", "parent"]
PUBLISHING_HOUSE = ("出版", "音像")  # licence holders that publish for others
ROLES = {"operator": "运营单位", "publisher": "出版单位"}
RULE_METHODS = ("full", "short", "prefix")


class GameCompanyBuilder:
    """
    Purpose:
        Link every approved game (dataset `game_license`, 版号) to the companies behind it (plan
        31 ph2): one row per (approval, role) for role operator (运营单位) and publisher (出版单位).
        A holder name resolves by rule (`EntityResolver.find_entity`: full, short or prefix
        name of an A-share company); a name the rules leave unresolved, or resolve only by
        prefix, uses its model proposal in `aliases` (`game_alias` table, written by the lake
        script meta/runs/plan31_game_aliases.py) through `EntityResolver.find_by_alias`, so 上海
        巨人网络科技有限公司 becomes a member of 巨人网络. A prefix match the proposal does not
        confirm is dropped. Publishing houses (出版 / 音像 in the name) are kept with method
        "publishing_house" and no company. known_on is the list's publication date.

    Contract:
        Input:
            resolver: EntityResolver  -- over A-share full, short and former names
            aliases: Mapping[str, Mapping[str, Any]]  -- holder name -> ALIAS_COLUMNS values
        Output:
            instance; `build_links(licenses) -> DataFrame` (GAME_COMPANY_COLUMNS);
            `list_unresolved(links) -> DataFrame` (UNRESOLVED_COLUMNS)
        Raises:
            (none)

    Used by:
        cli.DocumentCommands  -- `build-graph` writes game_company

    Test cases:
        TC-GCB-001  a full / short name resolves by rule; a subsidiary resolves through its
                    proposal (alias_<method>, a group member); a publishing house gets method
                    publishing_house
        TC-GCB-002  a prefix match the proposal contradicts is dropped (unresolved); a name
                    without proposal and rule stays unresolved; list_unresolved counts games
                    per holder, most first; empty licences give empty frames with columns
    """

    def __init__(self, resolver: EntityResolver, aliases: Mapping[str, Mapping[str, Any]]):
        self._resolver = resolver
        self._aliases = aliases

    def build_links(self, licenses: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            One row per (approval, role) with the resolved company.

        Contract:
            Input:
                licenses: DataFrame  -- game_license columns (approval_no, name, category,
                                        publisher, operator, approved_on, published, origin)
            Output:
                DataFrame  -- GAME_COMPANY_COLUMNS, ts_code None where unresolved
            Raises:
                (none)
        """
        cache: dict[str, tuple[EntityMatch | None, str]] = {}
        rows: list[dict[str, Any]] = []
        for lic in licenses.itertuples(index=False):
            for role in ROLES:
                holder = getattr(lic, role)
                if not isinstance(holder, str) or not holder:
                    continue
                if holder not in cache:
                    cache[holder] = self._find_company(holder)
                match, method = cache[holder]
                rows.append({
                    "game": lic.name, "approval_no": lic.approval_no, "role": role,
                    "holder": holder, "entity_id": match.entity_id if match else None,
                    "ts_code": match.ts_code if match else None, "method": method,
                    "is_member": bool(match and match.is_group_member),
                    "category": lic.category, "origin": lic.origin,
                    "approved_on": lic.approved_on, "known_on": lic.published, "source": "nppa",
                })  # fmt: skip
        return pd.DataFrame(rows, columns=GAME_COMPANY_COLUMNS)

    def list_unresolved(self, links: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Holders without a company (publishing houses excluded), for review.

        Contract:
            Input:
                links: DataFrame  -- build_links output
            Output:
                DataFrame  -- UNRESOLVED_COLUMNS, most games first
            Raises:
                (none)
        """
        lost = links[links["ts_code"].isna() & (links["method"] != "publishing_house")]
        if lost.empty:
            return pd.DataFrame(columns=UNRESOLVED_COLUMNS)
        grouped = lost.groupby("holder").agg(
            games=("approval_no", "nunique"), roles=("role", lambda r: ",".join(sorted(set(r))))
        )
        out = grouped.reset_index().sort_values(["games", "holder"], ascending=[False, True])
        return out[UNRESOLVED_COLUMNS].reset_index(drop=True)

    def _find_company(self, holder: str) -> tuple[EntityMatch | None, str]:
        if any(word in holder for word in PUBLISHING_HOUSE):
            return None, "publishing_house"
        rule = self._resolver.find_entity(holder)
        proposal = self._aliases.get(holder)
        if rule.ts_code is not None and rule.method in ("full", "short"):
            return rule, rule.method
        if proposal is not None:
            text = {k: v if isinstance(v, str) and v else None for k, v in proposal.items()}
            found = self._resolver.find_by_alias(
                holder, text.get("canonical") or holder, text.get("listed"), text.get("parent")
            )
            if found is not None:
                return found, f"alias_{found.method}"
            return None, "unresolved"
        if rule.ts_code is not None and rule.method in RULE_METHODS:
            return rule, rule.method
        return None, "unresolved"
