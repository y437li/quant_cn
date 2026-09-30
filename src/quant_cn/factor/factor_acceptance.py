"""The FACTOR_TESTING_DESIGN §6 acceptance bar applied to a campaign's IC_TEST."""

from __future__ import annotations

import math
from collections.abc import Sequence

import pandas as pd

from quant_cn.core.frames import IC_TEST

SUBPERIOD_WINDOWS: tuple[str, ...] = ("2019-2021", "2022-2024", "2025-")
NOTES: tuple[str, ...] = ("peak_horizon", "half_life", "accumulation_ratio")


class FactorAcceptance:
    """
    Purpose:
        Criteria 1-3 of FACTOR_TESTING_DESIGN §6 per factor at one horizon, from the campaign's
        IC_TEST: (1) NW t of the full-window mean IC >= t_min (HLZ) and BHY-adjusted p <= alpha;
        (2) every sub-period mean IC has the full-window sign with sign-oriented t >= t_sub;
        (3) the bootstrap CI of ICIR excludes 0. Criterion 4 (DSR, PBO, out-of-sample) needs a
        traded variant and belongs to plan 06, so `verdict` is "pass" (criteria 1-3 met) or
        "fail"; the horizon profile (peak, half-life, accumulation ratio; D-095) is attached as
        notes, never a criterion.

    Contract:
        Input:
            horizon: int > 0      -- acceptance horizon (20)
            t_min:   float > 0    -- criterion 1 hurdle (3.0)
            alpha:   float in (0, 1)  -- criterion 1 BHY level (0.05)
            t_sub:   float > 0    -- criterion 2 hurdle (1.5)
            windows: Sequence[str]  -- sub-period window labels of IC_TEST
        Output:
            instance; `compute`
        Raises:
            ValueError  -- non-positive horizon or hurdles, alpha outside (0, 1), no windows

    Used by:
        research_space/notebooks/20260930_factor_campaign_01.ipynb  -- verdict per factor
        plan 06 ReportBuilder                                         -- planned

    Test cases:
        TC-FA-001  a factor meeting all three criteria passes; each criterion failing alone
                   fails it and names the failed criterion
        TC-FA-002  a negative factor passes on |t| with every sub-period negative; a missing
                   sub-period or missing BHY p fails; D-095 notes are copied from horizon 0
        TC-FA-003  invalid construction raises ValueError; a frame without the horizon gives
                   an empty table; a wrong frame raises SchemaError
    """

    def __init__(
        self,
        horizon: int = 20,
        t_min: float = 3.0,
        alpha: float = 0.05,
        t_sub: float = 1.5,
        windows: Sequence[str] = SUBPERIOD_WINDOWS,
    ) -> None:
        if horizon < 1 or t_min <= 0 or t_sub <= 0 or not 0 < alpha < 1 or not windows:
            raise ValueError("invalid acceptance settings")
        self._horizon = float(horizon)
        self._t_min = t_min
        self._alpha = alpha
        self._t_sub = t_sub
        self._windows = list(windows)

    def compute(self, ic_test: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            One verdict row per factor.

        Contract:
            Input:
                ic_test: DataFrame  -- IC_TEST of a campaign (campaign-adjusted)
            Output:
                DataFrame  -- one row per factor with an ic_mean full row at the horizon:
                              factor, ic_mean, t, p_bhy, t_<window> per sub-period, icir,
                              icir_ci_lo, icir_ci_hi, c1, c2, c3 (bool), verdict ("pass" /
                              "fail"), failed ("1,2" etc., "" on pass), peak_horizon,
                              half_life, accumulation_ratio (NaN when absent); sorted by t desc
            Raises:
                SchemaError  -- not IC_TEST
        """
        frame = IC_TEST.validate(ic_test)
        at_h = frame[frame["horizon"] == self._horizon]
        main = at_h[(at_h["metric"] == "ic_mean") & (at_h["window"] == "full")]
        rows = [self._build_row(frame, at_h, str(f)) for f in main["factor"]]
        if not rows:
            return pd.DataFrame(columns=["factor", "verdict", "failed"])
        return pd.DataFrame(rows).sort_values("t", ascending=False).reset_index(drop=True)

    def _build_row(self, frame: pd.DataFrame, at_h: pd.DataFrame, factor: str) -> dict[str, object]:
        rows = at_h[at_h["factor"] == factor]
        mean = {str(r["window"]): r for r in rows[rows["metric"] == "ic_mean"].to_dict("records")}
        full = mean["full"]
        sign = math.copysign(1.0, float(full["value"]))
        p_bhy = float(full["p_adj_bhy"]) if pd.notna(full["p_adj_bhy"]) else math.nan
        c1 = abs(float(full["t"])) >= self._t_min and p_bhy <= self._alpha
        sub = {w: float(mean[w]["t"]) if w in mean else math.nan for w in self._windows}
        c2 = all(sign * t >= self._t_sub for t in sub.values())  # NaN compares False
        icir_rows = rows[(rows["metric"] == "icir") & (rows["window"] == "full")].to_dict("records")
        icir = (
            icir_rows[0] if icir_rows else {"value": math.nan, "ci_lo": math.nan, "ci_hi": math.nan}
        )
        lo, hi = float(icir["ci_lo"]), float(icir["ci_hi"])
        c3 = lo > 0 or hi < 0
        failed = [str(i) for i, ok in enumerate((c1, c2, c3), start=1) if not ok]
        notes = frame[(frame["factor"] == factor) & (frame["horizon"] == 0)]
        note = notes.set_index("metric")["value"]
        return {
            "factor": factor,
            "ic_mean": float(full["value"]),
            "t": float(full["t"]),
            "p_bhy": p_bhy,
            **{f"t_{w}": t for w, t in sub.items()},
            "icir": float(icir["value"]),
            "icir_ci_lo": lo,
            "icir_ci_hi": hi,
            "c1": c1,
            "c2": c2,
            "c3": c3,
            "verdict": "fail" if failed else "pass",
            "failed": ",".join(failed),
            **{m: float(note.get(m, math.nan)) for m in NOTES},
        }
