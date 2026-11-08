"""The product taxonomy of config/industry_chain, loaded for lookups (plan 12 ph1, D-097, D-107)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from quant_cn.core.exceptions import ConfigError

MERGED_FILE = "_merged_ids.yaml"
LABEL_TYPES = ("product", "segment", "material")  # node types a revenue line can name


@dataclass(frozen=True)
class TaxonomyNode:
    """
    Purpose:
        One node of the taxonomy as the matcher and views need it.

    Contract:
        Input:
            id: str; type: str; name: str; aliases: tuple[str, ...]; segment: str | None;
            parent: str | None; sector: str | None -- Shenwan L1 code of the file
        Output:
            frozen dataclass; `labels`
        Raises:
            (none)

    Used by:
        industry_graph.ProductTaxonomy  -- nodes
        industry_graph.ProductMatcher   -- candidate labels

    Test cases:
        TC-PT-001  (via ProductTaxonomy) names and aliases loaded as strings
    """

    id: str
    type: str
    name: str
    aliases: tuple[str, ...] = ()
    segment: str | None = None
    parent: str | None = None
    sector: str | None = None

    @property
    def labels(self) -> tuple[str, ...]:
        """
        Purpose:
            Name and aliases.

        Contract:
            Input:
                (none)
            Output:
                tuple[str, ...]
            Raises:
                (none)
        """
        return (self.name, *self.aliases)


class ProductTaxonomy:
    """
    Purpose:
        Load config/industry_chain/*.yaml once: nodes (names and aliases always strings, even
        when YAML reads "1,4-丁二醇" style values as numbers), the merged-id map, and the
        Shenwan L3 → segment map (`sw_l3_map`). Answers which segments and products belong to a
        company's Shenwan codes, which is the context ProductMatcher uses.

    Contract:
        Input:
            folder: Path  -- config/industry_chain
        Output:
            instance; `get_node`, `get_surviving_id`, `list_nodes`, `list_context_ids`
        Raises:
            ConfigError  -- folder missing, a file that is not a mapping, a duplicate node id

    Used by:
        industry_graph.ProductMatcher  -- labels and context
        research_space chain_view build_market_view.py

    Test cases:
        TC-PT-001  load: nodes with string names, sector from the file, merged id resolved
        TC-PT-002  list_context_ids: segments of an L3 code plus their child segments and the
                   products in them; unknown code -> empty set
        TC-PT-003  duplicate id or missing folder raises ConfigError
    """

    def __init__(self, folder: Path) -> None:
        if not folder.is_dir():
            raise ConfigError(f"taxonomy folder not found: {folder}")
        self._nodes: dict[str, TaxonomyNode] = {}
        self._sw: dict[str, list[str]] = {}
        for path in sorted(folder.glob("*.yaml")):
            if path.name == MERGED_FILE:
                continue
            self._load_file(path)
        merged_path = folder / MERGED_FILE
        merged = yaml.safe_load(merged_path.read_text()) if merged_path.exists() else {}
        self._merged = {str(k): str(v) for k, v in (merged or {}).items()}

    def _load_file(self, path: Path) -> None:
        doc: Any = yaml.safe_load(path.read_text()) or {}
        if not isinstance(doc, dict):
            raise ConfigError(f"{path.name}: not a mapping")
        sector = str((doc.get("sector") or {}).get("sw_l1", "")) or None
        for raw in doc.get("nodes") or []:
            node_id = str(raw["id"])
            if node_id in self._nodes:
                raise ConfigError(f"{path.name}: duplicate node id {node_id}")
            self._nodes[node_id] = TaxonomyNode(
                node_id, str(raw["type"]), str(raw["name"]),
                tuple(str(a) for a in raw.get("aliases") or []),
                raw.get("segment"), raw.get("parent"), sector,
            )  # fmt: skip
        for code, segments in (doc.get("sw_l3_map") or {}).items():
            self._sw.setdefault(str(code), []).extend(str(s) for s in segments or [])

    def get_node(self, node_id: str) -> TaxonomyNode | None:
        """
        Purpose:
            The node for an id, after translating a merged id.

        Contract:
            Input:
                node_id: str
            Output:
                TaxonomyNode | None
            Raises:
                (none)
        """
        return self._nodes.get(self.get_surviving_id(node_id))

    def get_surviving_id(self, node_id: str) -> str:
        """
        Purpose:
            Translate an id removed by the cross-sector merge to its surviving id.

        Contract:
            Input:
                node_id: str
            Output:
                str  -- unchanged when not merged
            Raises:
                (none)
        """
        return self._merged.get(node_id, node_id)

    def list_nodes(self, types: tuple[str, ...] = LABEL_TYPES) -> list[TaxonomyNode]:
        """
        Purpose:
            Nodes of the given types, in file order.

        Contract:
            Input:
                types: tuple[str, ...]
            Output:
                list[TaxonomyNode]
            Raises:
                (none)
        """
        return [n for n in self._nodes.values() if n.type in types]

    def list_context_ids(self, sw_codes: list[str]) -> set[str]:
        """
        Purpose:
            Segments mapped to the company's Shenwan codes (with their child segments) and the
            products in those segments.

        Contract:
            Input:
                sw_codes: list[str]  -- Shenwan L2/L3 industry codes, e.g. ["740100", "740101"]
            Output:
                set[str]  -- node ids; empty when no code is mapped
            Raises:
                (none)
        """
        segments = {s for code in sw_codes for s in self._sw.get(code, [])}
        changed = True
        while changed:
            children = {
                n.id for n in self._nodes.values()
                if n.type == "segment" and n.parent in segments and n.id not in segments
            }  # fmt: skip
            segments |= children
            changed = bool(children)
        products = {n.id for n in self._nodes.values() if n.segment in segments}
        return segments | products
