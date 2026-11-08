"""Revenue lines (主营构成 items) mapped to taxonomy nodes by rules (plan 12 phase 4, D-115)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy, TaxonomyNode

# lines that name no product: residuals, accounting items, eliminations
GENERIC = re.compile(
    r"^(其他[^：:]{0,6}|[^：:]{0,4}其他|配件|小计|合计|主营业务|其他业务.*|.*收益|.*抵[销消].*|.*调整.*|"
    r"产品销售|销售商品|提供劳务|服务费?收入|主营业务收入)$"
)
SUFFIX = re.compile(r"(收入|业务|销售|产品|系列|类|板块|行业|及服务|服务费)$")
SPLIT = re.compile(r"[、/及和与;；,，+]")
MIN_SCORE = 0.55
CONTEXT_BONUS = 0.2
SECTOR_FALLBACK_SCORE = 0.3
MIN_LABEL_CHARS = 2  # also the bigram size
MIN_DICE = 0.5  # overlap counts only for labels in the company's Shenwan context
MIN_INSIDE_CHARS = 3
# broad words that sit inside many specific labels: they match only a label equal to them
BROAD_WORDS = frozenset(
    [
        "技术服务",
        "技术开发",
        "服务",
        "工程",
        "工程施工",
        "施工",
        "销售",
        "运营",
        "咨询",
        "综合",
        "设备",
        "材料",
        "制品",
        "系统",
        "系统集成",
        "软件",
        "硬件",
        "配套",
        "加工",
        "解决方案",
        "租赁",
        "贸易",
        "物流",
        "维修",
        "安装",
        "检测",
        "设计",
        "开发",
    ]
)
MIN_INSIDE_SHARE = 0.5


@dataclass(frozen=True)
class ProductMatch:
    """
    Purpose:
        One taxonomy node a revenue line maps to, with how it was found.

    Contract:
        Input:
            node_id: str; score: float in (0, 1.2]; how: str -- exact | contains | overlap |
            part | sector
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        industry_graph.ProductMatcher  -- returned by find_matches

    Test cases:
        TC-PM-001  (via ProductMatcher) fields of an exact match
    """

    node_id: str
    score: float
    how: str


class ProductMatcher:
    """
    Purpose:
        Map a company's revenue line to taxonomy nodes without the LLM. Order: generic lines
        (其他, 投资收益, 抵销, ...) map to nothing and `is_generic` says so, so callers can drop
        them from the denominator; the name is normalized (parentheses and suffixes such as
        收入/业务/产品 removed; for "A:B:C" the leaf is tried first, then the top level); each
        product, segment or material label scores exact 1.0, contains 0.6-0.9 by length share
        (a line inside a label only with 3+ characters and half the label), character-bigram
        overlap up to 0.6 (only for labels in the company's context); labels inside the
        company's Shenwan context
        (ProductTaxonomy.list_context_ids) get CONTEXT_BONUS; the best label at or above
        MIN_SCORE wins (products before segments on ties). A compound line ("A、B及C") is
        split first; when two or more parts match, each part is a match, otherwise the whole
        line (or its one matching part) is matched. Last resort: a company whose
        Shenwan codes map to exactly one segment gets that segment with how="sector".

    Contract:
        Input:
            taxonomy: ProductTaxonomy
        Output:
            instance; `is_generic`, `find_matches`
        Raises:
            (none at construction)

    Used by:
        research_space chain_view build_market_view.py

    Test cases:
        TC-PM-001  exact name and alias match; suffix and parentheses stripped
        TC-PM-002  context bonus picks the in-sector label; a generic line returns [] and
                   is_generic True
        TC-PM-003  compound line split into two matches; hierarchical "A:B" uses the leaf,
                   then the top level
        TC-PM-004  sector fallback only when the Shenwan codes map to one segment
        TC-PM-005  no match for a short line inside a long label, nor for an overlap outside
                   the company's context, nor for a broad word (技术服务) inside a longer label
    """

    def __init__(self, taxonomy: ProductTaxonomy) -> None:
        self._taxonomy = taxonomy
        self._labels: list[tuple[str, TaxonomyNode]] = [
            (self._normalize(label), node)
            for node in taxonomy.list_nodes()
            for label in node.labels
            if len(self._normalize(label)) >= MIN_LABEL_CHARS
        ]
        # bigram -> label positions: only labels sharing a bigram with the line are scored
        self._by_bigram: dict[str, set[int]] = {}
        for k, (label, _) in enumerate(self._labels):
            for gram in self._list_bigrams(label):
                self._by_bigram.setdefault(gram, set()).add(k)
        self._contexts: dict[tuple[str, ...], set[str]] = {}

    @staticmethod
    def _list_bigrams(text: str) -> set[str]:
        return {text[i : i + MIN_LABEL_CHARS] for i in range(len(text) - 1)}

    @staticmethod
    def _normalize(text: str) -> str:
        text = re.sub(r"[（(].*?[)）]|\s+", "", str(text))
        while True:
            stripped = SUFFIX.sub("", text)
            if stripped == text or len(stripped) < MIN_LABEL_CHARS:
                return text
            text = stripped

    def is_generic(self, item: str) -> bool:
        """
        Purpose:
            True for lines that name no product (residuals, accounting items, eliminations).

        Contract:
            Input:
                item: str
            Output:
                bool
            Raises:
                (none)
        """
        return bool(GENERIC.match(re.sub(r"\s+", "", item)))

    def find_matches(self, item: str, sw_codes: list[str]) -> list[ProductMatch]:
        """
        Purpose:
            Taxonomy nodes for one revenue line.

        Contract:
            Input:
                item: str  -- 主营构成 item as reported
                sw_codes: list[str]  -- the company's Shenwan L2/L3 industry codes
            Output:
                list[ProductMatch]  -- [] for generic or unmatched lines; several for a split
                                       compound line
            Raises:
                (none)
        """
        if self.is_generic(item):
            return []
        key = tuple(sw_codes)
        if key not in self._contexts:
            self._contexts[key] = self._taxonomy.list_context_ids(sw_codes)
        context = self._contexts[key]
        levels = [p for p in re.split(r"[：:]", item) if p.strip()]
        for name in [levels[-1], *levels[:-1]] if len(levels) > 1 else levels:
            if self.is_generic(name):
                continue
            parts = [p for p in SPLIT.split(name) if len(self._normalize(p)) >= MIN_LABEL_CHARS]
            found = {m.node_id: m for m in (self._find_best(p, context) for p in parts) if m}
            if len(parts) > 1 and len(found) > 1:  # a compound line naming several products
                return [ProductMatch(m.node_id, m.score, "part") for m in found.values()]
            best = self._find_best(name, context) or next(iter(found.values()), None)
            if best:
                return [best]
        parents = {
            n.id: n.parent
            for n in (self._taxonomy.get_node(i) for i in context)
            if n is not None and n.type == "segment"
        }
        roots = [seg for seg, parent in parents.items() if parent not in parents]
        if len(roots) == 1:
            return [ProductMatch(roots[0], SECTOR_FALLBACK_SCORE, "sector")]
        return []

    def _find_best(self, name: str, context: set[str]) -> ProductMatch | None:
        target = self._normalize(name)
        if len(target) < MIN_LABEL_CHARS:
            return None
        best: tuple[float, int, str, str] | None = None
        positions = set().union(
            *(self._by_bigram.get(g, set()) for g in self._list_bigrams(target))
        )
        for k in sorted(positions):
            label, node = self._labels[k]
            score, how = self._compute_score(target, label)
            if score <= 0 or (how == "overlap" and node.id not in context):
                continue
            score += CONTEXT_BONUS if node.id in context else 0.0
            rank = 1 if node.type == "product" else 0
            if best is None or (score, rank) > (best[0], best[1]):
                best = (score, rank, node.id, how)
        if best is None or best[0] < MIN_SCORE:
            return None
        return ProductMatch(best[2], round(best[0], 3), best[3])

    @staticmethod
    def _compute_score(target: str, label: str) -> tuple[float, str]:
        if target == label:
            return 1.0, "exact"
        if label in target:
            return 0.6 + 0.3 * len(label) / len(target), "contains"
        if target in label and target in BROAD_WORDS:
            return 0.0, ""
        if target in label:  # a short line inside a long label ("配套" in "光刻胶配套试剂")
            share = len(target) / len(label)
            ok = len(target) >= MIN_INSIDE_CHARS and share >= MIN_INSIDE_SHARE
            return (0.55 + 0.3 * share, "contains") if ok else (0.0, "")
        a = ProductMatcher._list_bigrams(target)
        b = ProductMatcher._list_bigrams(label)
        if not a or not b:
            return 0.0, ""
        dice = 2 * len(a & b) / (len(a) + len(b))
        return (0.6 * dice, "overlap") if dice >= MIN_DICE else (0.0, "")
