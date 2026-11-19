"""Point-in-time questions to the plan 28 graph: a company as known on a date, its timeline."""

from __future__ import annotations

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.industry_graph.edge_span_builder import EdgeSpanBuilder
from quant_cn.lake.graph_store import GraphStore

NEIGHBOUR_COLUMNS = [
    "direction",
    "other_node",
    "kind",
    "source",
    "prior_relations",
    "weight",
    "n_pairs",
    "n_obs",
    "src_companies",
    "dst_companies",
    "known_on",
    "last_known_on",
]
MEMBER_COLUMNS = ["ts_code", "sales", "weight", "items", "known_on"]
HISTORY_COLUMNS = ["period", "n_members", "sales", "n_upstream", "n_downstream", "n_invests"]
ANNUAL = "1231"

TIMELINE_COLUMNS = [
    "known_on",
    "kind",
    "label_set",
    "period",
    "doc_key",
    "counterparty",
    "relation",
    "stage",
    "quote",
]


class GraphQuery:
    """
    Purpose:
        Answer plan 28's point-in-time questions (D-161) from the GraphStore tables, never
        using a fact before it was public:
        - `find_leaf(ts_code, as_of)`: the company as known on as_of: for each label set the
          rows of its latest period among rows with known_on <= as_of (FY2025 annual labels
          are absent before the report's filing date);
        - `list_spans(ts_code, as_of)`: the edge spans touching the company, rebuilt from the
          company_edge observations known on as_of (EdgeSpanBuilder);
        - `list_timeline(ts_code, start, end)`: one list ordered by known_on mixing report
          snapshots (company_period rows, kind "label") and edge observations the company
          stated (company_edge rows, kind "edge"), known_on in [start, end];
        - industry nodes (plan 28 ph4d; segments of node_member / node_edge, tables as built,
          rebuild with `build-graph --as-of` for a past date): `list_node_members(node_id,
          period)` (companies of the segment by sales), `list_node_neighbours(node_id,
          period, kind)` (upstream rows: the node buys from other_node; downstream: sells to
          it; by weight), `list_node_history(node_id)` (per annual period: members, sales,
          evidenced up / downstream and invest edges) and `list_node_lineage(node_id)` (what
          taxonomy versions did to the node).

    Contract:
        Input:
            graph: GraphStore; spans: EdgeSpanBuilder; date_codec: DateCodec
        Output:
            instance; `find_leaf`, `list_spans`, `list_timeline`, `list_node_members`,
            `list_node_neighbours`, `list_node_history`, `list_node_lineage` (DataFrames)
        Raises:
            (none at construction)

    Used by:
        (none yet; plan 28 ph5 app)

    Test cases:
        TC-GQ-001  find_leaf keeps the latest period per label set among rows known on
                   as_of; a report filed after as_of is absent
        TC-GQ-002  list_spans as of a date ignores later observations
        TC-GQ-003  list_timeline orders labels and edges by known_on within [start, end];
                   columns are TIMELINE_COLUMNS; a bad date raises SchemaError
        TC-GQ-004  list_node_members sums a company's lines in the segment for the period,
                   sorted by sales; unknown node gives an empty frame with MEMBER_COLUMNS
        TC-GQ-005  list_node_neighbours: upstream and downstream rows by weight, prior rows
                   included, other kinds excluded; bad period raises SchemaError
        TC-GQ-006  list_node_history counts members, sales and evidenced edges per annual
                   period; list_node_lineage keeps rows naming the node on either end
    """

    def __init__(self, graph: GraphStore, spans: EdgeSpanBuilder, date_codec: DateCodec) -> None:
        self._graph = graph
        self._spans = spans
        self._dates = date_codec

    def find_leaf(self, ts_code: str, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            The company's label rows as known on a date, latest period per label set.

        Contract:
            Input:
                ts_code: str; as_of: str (YYYYMMDD)
            Output:
                pd.DataFrame  -- company_period columns
            Raises:
                SchemaError  -- bad as_of
        """
        self._check_date(as_of)
        leaf = self._graph.read("company_period")
        if leaf.empty:
            return leaf
        rows = leaf[(leaf["ts_code"] == ts_code) & (leaf["known_on"] <= as_of)]
        latest = rows.groupby("label_set")["period"].transform("max")
        return rows[rows["period"] == latest].reset_index(drop=True)

    def list_spans(self, ts_code: str, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            The spans of the company's edges as known on a date.

        Contract:
            Input:
                ts_code: str; as_of: str (YYYYMMDD)
            Output:
                pd.DataFrame  -- SPAN_COLUMNS of EdgeSpanBuilder
            Raises:
                SchemaError  -- bad as_of
        """
        self._check_date(as_of)
        node = f"a:{ts_code}"
        edges = self._graph.read("company_edge")
        if not edges.empty:
            edges = edges[(edges["src"] == node) | (edges["dst"] == node)]
        return self._spans.build_spans(edges, as_of=as_of)

    def list_timeline(self, ts_code: str, start: str, end: str) -> pd.DataFrame:
        """
        Purpose:
            Labels and edge observations of the company, ordered by known_on.

        Contract:
            Input:
                ts_code: str; start, end: str (YYYYMMDD, inclusive)
            Output:
                pd.DataFrame  -- TIMELINE_COLUMNS
            Raises:
                SchemaError  -- bad start or end
        """
        self._check_date(start)
        self._check_date(end)
        leaf = self._graph.read("company_period")
        edges = self._graph.read("company_edge")
        parts = []
        if not leaf.empty:
            labels = leaf[leaf["ts_code"] == ts_code].assign(kind="label")
            parts.append(labels.reindex(columns=TIMELINE_COLUMNS))
        if not edges.empty:
            stated = edges[edges["ts_code"] == ts_code].assign(kind="edge")
            parts.append(stated.reindex(columns=TIMELINE_COLUMNS))
        if not parts:
            return pd.DataFrame(columns=TIMELINE_COLUMNS)
        line = pd.concat(parts, ignore_index=True)
        line = line[(line["known_on"] >= start) & (line["known_on"] <= end)]
        order = ["known_on", "kind", "label_set", "doc_key"]
        return line.sort_values(order, kind="stable").reset_index(drop=True)

    def list_node_members(self, node_id: str, period: str) -> pd.DataFrame:
        """
        Purpose:
            The companies of a segment in a period, by the sales of their lines in it.

        Contract:
            Input:
                node_id: str (segment id); period: str (YYYYMMDD, e.g. 20251231)
            Output:
                pd.DataFrame  -- MEMBER_COLUMNS, sales descending
            Raises:
                SchemaError  -- bad period
        """
        self._check_date(period)
        members = self._graph.read("node_member")
        if members.empty:
            return pd.DataFrame(columns=MEMBER_COLUMNS)
        rows = members[(members["segment"] == node_id) & (members["period"] == period)]
        if rows.empty:
            return pd.DataFrame(columns=MEMBER_COLUMNS)
        grouped = rows.groupby("ts_code", as_index=False).agg(
            sales=("sales", "sum"),
            weight=("weight", "sum"),
            items=("item", lambda s: "；".join(str(v) for v in s)),
            known_on=("known_on", "min"),
        )
        grouped = grouped.sort_values(["sales", "ts_code"], ascending=[False, True])
        return grouped.reindex(columns=MEMBER_COLUMNS).reset_index(drop=True)

    def list_node_neighbours(self, node_id: str, period: str, kind: str = "sales") -> pd.DataFrame:
        """
        Purpose:
            The segments a node buys from (upstream) and sells or invests to (downstream).

        Contract:
            Input:
                node_id: str; period: str (YYYYMMDD); kind: str ("sales" | "invests")
            Output:
                pd.DataFrame  -- NEIGHBOUR_COLUMNS; upstream first, weight descending
            Raises:
                SchemaError  -- bad period
        """
        self._check_date(period)
        edges = self._graph.read("node_edge")
        if edges.empty:
            return pd.DataFrame(columns=NEIGHBOUR_COLUMNS)
        rows = edges[(edges["period"] == period) & (edges["kind"] == kind)]
        up = rows[rows["dst_node"] == node_id].assign(direction="upstream")
        up = up.assign(other_node=up["src_node"])
        down = rows[rows["src_node"] == node_id].assign(direction="downstream")
        down = down.assign(other_node=down["dst_node"])
        both = pd.concat([up, down], ignore_index=True).reindex(columns=NEIGHBOUR_COLUMNS)
        order = ["direction", "weight", "other_node"]
        both = both.sort_values(order, ascending=[False, False, True], kind="stable")
        return both.reset_index(drop=True)

    def list_node_history(self, node_id: str) -> pd.DataFrame:
        """
        Purpose:
            A node's size and links per annual period.

        Contract:
            Input:
                node_id: str
            Output:
                pd.DataFrame  -- HISTORY_COLUMNS, period ascending; edges counted when
                                 evidenced (source evidenced or both)
            Raises:
                (none)
        """
        members = self._graph.read("node_member")
        edges = self._graph.read("node_edge")
        stats: dict[str, dict[str, float]] = {}
        if not members.empty:
            rows = members[(members["segment"] == node_id) & members["period"].str.endswith(ANNUAL)]
            for period, group in rows.groupby("period"):
                stats.setdefault(str(period), {})
                stats[str(period)]["n_members"] = group["ts_code"].nunique()
                stats[str(period)]["sales"] = float(group["sales"].sum())
        if not edges.empty:
            seen = edges[edges["source"].isin(["evidenced", "both"])]
            for column, mask in (
                ("n_upstream", (seen["dst_node"] == node_id) & (seen["kind"] == "sales")),
                ("n_downstream", (seen["src_node"] == node_id) & (seen["kind"] == "sales")),
                ("n_invests", (seen["src_node"] == node_id) & (seen["kind"] == "invests")),
            ):
                counts = seen[mask].groupby("period").size()
                for key, count in zip(counts.index, counts.to_numpy(), strict=True):
                    stats.setdefault(str(key), {})[column] = int(count)
        rows_out = [{"period": p, **values} for p, values in sorted(stats.items())]
        frame = pd.DataFrame(rows_out, columns=HISTORY_COLUMNS)
        count_columns = ["n_members", "n_upstream", "n_downstream", "n_invests"]
        frame[count_columns] = frame[count_columns].fillna(0).astype(int)
        return frame

    def list_node_lineage(self, node_id: str) -> pd.DataFrame:
        """
        Purpose:
            The node_lineage rows that name the node (as node, source or successor).

        Contract:
            Input:
                node_id: str
            Output:
                pd.DataFrame  -- node_lineage columns, in version order
            Raises:
                (none)
        """
        lineage = self._graph.read("node_lineage")
        if lineage.empty:
            return lineage
        hit = (
            (lineage["node_id"] == node_id)
            | (lineage["from_node"] == node_id)
            | (lineage["to_node"] == node_id)
        )
        return lineage[hit].reset_index(drop=True)

    def _check_date(self, value: str) -> None:
        try:
            self._dates.validate(value)
        except ValueError as exc:
            raise SchemaError(f"{value!r} is not YYYYMMDD") from exc
