"""The product taxonomy of config/industry_chain, loaded for lookups (plan 12 ph1, D-097, D-107)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from quant_cn.core.exceptions import ConfigError
from quant_cn.industry_graph.taxonomy_change_set import TaxonomyChange, TaxonomyChangeSet

MERGED_FILE = "_merged_ids.yaml"
LABEL_TYPES = ("product", "segment", "material")
EDGE_FIELDS = 3  # an edge is [subject, relation, object]  # node types a revenue line can name


@dataclass(frozen=True)
class TaxonomyNode:
    """
    Purpose:
        One node of the taxonomy as the matcher and views need it.

    Contract:
        Input:
            id: str; type: str; name: str; aliases: tuple[str, ...]; segment: str | None;
            parent: str | None; sector: str | None -- Shenwan L1 code of the file;
            context_aliases: tuple[str, ...] -- short wordings (板材, 生猪) that count only as an
            exact line of a company whose Shenwan context holds the node
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
    context_aliases: tuple[str, ...] = ()

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
        Load config/industry_chain/*.yaml once (taxonomy v0), then apply the accepted change
        sets in order (TaxonomyChangeSet: upsert adds a node or updates name / segment / parent
        and aliases; retire removes a node, moves its children and products to the successor
        and resolves its id there; `version` is the last set applied): nodes (names and
        aliases always strings, even when YAML reads "1,4-丁二醇" style values as numbers),
        the merged-id map, the Shenwan L3 → segment map (`sw_l3_map`) and the prior edges
        (`edges`). Answers which segments and products belong to a company's Shenwan codes,
        which is the context ProductMatcher uses.

    Contract:
        Input:
            folder: Path  -- config/industry_chain
            change_sets: Sequence[TaxonomyChangeSet]  -- accepted versions, in order (default
                                                         none: v0)
        Output:
            instance; `version`, `get_node`, `get_surviving_id`, `get_segment_id`,
            `list_nodes`, `list_edges`, `list_context_ids`
        Raises:
            ConfigError  -- folder missing, a file that is not a mapping, a duplicate node id,
                            an edge with fewer than three fields

    Used by:
        industry_graph.NodeLineageBuilder  -- taxonomy before and after a version
        industry_graph.NodeMemberBuilder  -- node segment and sector
        industry_graph.NodeEdgeBuilder  -- prior edges and their segments
        cli.DocumentCommands  -- `build-graph` wiring
        industry_graph.ProductMatcher  -- labels and context
        research_space chain_view build_market_view.py

    Test cases:
        TC-PT-001  load: nodes with string names, sector from the file, merged id resolved
        TC-PT-002  list_context_ids: segments of an L3 code plus their child segments and the
                   products in them; unknown code -> empty set
        TC-PT-003  duplicate id or missing folder raises ConfigError
        TC-PT-004  change sets: upsert adds a node and updates an existing one (aliases merged,
                   drop_aliases removed, sector kept); retire moves products to the
                   successor and get_surviving_id resolves it; version is the last set
        TC-PT-005  context_aliases load from a file and are added by an upsert
        TC-PT-006  list_edges keeps the asked relations, translates a retired end to its
                   successor, drops an unknown end and duplicates; get_segment_id gives the
                   segment of a product, the segment itself, None for a material without one
    """

    def __init__(self, folder: Path, change_sets: Sequence[TaxonomyChangeSet] = ()) -> None:
        if not folder.is_dir():
            raise ConfigError(f"taxonomy folder not found: {folder}")
        self._nodes: dict[str, TaxonomyNode] = {}
        self._sw: dict[str, list[str]] = {}
        self._edges: list[tuple[str, str, str]] = []
        for path in sorted(folder.glob("*.yaml")):
            if path.name == MERGED_FILE:
                continue
            self._load_file(path)
        merged_path = folder / MERGED_FILE
        merged = yaml.safe_load(merged_path.read_text()) if merged_path.exists() else {}
        self._merged = {str(k): str(v) for k, v in (merged or {}).items()}
        self._version = "v0"
        for change_set in change_sets:
            for change in change_set.changes:
                self._record_change(change)
            self._version = change_set.version

    @property
    def version(self) -> str:
        """
        Purpose:
            The taxonomy version loaded: "v0" (the YAML files) or the last change set applied.

        Contract:
            Input:
                (none)
            Output:
                str
            Raises:
                (none)
        """
        return self._version

    def _record_change(self, change: TaxonomyChange) -> None:
        if change.op == "retire":
            self._remove_node(str(change.id), str(change.successor))
            return
        raw = dict(change.node or {})
        node_id = str(raw["id"])
        self._merged.pop(node_id, None)  # a node added again is no longer retired
        old = self._nodes.get(node_id)
        kept = [a for a in (old.aliases if old else ()) if a not in change.drop_aliases]
        added = [str(a) for a in raw.get("aliases") or [] if str(a) not in kept]
        short_old = old.context_aliases if old else ()
        short_new = [str(a) for a in raw.get("context_aliases") or [] if str(a) not in short_old]
        self._nodes[node_id] = TaxonomyNode(
            node_id, str(raw["type"]), str(raw["name"]), (*kept, *added),
            raw.get("segment", old.segment if old else None),
            raw.get("parent", old.parent if old else None),
            old.sector if old else change.sector,
            (*short_old, *short_new),
        )  # fmt: skip
        for code in raw.get("sw_l3") or []:
            self._sw.setdefault(str(code), []).append(node_id)

    def _remove_node(self, node_id: str, successor: str) -> None:
        self._nodes.pop(node_id, None)
        self._merged[node_id] = successor
        for key, node in list(self._nodes.items()):
            if node_id in (node.segment, node.parent):
                segment = successor if node.segment == node_id else node.segment
                parent = successor if node.parent == node_id else node.parent
                self._nodes[key] = replace(node, segment=segment, parent=parent)
        for code, segments in self._sw.items():
            self._sw[code] = [successor if s == node_id else s for s in segments]

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
                tuple(str(a) for a in raw.get("context_aliases") or []),
            )  # fmt: skip
        for code, segments in (doc.get("sw_l3_map") or {}).items():
            self._sw.setdefault(str(code), []).extend(str(s) for s in segments or [])
        for edge in doc.get("edges") or []:
            if len(edge) < EDGE_FIELDS:
                raise ConfigError(f"{path.name}: edge {edge!r} is not [subject, relation, object]")
            self._edges.append((str(edge[0]), str(edge[1]), str(edge[2])))

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

    def list_edges(self, relations: tuple[str, ...]) -> list[tuple[str, str, str]]:
        """
        Purpose:
            The prior edges of the YAML files (README: [subject, relation, object]) of the
            given relations, with retired or merged ids translated to their successors; edges
            whose ends no longer exist are dropped. File order, duplicates removed.

        Contract:
            Input:
                relations: tuple[str, ...]  -- e.g. ("upstream_of", "component_of")
            Output:
                list[tuple[str, str, str]]  -- (subject, relation, object)
            Raises:
                (none)
        """
        seen: dict[tuple[str, str, str], None] = {}
        for subject, relation, obj in self._edges:
            if relation not in relations:
                continue
            ends = (self.get_node(subject), self.get_node(obj))
            if ends[0] is not None and ends[1] is not None:
                seen.setdefault((ends[0].id, relation, ends[1].id), None)
        return list(seen)

    def get_segment_id(self, node_id: str) -> str | None:
        """
        Purpose:
            The segment a node belongs to: the node itself for a segment, else its segment.

        Contract:
            Input:
                node_id: str
            Output:
                str | None  -- None for an unknown node or one without a segment (most materials)
            Raises:
                (none)
        """
        node = self.get_node(node_id)
        if node is None:
            return None
        if node.type == "segment":
            return node.id
        segment = self.get_node(node.segment) if node.segment else None
        return segment.id if segment is not None else None

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
