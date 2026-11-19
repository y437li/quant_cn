"""Rule hits and ranking of the daily opportunity list (plan 21 ph4)."""

from __future__ import annotations

import pandas as pd

from quant_cn.core.opportunity_settings import RULES, OpportunitySettings

METRIC_COLUMNS = [
    "pct", "avoid", "retail_leaving", "lg_weeks_pos_4w", "np_yoy", "np_qoq",
    "val_value", "val_median", "fit",
]  # fmt: skip
LIST_COLUMNS = ["rank", "status", "is_new", "n_hit", "rules_hit", "missing"]
HIT_COLUMNS = [f"hit_{rule}" for rule in RULES]
LISTED, NEAR = "listed", "near"


class OpportunityRules:
    """
    Purpose:
        Evaluate the opportunity rules (OpportunitySettings, RULES) on a metrics frame and
        rank the list: `listed` names hit every rule (top_n, lowest gauge pct first);
        `near` names miss exactly one rule that is not `required` (near_n, same order).
        Unknown metrics (NaN) never count as a hit; a name with `avoid` is dropped before
        anything else (D-155).

    Contract:
        Input:
            settings: OpportunitySettings
        Output:
            instance; `compute_hits(metrics) -> DataFrame[bool]` (index of metrics, columns
            RULES); `build_list(metrics, previous) -> DataFrame` (index ts_code; the metrics
            columns plus HIT_COLUMNS (hit_<rule>) and LIST_COLUMNS: rank 1.., status
            listed | near, is_new (not in `previous`), n_hit, rules_hit and missing as
            comma-joined rule names)
        Raises:
            KeyError  -- metrics without METRIC_COLUMNS

    Used by:
        portfolio.OpportunityScreen  -- rules and ranking
        cli.GaugeCommands            -- wires it

    Test cases:
        TC-OPR-001  each rule fires at its boundary and not one tick inside it (inflow weeks,
                    np_yoy, np_qoq, valuation below the median, fit, retail_leaving)
        TC-OPR-002  avoid names are never listed nor near; a near-miss never misses a
                    required rule; NaN metrics do not hit
        TC-OPR-003  ranking by pct, top_n / near_n caps, is_new against the previous list
    """

    def __init__(self, settings: OpportunitySettings) -> None:
        self._settings = settings

    def compute_hits(self, metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Boolean hit of every rule per name (see the class contract).

        Contract:
            Input:
                metrics: DataFrame  -- METRIC_COLUMNS, index ts_code
            Output:
                DataFrame  -- columns RULES, bool, NaN metrics -> False
            Raises:
                KeyError  -- a metric column missing
        """
        s = self._settings
        value, median = metrics["val_value"], metrics["val_median"]
        hits = {
            "retail_leaving": metrics["retail_leaving"].fillna(False).astype(bool),
            "inflow": metrics["lg_weeks_pos_4w"] >= s.inflow_weeks,
            "earnings": (metrics["np_yoy"] >= s.np_yoy_min) & (metrics["np_qoq"] >= s.np_qoq_min),
            "valuation": (value > 0) & (value < median),
            "fit": metrics["fit"] == 1.0,
        }
        return pd.DataFrame(hits, index=metrics.index)[list(RULES)].astype(bool)

    def build_list(self, metrics: pd.DataFrame, previous: set[str]) -> pd.DataFrame:
        """
        Purpose:
            The ranked list: listed names, then near-misses (see the class contract).

        Contract:
            Input:
                metrics: DataFrame  -- METRIC_COLUMNS, index ts_code
                previous: set[str]  -- ts_codes on the previous session's list (listed or near)
            Output:
                DataFrame  -- index ts_code, metrics + HIT_COLUMNS + LIST_COLUMNS; empty with those
                              columns when nothing qualifies
            Raises:
                KeyError  -- a metric column missing
        """
        hits = self.compute_hits(metrics).add_prefix("hit_")
        frame = metrics.join(hits)
        frame = frame[~frame["avoid"].fillna(False).astype(bool)]
        n_hit = frame[HIT_COLUMNS].sum(axis=1)
        required = frame[[f"hit_{r}" for r in self._settings.required]].all(axis=1)
        listed = frame[n_hit == len(RULES)].sort_values("pct").head(self._settings.top_n)
        near = frame[(n_hit == len(RULES) - 1) & required]
        near = near.sort_values("pct").head(self._settings.near_n)
        out = pd.concat([listed.assign(status=LISTED), near.assign(status=NEAR)])
        out["rank"] = range(1, len(out) + 1)
        out["is_new"] = ~out.index.isin(list(previous))
        flags = out[HIT_COLUMNS].to_numpy(bool)
        out["n_hit"] = flags.sum(axis=1).astype(int)
        out["rules_hit"] = [
            ",".join(r for r, f in zip(RULES, row, strict=True) if f) for row in flags
        ]
        out["missing"] = [
            ",".join(r for r, f in zip(RULES, row, strict=True) if not f) for row in flags
        ]
        return out[[*metrics.columns, *HIT_COLUMNS, *LIST_COLUMNS]]
