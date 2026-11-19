"""A structured buy / falsifier condition on a watchlist entry or a position note (plan 15 ph7f)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

Kind = Literal[
    "price", "flow", "chip", "retail", "heat", "statement", "series", "manual", "margin", "capital"
]
Op = Literal["<=", ">=", "<", ">", "=="]

# Metrics each kind may use; `series` takes any manual-series id. Units: flows in 亿 CNY,
# changes and ratios as fractions unless the name says pp (percentage points) or pct (percent).
METRICS: dict[str, frozenset[str]] = {
    "price": frozenset({"close"}),
    "flow": frozenset(
        {"lg_weeks_pos_4w", "lg_net_4w", "lg_net_20d", "sm_weeks_neg_4w", "sm_net_4w"}
    ),
    "chip": frozenset(
        {
            "winner_rate",
            "inst_top10_dq_pp",
            "north_chg_pp",
            "margin_chg_60d",
            "unlock_6m_pct",
            "insider_sell_6m_pct",
            "holder_sell_90d_pct",
        }
    ),
    "retail": frozenset({"retail_gauge", "holders_chg_q"}),
    "heat": frozenset({"bank_etf_z", "dividend_etf_z"}),
    "statement": frozenset({"gm_q", "dedt_yoy_q", "ocf_to_np"}),
    "manual": frozenset({"flag"}),
    "margin": frozenset({"rz_chg_20d", "rz_net_20d_pct", "rq_pct_float", "rq_max_ratio"}),
    "capital": frozenset(
        {"shareholder_yield", "buyback_yield", "buyback_plan_pct", "buyback_done_pct"}
    ),
}


class Condition(BaseModel):
    """
    Purpose:
        One condition the user wants met before acting (buy) or that would break a thesis:
        `<metric> <op> <value>`, e.g. `lg_weeks_pos_4w >= 3`. A `manual` condition is a flag the
        user sets by hand (`metric: flag, op: "==", value: 1` when met, 0 when not).

    Contract:
        Input:
            label:  str    -- what the user reads, e.g. "大单近 4 周至少 3 周净流入"
            kind:   Kind   -- price / flow / chip / retail / heat / statement / series / manual /
                              margin (plan 15 ph7m) / capital (plan 23 ph5)
            metric: str    -- one of METRICS[kind]; for `series` a manual-series id
            op:     Op     -- <=, >=, <, >, ==
            value:  float  -- threshold in the metric's unit
            window: str    -- free text, e.g. "4w", "Q4 report"; "" allowed
            required: bool -- must be met whatever `conditions_needed` says (default False)
        Output:
            frozen pydantic model; `metric_key` -> the key the evaluator looks up
        Raises:
            pydantic.ValidationError  -- unknown kind or op, metric not allowed for the kind,
                                         extra keys

    Used by:
        core.WatchlistEntry             -- `conditions`
        core.PositionNote               -- `conditions`
        portfolio.ConditionEvaluator    -- evaluates them

    Test cases:
        TC-CND-001  each kind accepts its metrics; a metric of another kind is refused
        TC-CND-002  series accepts any id and keys it as "series:<id>"; extra keys refused
        TC-CND-003  `required` defaults to False and loads from YAML
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    kind: Kind
    metric: str
    op: Op
    value: float
    window: str = ""
    required: bool = False

    @model_validator(mode="after")
    def _check_metric(self) -> Condition:
        if self.kind != "series" and self.metric not in METRICS[self.kind]:
            allowed = sorted(METRICS[self.kind])
            raise ValueError(f"{self.label}: metric {self.metric!r} not in {self.kind} {allowed}")
        return self

    @property
    def metric_key(self) -> str:
        """
        Purpose:
            The name of the value this condition compares, as the metrics frame spells it.

        Contract:
            Input:
                (none)
            Output:
                str  -- "series:<id>" for series, else the metric name
            Raises:
                (none)
        """
        return f"series:{self.metric}" if self.kind == "series" else self.metric
