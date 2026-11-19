"""node_edge: supplier segment -> buyer segment per year, evidenced vs prior (plan 28 ph4d)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy

NODE_EDGE_COLUMNS = [
    "period",
    "src_node",
    "dst_node",
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
    "taxonomy_version",
]
# company edge relation -> node edge kind (src supplies or invests in dst)
KINDS = {"customer": "sales", "supplier": "sales", "holds": "invests", "invests_in": "invests"}
# prior relation -> True when the object supplies the subject (README of config/industry_chain)
SUPPLY_RELATIONS = {
    "upstream_of": False,
    "component_of": False,
    "used_in": False,
    "uses_material": True,
}
SHARE_PREFIX = "a:"  # entity ids of A-share companies; only they have node members
TOP_COMPANIES = 5  # companies named per node edge side, by weight
ANNUAL, INTERIM = "1231", "0630"


class NodeEdgeBuilder:
    """
    Purpose:
        Aggregate company edges into `node_edge` (plan 28 ph4d, D-161): one row per year
        (period YYYY1231), supplier segment, buyer segment and kind ("sales": customer /
        supplier rows, src sells to dst; "invests": holds / invests_in, src invests in dst).
        Evidence: company_edge rows between two A-share companies (other counterparties have
        no node members), one observation per (year, src, dst, kind) however many documents
        state it; the year is the edge period's year, or the known_on year when the period
        lies after known_on (forecast periods). Each side is spread over its company's segment
        weights from `node_member` (rows with a segment; annual period of that year, else the
        interim of that year, else the latest earlier period, else the earliest later one);
        weight = sum over company pairs of w_src * w_dst. Prior: taxonomy edges of
        SUPPLY_RELATIONS mapped to the segments of both ends (uses_material reversed; ends
        without a segment and same-segment pairs dropped). Every prior pair gets a "sales"
        row in every year with members (source "prior", weight 0) unless evidence exists ("both");
        evidence alone is "evidenced". known_on / last_known_on are the first and last
        known_on of the evidence (None for prior-only rows). With `as_of`, edges and members
        known after it are dropped (point in time). No LLM call.

    Contract:
        Input:
            taxonomy: ProductTaxonomy  -- the version node_member was built with
            dates:    DateCodec
        Output:
            instance; `build_node_edges(edges, members, as_of=None) -> DataFrame`
            (NODE_EDGE_COLUMNS, sorted by period, kind, src_node, dst_node)
        Raises:
            (none at construction)

    Used by:
        cli.DocumentCommands  -- `build-graph` writes node_edge

    Test cases:
        TC-NEB-001  sales and invests rows from A-share pairs; a pair stated twice counts once
                    in weight and twice in n_obs; weights split over segments; partner and
                    non-A counterparties dropped; companies and known_on range
        TC-NEB-002  member period choice: annual of the year, else interim, else latest
                    earlier; an edge period after its known_on uses the known_on year
        TC-NEB-003  prior pairs: evidenced -> "both" with relations; not evidenced -> "prior"
                    weight 0 in every year with members; uses_material reversed; same-segment and
                    segmentless ends dropped
        TC-NEB-004  as_of drops later edges and members; bad as_of raises SchemaError; empty
                    inputs give an empty frame with NODE_EDGE_COLUMNS
    """

    def __init__(self, taxonomy: ProductTaxonomy, dates: DateCodec) -> None:
        self._taxonomy = taxonomy
        self._dates = dates

    def build_node_edges(
        self, edges: pd.DataFrame, members: pd.DataFrame, as_of: str | None = None
    ) -> pd.DataFrame:
        """
        Purpose:
            The node_edge table from company_edge and node_member.

        Contract:
            Input:
                edges:   pd.DataFrame  -- company_edge (src, dst, relation, period, known_on)
                members: pd.DataFrame  -- node_member (ts_code, period, known_on, segment,
                                          weight)
                as_of:   str | None    -- YYYYMMDD
            Output:
                pd.DataFrame  -- NODE_EDGE_COLUMNS
            Raises:
                SchemaError  -- as_of not YYYYMMDD
        """
        if as_of is not None:
            try:
                self._dates.validate(as_of)
            except ValueError as exc:
                raise SchemaError(f"as_of {as_of!r} is not YYYYMMDD") from exc
        weights = self._build_weights(members, as_of)
        pairs = self._build_pairs(edges, as_of)
        evidenced = self._build_evidenced(pairs, weights)
        years = sorted(set(weights["period"].str[:4]))  # prior rows: years with members
        frame = self._add_prior(evidenced, [f"{y}{ANNUAL}" for y in years])
        frame["taxonomy_version"] = self._taxonomy.version
        frame = frame.reindex(columns=NODE_EDGE_COLUMNS)
        frame = frame.sort_values(["period", "kind", "src_node", "dst_node"], kind="stable")
        return frame.reset_index(drop=True)

    @staticmethod
    def _build_weights(members: pd.DataFrame, as_of: str | None) -> pd.DataFrame:
        cols = ["ts_code", "period", "segment", "weight"]
        if members.empty:
            return pd.DataFrame(columns=cols)
        frame = members[members["segment"].notna() & members["weight"].notna()]
        frame = frame[frame["period"].str[4:].isin((ANNUAL, INTERIM))]
        if as_of is not None:
            frame = frame[frame["known_on"].notna() & (frame["known_on"] <= as_of)]
        grouped = frame.groupby(["ts_code", "period", "segment"], as_index=False).agg(
            weight=("weight", "sum")
        )
        return grouped.reindex(columns=cols)

    @staticmethod
    def _build_pairs(edges: pd.DataFrame, as_of: str | None) -> pd.DataFrame:
        cols = ["year", "src", "dst", "kind", "n_obs", "known_on", "last_known_on"]
        if edges.empty:
            return pd.DataFrame(columns=cols)
        frame = edges[
            edges["relation"].isin(list(KINDS))
            & edges["src"].str.startswith(SHARE_PREFIX)
            & edges["dst"].str.startswith(SHARE_PREFIX)
            & edges["known_on"].notna()
            & (edges["src"] != edges["dst"])
        ].copy()
        if as_of is not None:
            frame = frame[frame["known_on"] <= as_of]
        if frame.empty:
            return pd.DataFrame(columns=cols)
        period = frame["period"].fillna(frame["known_on"])
        late = period > frame["known_on"]
        frame["year"] = period.where(~late, frame["known_on"]).str[:4]
        frame["kind"] = frame["relation"].map(KINDS)
        frame["src"] = frame["src"].str[len(SHARE_PREFIX) :]
        frame["dst"] = frame["dst"].str[len(SHARE_PREFIX) :]
        grouped = frame.groupby(["year", "src", "dst", "kind"], as_index=False).agg(
            n_obs=("known_on", "size"),
            known_on=("known_on", "min"),
            last_known_on=("known_on", "max"),
        )
        return grouped.reindex(columns=cols)

    @staticmethod
    def _find_periods(weights: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
        """(ts_code, year) -> the member period used for that company in that year."""
        available: dict[str, list[str]] = {}
        for code, period in sorted(set(zip(weights["ts_code"], weights["period"], strict=True))):
            available.setdefault(code, []).append(period)
        rows: list[dict[str, Any]] = []
        for code, year in sorted(set(zip(keys["ts_code"], keys["year"], strict=True))):
            periods = available.get(code)
            if not periods:
                continue
            choice = next(
                (p for p in (f"{year}{ANNUAL}", f"{year}{INTERIM}") if p in periods), None
            )
            if choice is None:
                earlier = [p for p in periods if p[:4] < year]
                choice = earlier[-1] if earlier else periods[0]
            rows.append({"ts_code": code, "year": year, "period": choice})
        return pd.DataFrame(rows, columns=["ts_code", "year", "period"])

    def _build_evidenced(self, pairs: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
        cols = ["period", "src_node", "dst_node", "kind", "weight", "n_pairs", "n_obs",
                "src_companies", "dst_companies", "known_on", "last_known_on"]  # fmt: skip
        if pairs.empty or weights.empty:
            return pd.DataFrame(columns=cols)
        keys = pd.concat([
            pairs[["src", "year"]].rename(columns={"src": "ts_code"}),
            pairs[["dst", "year"]].rename(columns={"dst": "ts_code"}),
        ])  # fmt: skip
        chosen = self._find_periods(weights, keys).merge(weights, on=["ts_code", "period"])
        side = chosen[["ts_code", "year", "segment", "weight"]]
        frame = pairs.merge(
            side.rename(columns={"ts_code": "src", "segment": "src_node", "weight": "w_src"}),
            on=["src", "year"],
        ).merge(
            side.rename(columns={"ts_code": "dst", "segment": "dst_node", "weight": "w_dst"}),
            on=["dst", "year"],
        )
        if frame.empty:
            return pd.DataFrame(columns=cols)
        frame["weight"] = frame["w_src"] * frame["w_dst"]
        frame["period"] = frame["year"] + ANNUAL
        rows = [
            self._build_row(key, group)
            for key, group in frame.groupby(["period", "src_node", "dst_node", "kind"], sort=True)
        ]
        return pd.DataFrame(rows, columns=cols)

    @staticmethod
    def _build_row(key: Any, group: pd.DataFrame) -> dict[str, Any]:
        period, src_node, dst_node, kind = key
        return {
            "period": period, "src_node": src_node, "dst_node": dst_node, "kind": kind,
            "weight": float(group["weight"].sum()),
            "n_pairs": len(group[["src", "dst"]].drop_duplicates()),
            "n_obs": int(group["n_obs"].sum()),
            "src_companies": NodeEdgeBuilder._list_top(group, "src"),
            "dst_companies": NodeEdgeBuilder._list_top(group, "dst"),
            "known_on": str(group["known_on"].min()),
            "last_known_on": str(group["last_known_on"].max()),
        }  # fmt: skip

    @staticmethod
    def _list_top(group: pd.DataFrame, code: str) -> str:
        totals = group["weight"].groupby(group[code]).sum()
        totals = totals.sort_index().sort_values(ascending=False, kind="stable")
        return ";".join(str(c) for c in totals.index[:TOP_COMPANIES])

    def _list_prior(self) -> dict[tuple[str, str], str]:
        """(supplier segment, buyer segment) -> ';'-joined prior relations."""
        found: dict[tuple[str, str], list[str]] = {}
        for subject, relation, obj in self._taxonomy.list_edges(tuple(SUPPLY_RELATIONS)):
            ends = (self._taxonomy.get_segment_id(subject), self._taxonomy.get_segment_id(obj))
            supplier, buyer = (ends[1], ends[0]) if SUPPLY_RELATIONS[relation] else ends
            if supplier is None or buyer is None or supplier == buyer:
                continue
            relations = found.setdefault((supplier, buyer), [])
            if relation not in relations:
                relations.append(relation)
        return {pair: ";".join(sorted(rels)) for pair, rels in sorted(found.items())}

    def _add_prior(self, evidenced: pd.DataFrame, periods: list[str]) -> pd.DataFrame:
        prior = self._list_prior()
        frame = evidenced.copy()
        relations = [
            prior.get((s, d)) if k == "sales" else None
            for s, d, k in zip(frame["src_node"], frame["dst_node"], frame["kind"], strict=True)
        ]
        frame["prior_relations"] = relations
        frame["source"] = ["both" if r else "evidenced" for r in relations]
        seen = set(zip(frame["period"], frame["src_node"], frame["dst_node"], frame["kind"],
                       strict=True))  # fmt: skip
        rows = [
            {"period": period, "src_node": s, "dst_node": d, "kind": "sales", "source": "prior",
             "prior_relations": rels, "weight": 0.0, "n_pairs": 0, "n_obs": 0}
            for period in periods
            for (s, d), rels in prior.items()
            if (period, s, d, "sales") not in seen
        ]  # fmt: skip
        if not rows:
            return frame
        if frame.empty:
            return pd.DataFrame(rows)
        return pd.concat([frame, pd.DataFrame(rows)], ignore_index=True)
