"""Rebuild company_edge and edge_span from the label store and the entity map (plan 28 ph4)."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping

import pandas as pd

from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader
from quant_cn.industry_graph.company_edge_builder import EDGE_COLUMNS, CompanyEdgeBuilder
from quant_cn.industry_graph.company_period_builder import CompanyPeriodBuilder
from quant_cn.industry_graph.edge_span_builder import EdgeSpanBuilder
from quant_cn.industry_graph.entity_resolver import EntityResolver
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.label_store import LabelStore

logger = logging.getLogger(__name__)

NOT_NODES = ("generic", "unknown", "person")  # entity kinds that do not become graph nodes
NamePairs = Iterable[tuple[str, str]]


class GraphBuilder:
    """
    Purpose:
        Rebuild the company graph tables (plan 28 ph4, D-161 updates 7, 9-11) from what the
        lake holds: every label set that has a reader is read from the LabelStore, its edges
        are built by CompanyEdgeBuilder with an EntityResolver over the A-share names and the
        `entity_map` of the GraphStore (names the entity pass asked: alias to their entity id;
        kinds in NOT_NODES skipped; is_member names flagged), then EdgeSpanBuilder joins them
        into spans. Writes `company_edge` (sorted by src, dst, known_on, doc_key), `edge_span`
        and `company_period` (CompanyPeriodBuilder over every label set). No LLM call: the
        same lake gives the same tables.

    Contract:
        Input:
            labels:  LabelStore
            graph:   GraphStore
            readers: Mapping[str, BaseEdgeReader]  -- label set -> reader
            spans:   EdgeSpanBuilder
            leaf:    CompanyPeriodBuilder
        Output:
            instance; `build(full, short, former, as_of=None) -> dict[str, int]` (rows per
            table written); `build_resolver(full, short, former) -> (EntityResolver, skipped
            names)`
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `build-graph`

    Test cases:
        TC-GB-001  build writes company_edge and edge_span from label rows; an alias of the
                   entity map is used and its member flag kept; a generic name is skipped
        TC-GB-002  building twice from the same lake gives identical tables
        TC-GB-003  label sets without rows give empty tables with their columns
        TC-GB-004  company_period is written with one row per label row of every set
    """

    def __init__(
        self,
        labels: LabelStore,
        graph: GraphStore,
        readers: Mapping[str, BaseEdgeReader],
        spans: EdgeSpanBuilder,
        leaf: CompanyPeriodBuilder,
    ) -> None:
        self._labels = labels
        self._graph = graph
        self._readers = dict(readers)
        self._spans = spans
        self._leaf = leaf

    def build_resolver(
        self, full: NamePairs, short: NamePairs, former: NamePairs
    ) -> tuple[EntityResolver, set[str]]:
        """
        Purpose:
            The resolver over A-share names and the entity map, and the names to skip.

        Contract:
            Input:
                full, short, former: Iterable[tuple[str, str]]  -- (ts_code, name)
            Output:
                (EntityResolver, set[str])  -- names of kinds in NOT_NODES
            Raises:
                (none)
        """
        emap = self._graph.read("entity_map")
        if emap.empty:
            return EntityResolver(full, short, former_names=former), set()
        asked = emap[emap["canonical"].notna()]
        aliases = dict(zip(asked["name"], asked["entity_id"], strict=True))
        members = asked.loc[asked["is_member"].fillna(False).astype(bool), "name"]
        skip = set(asked.loc[asked["kind"].isin(NOT_NODES), "name"])
        return EntityResolver(full, short, aliases, set(members), former), skip

    def build(
        self, full: NamePairs, short: NamePairs, former: NamePairs, as_of: str | None = None
    ) -> dict[str, int]:
        """
        Purpose:
            Rebuild company_edge, edge_span and company_period.

        Contract:
            Input:
                full, short, former: Iterable[tuple[str, str]]  -- A-share names
                as_of: str | None  -- YYYYMMDD; spans as known on that date
            Output:
                dict[str, int]  -- rows written per table
            Raises:
                SchemaError  -- bad as_of
                LakeError    -- a write failed
        """
        resolver, skip = self.build_resolver(full, short, former)
        edges_of = CompanyEdgeBuilder(resolver, self._readers, skip)
        parts = []
        for label_set in self._readers:
            edges = edges_of.build_edges(label_set, self._labels.read(label_set))
            logger.info("graph edges %s: %d", label_set, len(edges))
            parts.append(edges)
        edges = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        edges = edges.reindex(columns=EDGE_COLUMNS)
        edges = edges.sort_values(["src", "dst", "known_on", "doc_key"], kind="stable")
        edges = edges.reset_index(drop=True)
        spans = self._spans.build_spans(edges, as_of=as_of)
        leaf = self._leaf.build_leaf()
        self._graph.write("company_edge", edges)
        self._graph.write("edge_span", spans)
        self._graph.write("company_period", leaf)
        return {"company_edge": len(edges), "edge_span": len(spans), "company_period": len(leaf)}
