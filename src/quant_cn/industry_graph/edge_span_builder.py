"""The life cycle of each company edge, built from its observations (plan 28 ph4, D-161)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError

SPAN_COLUMNS = [
    "src",
    "dst",
    "kind",
    "first_seen",
    "last_seen",
    "n_obs",
    "n_docs",
    "sources",
    "stage_path",
    "last_stage",
    "status",
    "shares",
    "amounts",
]
# relations of one edge kind: a customer row of the seller and a supplier row of the buyer
# state the same sales edge
KIND = {
    "customer": "sales",
    "supplier": "sales",
    "partner": "partner",
    "competitor": "competitor",
    "holds": "holds",
    "invests_in": "invests_in",
}
STAGE_ORDER = ("contact", "sample", "qualified", "designated", "small_batch", "volume")
END_STAGES = {"ended": "ended", "denied": "denied", "terminated": "ended"}
SILENT_DAYS = 548  # not seen for about six reports -> silent (not lost)


class EdgeSpanBuilder:
    """
    Purpose:
        Join the observations of one edge (src, dst, kind; customer and supplier rows are the
        same "sales" kind) into one `edge_span` row (plan 28 ph4, D-161 update 7):
        first_seen and last_seen (known_on), number of observations and documents, the label
        sets behind it, the stage path (each stage the first time it was reached, in order of
        known_on, as "stage@YYYYMMDD" joined by " > "; a stage lower than one already reached
        is not a step, nor is an end stage repeating the previous step), the last stage, the
        status and the share and amount per period and share base (JSON
        {"<period> <share_base>": value}, the largest stated; a share of 境外收入 is not mixed
        with a share of 营业收入). Status: "ended" or "denied" when the
        latest observation says so; else "silent" when last_seen is more than SILENT_DAYS
        before the as-of date; else "active". With `as_of`, only observations known on that
        date count (point in time); without it the as-of date is the latest known_on.

    Contract:
        Input:
            date_codec: DateCodec
        Output:
            instance; `build_spans(edges, as_of=None) -> DataFrame` (SPAN_COLUMNS)
        Raises:
            SchemaError  -- as_of not YYYYMMDD

    Used by:
        industry_graph.GraphQuery  -- spans as of a date
        industry_graph.GraphBuilder  -- joins edges into spans
        cli.DocumentCommands  -- `build-graph` wiring
        lake meta/runs/plan28_edges.py (plan 28 phase 4)

    Test cases:
        TC-ESB-001  a customer row and a supplier row of the same pair make one sales span;
                    stage path contact > sample > volume with dates; n_obs, n_docs, sources
        TC-ESB-002  status: ended / denied by the latest observation; silent after
                    SILENT_DAYS; active otherwise
        TC-ESB-003  as_of drops later observations; shares per period and base keep the
                    largest;
                    empty edges give an empty frame with SPAN_COLUMNS; a bad as_of raises
    """

    def __init__(self, date_codec: DateCodec) -> None:
        self._dates = date_codec

    def build_spans(self, edges: pd.DataFrame, as_of: str | None = None) -> pd.DataFrame:
        """
        Purpose:
            The spans of all edges, as known on a date.

        Contract:
            Input:
                edges: pd.DataFrame  -- CompanyEdgeBuilder output (src, dst, relation,
                                        stage, period, known_on, share, amount, label_set,
                                        doc_key; share_base optional)
                as_of: str | None    -- YYYYMMDD
            Output:
                pd.DataFrame  -- SPAN_COLUMNS, one row per (src, dst, kind)
            Raises:
                SchemaError  -- as_of not YYYYMMDD
        """
        if as_of is not None:
            try:
                self._dates.validate(as_of)
            except ValueError as exc:
                raise SchemaError(f"as_of {as_of!r} is not YYYYMMDD") from exc
        frame = edges[edges["known_on"].notna()].copy()
        if as_of is not None:
            frame = frame[frame["known_on"] <= as_of]
        if frame.empty:
            return pd.DataFrame(columns=SPAN_COLUMNS)
        frame["kind"] = frame["relation"].map(KIND)
        frame = frame.sort_values(["known_on", "doc_key"], kind="stable")
        today = as_of or str(frame["known_on"].max())
        rows = [
            self._build_span(key, group, today)
            for key, group in frame.groupby(["src", "dst", "kind"], sort=True)
        ]
        return pd.DataFrame(rows, columns=SPAN_COLUMNS)

    def _build_span(self, key: Any, group: pd.DataFrame, today: str) -> dict[str, Any]:
        src, dst, kind = key
        last = group.iloc[-1]
        last_seen = str(last["known_on"])
        end = END_STAGES.get(str(last["stage"]))
        if end is not None:
            status = end
        elif (self._dates.to_date(today) - self._dates.to_date(last_seen)).days > SILENT_DAYS:
            status = "silent"
        else:
            status = "active"
        return {
            "src": src,
            "dst": dst,
            "kind": kind,
            "first_seen": str(group["known_on"].iloc[0]),
            "last_seen": last_seen,
            "n_obs": len(group),
            "n_docs": group["doc_key"].nunique(),
            "sources": ",".join(sorted(set(group["label_set"]))),
            "stage_path": self._build_path(group),
            "last_stage": last["stage"] if pd.notna(last["stage"]) else None,
            "status": status,
            "shares": self._build_by_period(group, "share"),
            "amounts": self._build_by_period(group, "amount"),
        }

    @staticmethod
    def _build_path(group: pd.DataFrame) -> str:
        steps: list[str] = []
        reached = -1
        for stage, day in zip(group["stage"], group["known_on"], strict=True):
            if stage in STAGE_ORDER and STAGE_ORDER.index(stage) > reached:
                reached = STAGE_ORDER.index(stage)
                steps.append(f"{stage}@{day}")
            elif stage in END_STAGES and not (steps and steps[-1].startswith(f"{stage}@")):
                steps.append(f"{stage}@{day}")
        return " > ".join(steps)

    @staticmethod
    def _build_by_period(group: pd.DataFrame, column: str) -> str | None:
        stated = group[group[column].notna() & group["period"].notna()]
        if stated.empty:
            return None
        base = stated["share_base"].fillna("") if "share_base" in stated else ""
        key = (stated["period"].astype(str) + " " + base).str.strip()
        best = stated[column].groupby(key).max().sort_index()
        return json.dumps({str(k): float(v) for k, v in best.items()}, ensure_ascii=False)
