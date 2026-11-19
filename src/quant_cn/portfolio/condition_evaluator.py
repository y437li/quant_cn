"""Evaluate structured conditions against lake signals (plan 15 ph7f)."""

from __future__ import annotations

import math
import operator
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from quant_cn.core.condition import Condition
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.fundamental_signal_reader import FundamentalSignalReader
from quant_cn.lake.margin_signal_reader import MarginSignalReader
from quant_cn.lake.shareholder_yield_reader import ShareholderYieldReader

_OPS: dict[str, Callable[[float, float], bool]] = {
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
    "==": operator.eq,
}


@dataclass(frozen=True)
class ConditionResult:
    """
    Purpose:
        One condition with the value found and its state.

    Contract:
        Input:
            label, kind, metric, op: str; value: float
            actual: float | None  -- None when the metric is unknown
            state:  str           -- "met", "unmet" or "unknown"
            required: bool        -- copied from the condition (default False)
        Output:
            frozen dataclass; `to_record()` -> dict for JSON
        Raises:
            (none)

    Used by:
        portfolio.ConditionEvaluator  -- compute_results / compute_status

    Test cases:
        TC-CE-001  each op met / unmet at its boundary; NaN or missing metric -> unknown
    """

    label: str
    kind: str
    metric: str
    op: str
    value: float
    actual: float | None
    state: str
    required: bool = False

    def to_record(self) -> dict[str, Any]:
        """
        Purpose:
            JSON-ready form.

        Contract:
            Input:
                (none)
            Output:
                dict  -- the dataclass fields
            Raises:
                (none)
        """
        return asdict(self)


class ConditionEvaluator:
    """
    Purpose:
        Gather the metrics conditions refer to (closes, 筹码结构, statements, manual series)
        and evaluate conditions to met / unmet / unknown. An entry's status: `buy` when the
        price range and every condition are met; `near` when the price is met and the others
        are not (enough) met; `wait` otherwise. An entry may ask for k of n conditions.
        Unknown is never treated as met. A low RetailGauge condition (`retail_gauge` with
        `<=` or `<`) is met only when the reading is also `retail_leaving` (3 checkpoints in a
        row, D-167, chips `gauge_leaving` = 1.0).

    Contract:
        Input:
            chips:        ChipStructureReader
            fundamentals: FundamentalSignalReader
            heat:         Mapping[str, float]  -- market-wide heat metrics (e.g. bank_etf_z from
                                                  etf_proxy.json, ph7g); same value for every code
            margin:       MarginSignalReader | None  -- kind `margin` metrics (ph7m)
            capital:      ShareholderYieldReader | None  -- kind `capital` metrics (plan 23)
        Output:
            instance; `read_metrics`, `compute_results`, `compute_status`
        Raises:
            (none at construction)

    Used by:
        portfolio.PositionReviewer  -- position conditions and chip rows
        portfolio.WatchlistBuilder  -- entry conditions
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-CE-001  each op met / unmet at its boundary; NaN or missing metric -> unknown
        TC-CE-002  compute_status: buy / near / wait; unknown blocks buy
        TC-CE-005  a required condition unmet blocks buy; `needed` counts only the others
        TC-CE-006  margin metrics joined when a margin reader is given
        TC-CE-007  capital metrics joined when a shareholder-yield reader is given
        TC-CE-003  read_metrics joins closes, chips, statements and the series asked for
        TC-CE-004  heat metrics are copied to every code; a missing heat metric stays unknown
        TC-CE-008  retail_gauge <= 0.3 is met only with gauge_leaving 1.0; >= is unaffected
    """

    def __init__(
        self,
        chips: ChipStructureReader,
        fundamentals: FundamentalSignalReader,
        heat: Mapping[str, float] | None = None,
        margin: MarginSignalReader | None = None,
        capital: ShareholderYieldReader | None = None,
    ) -> None:
        self._chips = chips
        self._fundamentals = fundamentals
        self._heat = dict(heat or {})
        self._margin = margin
        self._capital = capital

    def read_metrics(
        self, closes: Mapping[str, float], as_of: str, series: Sequence[str] = ()
    ) -> pd.DataFrame:
        """
        Purpose:
            One row of metrics per code, as known on `as_of`.

        Contract:
            Input:
                closes: Mapping[str, float]  -- ts_code -> latest close (price conditions)
                as_of:  str                  -- YYYYMMDD
                series: Sequence[str]        -- manual-series ids used by any condition
            Output:
                DataFrame  -- index ts_code; columns close, ChipStructureReader COLUMNS,
                              FundamentalSignalReader COLUMNS, "series:<id>" per series, heat
                              metrics
            Raises:
                LakeError  -- a reader query fails
        """
        codes = list(closes)
        frame = pd.DataFrame({"close": pd.Series(closes, dtype=float)}, index=codes)
        frame = frame.join(self._chips.read(codes, as_of)).join(
            self._fundamentals.read(codes, as_of)
        )
        for key, value in self._fundamentals.read_series(list(series), as_of).items():
            frame[key] = value
        for key, value in self._heat.items():
            frame[key] = value
        if self._margin is not None:
            frame = frame.join(self._margin.read(codes, as_of))
        if self._capital is not None:
            frame = frame.join(self._capital.read_metrics(codes, as_of))
        return frame

    def compute_results(
        self, conditions: Sequence[Condition], metrics: Mapping[Any, Any]
    ) -> list[ConditionResult]:
        """
        Purpose:
            Evaluate each condition against one code's metrics.

        Contract:
            Input:
                conditions: Sequence[Condition]
                metrics:    Mapping[Any, Any]  -- one row of read_metrics (or a dict)
            Output:
                list[ConditionResult]  -- same order; unknown when the value is missing / NaN
            Raises:
                (none)
        """
        out = []
        for c in conditions:
            raw = metrics.get(c.metric_key)
            actual = float(raw) if isinstance(raw, int | float) and not math.isnan(raw) else None
            if actual is None:
                state = "unknown"
            else:
                state = "met" if _OPS[c.op](actual, c.value) else "unmet"
            if state == "met" and self._is_streak_missing(c, metrics):
                state = "unmet"
            out.append(
                ConditionResult(c.label, c.kind, c.metric, c.op, c.value, actual, state, c.required)
            )
        return out

    @staticmethod
    def _is_streak_missing(condition: Condition, metrics: Mapping[Any, Any]) -> bool:
        """A low-gauge condition (`retail_gauge <= / <`) also needs D-167 retail_leaving."""
        if condition.metric_key != "retail_gauge" or condition.op not in ("<=", "<"):
            return False
        leaving = metrics.get("gauge_leaving")
        return not (isinstance(leaving, int | float) and leaving == 1.0)

    @staticmethod
    def compute_status(
        results: Sequence[ConditionResult], price_met: bool, needed: int | None = None
    ) -> str:
        """
        Purpose:
            One status for an entry from its price check and condition results.

        Contract:
            Input:
                results:   Sequence[ConditionResult]
                price_met: bool        -- the price is inside (or below) the buy range
                needed:    int | None  -- of the conditions not marked required, how many must
                                          be met; None = all of them
            Output:
                str  -- "buy" when every required condition and `needed` of the others are
                        met; "near" when the price is met but not the conditions; "wait"
            Raises:
                (none)
        """
        if not price_met:
            return "wait"
        if any(r.required and r.state != "met" for r in results):
            return "near"
        rest = [r for r in results if not r.required]
        met = sum(r.state == "met" for r in rest)
        return "buy" if met >= (len(rest) if needed is None else needed) else "near"
