"""Factor campaign charts: rolling IC with a band, ICIR bars, quantile ladder, IC by horizon."""

from __future__ import annotations

import math
from typing import Literal

import pandas as pd
import plotly.graph_objects as go

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.frames import IC_SERIES, IC_TEST, QUANTILE_RETURNS
from quant_cn.visualization.base_chart import BaseChart
from quant_cn.visualization.chart_theme import ChartTheme

Kind = Literal["ic_series", "icir", "quantiles", "horizon"]
KINDS: tuple[Kind, ...] = ("ic_series", "icir", "quantiles", "horizon")


class FactorChart(BaseChart):
    """
    Purpose:
        The four views of a factor campaign (plan 04 phase 6), one single-series chart each so
        identity never rests on colour: "ic_series" (IC_SERIES) the rolling mean IC of one factor
        and horizon with a band of +/- 1.96 sd / sqrt(window / h), the effective number of
        non-overlapping observations; "icir" (IC_TEST) full-window ICIR per factor at one horizon
        with its bootstrap CI; "quantiles" (QUANTILE_RETURNS) mean forward return per quantile of
        one factor and horizon, long-short mean in the title; "horizon" (IC_TEST) full-window
        mean IC of one factor by horizon with its CI, peak horizon and half-life in the title
        (D-095).

    Contract:
        Input:
            theme:   ChartTheme
            kind:    "ic_series" | "icir" | "quantiles" | "horizon"
            factor:  str | None  -- required except for "icir"
            horizon: int > 0     -- ignored by "horizon"
            window:  int > 1     -- rolling window of "ic_series", sessions
            codec:   DateCodec | None  -- date labels of "ic_series" (default DateCodec())
            width, height: int
        Output:
            instance; BaseChart API (frame per kind as above)
        Raises:
            ValueError  -- unknown kind, missing factor, horizon < 1 or window < 2

    Used by:
        research_space/notebooks/20260930_factor_campaign_01.ipynb  -- campaign charts
        plan 06 ReportBuilder                                         -- planned

    Test cases:
        TC-FC-001  ic_series: rolling mean equals the hand mean; band half-width is
                   1.96 sd / sqrt(window / h); x are ISO dates
        TC-FC-002  icir bars sorted by value with CI error bars; quantile ladder excludes the
                   long-short quantile 0 and names its mean in the title
        TC-FC-003  horizon: one point per horizon with CI; title names peak and "rising" for a
                   NaN half-life
        TC-FC-004  bad kind / missing factor raise ValueError; no rows raise ValueError; a wrong
                   frame raises SchemaError
    """

    def __init__(
        self,
        theme: ChartTheme,
        kind: Kind,
        factor: str | None = None,
        horizon: int = 20,
        window: int = 252,
        codec: DateCodec | None = None,
        width: int = 960,
        height: int = 420,
    ) -> None:
        super().__init__(theme, width, height)
        if kind not in KINDS:
            raise ValueError(f"unknown kind {kind!r}")
        if factor is None and kind != "icir":
            raise ValueError(f"kind {kind!r} needs a factor")
        if horizon < 1 or window < 2:  # noqa: PLR2004 -- a rolling sd needs two points
            raise ValueError("horizon must be >= 1 and window >= 2")
        self.kind = kind
        self.factor = factor
        self.horizon = horizon
        self.window = window
        self._codec = codec or DateCodec()

    def build_figure(self, frame: pd.DataFrame) -> go.Figure:
        """
        Purpose:
            The figure for `kind`.

        Contract:
            Input:
                frame: DataFrame  -- IC_SERIES ("ic_series"), IC_TEST ("icir", "horizon"),
                                     QUANTILE_RETURNS ("quantiles")
            Output:
                plotly Figure
            Raises:
                SchemaError  -- frame is not the kind's schema
                ValueError   -- no rows for the factor / horizon
        """
        if self.kind == "ic_series":
            return self._build_ic_series(IC_SERIES.validate(frame))
        if self.kind == "icir":
            return self._build_icir(IC_TEST.validate(frame))
        if self.kind == "quantiles":
            return self._build_quantiles(QUANTILE_RETURNS.validate(frame))
        return self._build_horizon(IC_TEST.validate(frame))

    def _build_ic_series(self, frame: pd.DataFrame) -> go.Figure:
        rows = self._get_rows(frame, factor=True, horizon=True).sort_values("trade_date")
        ic = rows["ic"].astype(float).reset_index(drop=True)
        mean = ic.rolling(self.window).mean()
        half = 1.96 * ic.rolling(self.window).std() / math.sqrt(self.window / self.horizon)
        days = [self._codec.to_date(str(d)).isoformat() for d in rows["trade_date"]]
        t = self.theme
        band = {"mode": "lines", "line": {"width": 0}, "hoverinfo": "skip"}
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=mean + half, name="upper", **band))
        fig.add_trace(
            go.Scatter(
                x=days,
                y=mean - half,
                name="lower",
                fill="tonexty",
                fillcolor=self._compute_fade(0.18),
                **band,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=days,
                y=mean,
                name="rolling mean IC",
                mode="lines",
                line={"color": t.accent, "width": 2},
                hovertemplate="%{y:.3f}<extra>rolling mean IC</extra>",
            )
        )
        fig.add_hline(y=0, line={"color": t.neutral, "width": 1})
        fig.update_layout(
            title_text=f"{self.factor}: {self.window}-session mean IC, h = {self.horizon} "
            f"(band +/- 1.96 sd / sqrt({self.window}/{self.horizon}))"
        )
        fig.update_yaxes(title_text="Rank IC")
        return fig

    def _build_icir(self, frame: pd.DataFrame) -> go.Figure:
        rows = frame[
            (frame["metric"] == "icir")
            & (frame["window"] == "full")
            & (frame["horizon"] == float(self.horizon))
        ].sort_values("value", ascending=False)
        if rows.empty:
            raise ValueError(f"no icir rows at h = {self.horizon}")
        fig = go.Figure(
            go.Bar(
                x=rows["factor"],
                y=rows["value"],
                marker={"color": self.theme.accent, "cornerradius": 4},
                error_y=self._build_error(rows),
                hovertemplate="%{x}: ICIR %{y:.2f}<extra></extra>",
            )
        )
        fig.update_layout(title_text=f"ICIR by factor, h = {self.horizon} (bootstrap 95% CI)")
        fig.update_yaxes(title_text="ICIR (mean IC / sd IC)")
        return fig

    def _build_quantiles(self, frame: pd.DataFrame) -> go.Figure:
        rows = self._get_rows(frame, factor=True, horizon=True)
        means = rows.groupby("quantile")["ret"].mean() * 100
        ladder = means[means.index > 0]
        ls = means.get(0, math.nan)
        fig = go.Figure(
            go.Bar(
                x=[f"Q{int(q)}" for q in ladder.index],
                y=ladder.to_numpy(),
                marker={"color": self.theme.accent, "cornerradius": 4},
                hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
            )
        )
        fig.update_layout(
            title_text=f"{self.factor}: mean {self.horizon}-session return by quantile "
            f"(long-short {ls:.2f}%)"
        )
        fig.update_yaxes(title_text=f"Mean {self.horizon}-session return, %")
        return fig

    def _build_horizon(self, frame: pd.DataFrame) -> go.Figure:
        rows = self._get_rows(frame, factor=True, horizon=False)
        main = rows[
            (rows["metric"] == "ic_mean") & (rows["window"] == "full") & (rows["horizon"] > 0)
        ].sort_values("horizon")
        if main.empty:
            raise ValueError(f"no ic_mean rows for {self.factor}")
        profile = rows[rows["horizon"] == 0].set_index("metric")["value"]
        peak, half = profile.get("peak_horizon", math.nan), profile.get("half_life", math.nan)
        shape = "rising" if pd.isna(half) else f"half-life {half:.0f} sessions"
        fig = go.Figure(
            go.Scatter(
                x=[str(int(h)) for h in main["horizon"]],
                y=main["value"],
                mode="lines+markers",
                line={"color": self.theme.accent, "width": 2},
                marker={"size": 8, "line": {"color": self.theme.surface, "width": 2}},
                error_y=self._build_error(main),
                hovertemplate="h = %{x}: IC %{y:.3f}<extra></extra>",
            )
        )
        fig.add_hline(y=0, line={"color": self.theme.neutral, "width": 1})
        peak_text = "n/a" if pd.isna(peak) else f"{peak:.0f}"
        fig.update_layout(
            title_text=f"{self.factor}: mean IC by horizon (peak {peak_text}, {shape})"
        )
        fig.update_xaxes(type="category", title_text="Horizon, sessions")
        fig.update_yaxes(title_text="Mean rank IC (95% CI)")
        return fig

    def _get_rows(self, frame: pd.DataFrame, factor: bool, horizon: bool) -> pd.DataFrame:
        mask = pd.Series(True, index=frame.index)
        if factor:
            mask &= frame["factor"] == self.factor
        if horizon:
            mask &= frame["horizon"] == float(self.horizon)
        rows = frame[mask]
        if rows.empty:
            raise ValueError(f"no rows for {self.factor} at h = {self.horizon}")
        return rows

    def _build_error(self, rows: pd.DataFrame) -> dict[str, object]:
        return {
            "type": "data",
            "symmetric": False,
            "array": (rows["ci_hi"] - rows["value"]).to_numpy(float),
            "arrayminus": (rows["value"] - rows["ci_lo"]).to_numpy(float),
            "color": self.theme.text_secondary,
            "thickness": 1.5,
        }

    def _compute_fade(self, alpha: float) -> str:
        hexa = self.theme.accent.lstrip("#")
        r, g, b = (int(hexa[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({r},{g},{b},{alpha})"
