"""One id per counterparty name across documents and periods (plan 28 ph3; plan 12 ph5)."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

SPACE = re.compile(r"[\s　·•.,，、\"“”'‘’]")
LEGAL_SUFFIX = re.compile(
    r"(?:股份有限公司|有限责任公司|有限公司|股份公司|集团公司|公司"
    r"|co\.?,?ltd\.?|ltd\.?|inc\.?|corp\.?|corporation|limited|llc|gmbh|ag)$"
)
# a group member written as the group plus a tail (及其关联方, 子公司4, 销售分公司, 及下属企业)
GROUP_TAIL = re.compile(
    r"(?:及其?(?:关联方|关联公司|关联企业|子公司|下属公司|下属企业|下属单位|控制的企业)"
    r"|子公司[0-9一二三四五六七八九十]*|下属公司|下属企业|[^\s]{0,8}分公司)$"
)
REGION = re.compile(r"\([^)]*\)")
SHORT_PREFIX = re.compile(r"^(?:\*?ST|S\*?ST|S|N|C|XD|XR|DR)(?=.)", re.I)
SHARE_CLASS = re.compile(r"[ab]$")  # 京东方A, 万科A: the company without its share class
MIN_KEY = 2  # a one-character name matches by chance
MIN_PREFIX = (
    4  # a listed short name used as a prefix must be this long (3 gives 史丹利百得 → 史丹利)
)


@dataclass(frozen=True)
class EntityMatch:
    """
    Purpose:
        Where one counterparty name resolved to.

    Contract:
        Input:
            name: str (as written); entity_id: str ("a:<ts_code>" for an A-share company,
            else the alias map's id, else "x:<key>"); ts_code: str | None; method: str
            (alias / full / short / former / prefix / code / member_code / unresolved);
            is_group_member: bool (a subsidiary, branch or "及其关联方" form of the entity)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.EntityResolver  -- returned by find_entity
        industry_graph.GameCompanyBuilder  -- resolved licence holders

    Test cases:
        TC-ER-001  (via EntityResolver) every method's match
    """

    name: str
    entity_id: str
    ts_code: str | None
    method: str
    is_group_member: bool = False


class EntityResolver:
    """
    Purpose:
        Give every customer / supplier / partner name one entity id across documents and
        periods (plan 28 ph3, D-161 update 9). A name is keyed by `build_key` (whitespace and
        punctuation removed, lower case, full-width brackets folded, legal suffixes removed),
        then looked up in order: the alias map (canonical names an LLM pass proposed and the
        caller checked; e.g. 华为技术 → x:华为), A-share full names (stock_company), A-share
        short names in use (stock_basic, ST marks removed), former short names (namechange; method
        "former", a name another company may now use), the same four without a
        bracketed region, and last an A-share short name of at least MIN_PREFIX characters
        that starts the key (中国移动通信有限公司 → 中国移动; marked a group member). A lookup that
        hits two companies does not resolve. A group tail (及其关联方, 子公司4, 销售分公司) is
        cut first and marks the match a group member. Unresolved names get "x:<key>", so the
        same spelling in two documents still shares an id.

    Contract:
        Input:
            full_names:  Iterable[tuple[str, str]]  -- (ts_code, registered full name)
            short_names: Iterable[tuple[str, str]]  -- (ts_code, short name in use)
            aliases:     Mapping[str, str] | None   -- name or key -> entity id ("a:<ts_code>" or
                                                       "x:<canonical>")
            member_names: Iterable[str]             -- alias names that are a subsidiary or
                                                       branch of their entity
            former_names: Iterable[tuple[str, str]] -- (ts_code, short name no longer used);
                                                       checked after names in use
        Output:
            instance; `find_entity(name) -> EntityMatch`; `find_by_code(name, ts_code,
            is_member=False) -> EntityMatch | None`; `find_by_alias(name, canonical, listed,
            parent) -> EntityMatch | None`; `build_key(name) -> str` (static)
        Raises:
            (none)

    Used by:
        industry_graph.GraphBuilder  -- built over A-share names and entity_map
        lake meta/runs/plan28_entities.py (plan 28 phase 3)
        industry_graph.CompanyEdgeBuilder  -- resolves edge counterparties
        industry_graph.GameCompanyBuilder  -- licence holders through alias proposals
        cli.DocumentCommands  -- `build-graph` builds it for game_company

    Test cases:
        TC-ER-001  full name, short name, former short name, alias, prefix and unresolved
                   names resolve by that method; ST marks and regions are ignored
        TC-ER-002  a group tail is cut and marks a group member; a 3-character prefix does
                   not resolve; a short name shared by two companies does not resolve
        TC-ER-003  build_key folds spaces, case, brackets and legal suffixes
        TC-ER-004  find_by_code accepts a code whose short name (share class removed) or full
                   name starts with the name (京东方 → 000725.SZ via 京东方A); refuses an
                   unknown code or one whose names do not start with it
        TC-ER-005  an alias listed in member_names resolves as a group member
        TC-ER-006  a short name two companies used at different times resolves to the one
                   using it now; a name only a former company used resolves as "former"
        TC-ER-007  find_by_code with is_member accepts any known code as member_code (a group
                   member); an unknown code is still refused
        TC-ER-008  find_by_alias: canonical short name, proposed code, and a member whose
                   parent resolves (member_code); an unlisted canonical or an unknown parent
                   gives None
    """

    def __init__(
        self,
        full_names: Iterable[tuple[str, str]],
        short_names: Iterable[tuple[str, str]],
        aliases: Mapping[str, str] | None = None,
        member_names: Iterable[str] = (),
        former_names: Iterable[tuple[str, str]] = (),
    ) -> None:
        self._full = self._build_index(full_names)
        self._short = self._build_index(
            (ts, SHORT_PREFIX.sub("", name or "")) for ts, name in short_names
        )
        self._former = self._build_index(
            (ts, SHORT_PREFIX.sub("", name or "")) for ts, name in former_names
        )
        self._aliases = {self.build_key(k): v for k, v in (aliases or {}).items()}
        self._members = {self.build_key(n) for n in member_names}
        self._names_of: dict[str, set[str]] = {}
        for index in (self._full, self._short, self._former):
            for key, codes in index.items():
                for ts in codes:
                    self._names_of.setdefault(ts, set()).update({key, SHARE_CLASS.sub("", key)})

    @staticmethod
    def build_key(name: str) -> str:
        """
        Purpose:
            The lookup key of a name.

        Contract:
            Input:
                name: str
            Output:
                str  -- may be empty
            Raises:
                (none)
        """
        key = SPACE.sub("", name or "").lower().replace("（", "(").replace("）", ")")
        previous = None
        while previous != key:
            previous, key = key, LEGAL_SUFFIX.sub("", key)
        return key

    def find_entity(self, name: str) -> EntityMatch:
        """
        Purpose:
            Resolve one name.

        Contract:
            Input:
                name: str  -- as written in the document
            Output:
                EntityMatch
            Raises:
                (none)
        """
        key = self.build_key(name)
        cut = self.build_key(GROUP_TAIL.sub("", key))
        member = bool(cut) and cut != key
        key = cut or key
        for candidate in dict.fromkeys((key, self.build_key(REGION.sub("", key)))):
            hit = self._find_exact(name, candidate, member)
            if hit is not None:
                return hit
        for size in range(len(key) - 1, MIN_PREFIX - 1, -1):
            codes = self._short.get(key[:size], set())
            if len(codes) == 1:
                ts = next(iter(codes))
                return EntityMatch(name, f"a:{ts}", ts, "prefix", True)
        return EntityMatch(name, f"x:{key}", None, "unresolved", member)

    def find_by_code(self, name: str, ts_code: str, is_member: bool = False) -> EntityMatch | None:
        """
        Purpose:
            Confirm a proposed A-share code for a name: the code is known and one of its
            names (short name without share class, or full name) starts with the name's key
            (method "code"). For a name proposed as a subsidiary, brand or branch of the
            listed company (is_member), a known code is enough: 埃安 does not start any name of
            广汽集团 (method "member_code", a group member).

        Contract:
            Input:
                name: str; ts_code: str  -- e.g. a code an LLM proposed;
                is_member: bool          -- the name was proposed as part of that company
            Output:
                EntityMatch (method "code" or "member_code") | None
            Raises:
                (none)
        """
        key = self.build_key(name)
        known = self._names_of.get(ts_code, set())
        if len(key) >= MIN_KEY and any(k.startswith(key) for k in known):
            return EntityMatch(name, f"a:{ts_code}", ts_code, "code", is_member)
        if is_member and known:
            return EntityMatch(name, f"a:{ts_code}", ts_code, "member_code", True)
        return None

    def find_by_alias(
        self, name: str, canonical: str, listed: str | None, parent: str | None
    ) -> EntityMatch | None:
        """
        Purpose:
            Resolve a name through an LLM alias proposal (EntityAliasExtractor), checked by
            rule: the canonical name by `find_entity`; else the proposed A-share code by
            `find_by_code`; else, for a proposed group member, the parent's short or full name
            must resolve by rule, and the name becomes a member of that company (method
            "member_code"). Only A-share matches (full / short / code / member_code) count.

        Contract:
            Input:
                name: str (as written); canonical: str; listed: str | None (".SH" / ".SZ" /
                ".BJ" codes only are tried); parent: str | None (set for a group member)
            Output:
                EntityMatch named `name` | None
            Raises:
                (none)
        """
        found = self.find_entity(canonical)
        if found.ts_code is None and listed and listed[-3:] in (".SH", ".SZ", ".BJ"):
            found = self.find_by_code(canonical, listed) or found
        if found.ts_code is None and parent:
            owner = self.find_entity(parent)
            if owner.ts_code is not None and owner.method in ("full", "short"):
                ts = owner.ts_code
                found = EntityMatch(name, f"a:{ts}", ts, "member_code", True)
        if found.ts_code is None or found.method not in ("full", "short", "code", "member_code"):
            return None
        member = found.is_group_member or bool(parent)
        return EntityMatch(name, found.entity_id, found.ts_code, found.method, member)

    def _find_exact(self, name: str, key: str, member: bool) -> EntityMatch | None:
        if key in self._aliases:
            entity = self._aliases[key]
            ts = entity[2:] if entity.startswith("a:") else None
            return EntityMatch(name, entity, ts, "alias", member or key in self._members)
        lookups = (("full", self._full), ("short", self._short), ("former", self._former))
        for method, index in lookups:
            codes = index.get(key, set())
            if len(codes) == 1:
                ts = next(iter(codes))
                return EntityMatch(name, f"a:{ts}", ts, method, member)
        return None

    @classmethod
    def _build_index(cls, pairs: Iterable[tuple[str, str]]) -> dict[str, set[str]]:
        index: dict[str, set[str]] = {}
        for ts, name in pairs:
            key = cls.build_key(name)
            if len(key) >= MIN_KEY:
                index.setdefault(key, set()).add(ts)
        return index
