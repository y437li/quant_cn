"""Risk model charts: cumulative factor returns, factor correlations, risk decomposition."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.frames import FACTOR_COV, FACTOR_RETURN, RISK_DECOMP
from quant_cn.visualization.base_chart import BaseChart
from quant_cn.visualization.chart_theme import ChartTheme

Kind = Literal["cumulative", "correlation", "decomposition"]
KINDS: tuple[Kind, ...] = ("cumulative", "correlation", "decomposition")
ANNUAL = np.sqrt(252.0)


class RiskChart(BaseChart):
    """
    Purpose:
        Three views of the risk model (plan 05 phase 5), over frames only: "cumulative"
        (FACTOR_RETURN) compounded returns of the chosen factors, one line each, labelled at the
        line end so identity does not rest on colour; "correlation" (FACTOR_COV) the factor
        correlation matrix of one session as a diverging heatmap (-1..1); "decomposition"
        (RISK_DECOMP) each factor's contribution to a portfolio's annualised volatility as
        horizontal bars (specific risk as its own bar), total in the title.

    Contract:
        Input:
            theme:      ChartTheme
            kind:       "cumulative" | "correlation" | "decomposition"
            factors:    Sequence[str]  -- factors to draw ("cumulative", "correlation"); empty =
                                          every non-industry factor
            trade_date: str | None     -- session of "correlation" / "decomposition" (None = last)
            portfolio:  str | None     -- RISK_DECOMP.portfolio of "decomposition" (None = first)
            codec:      DateCodec | None; width, height: int
        Output:
            instance; BaseChart API
        Raises:
            ValueError  -- unknown kind

    Used by:
        research_space/notebooks/20261111_risk_model_validation.ipynb  -- model charts

    Test cases:
        TC-RC-001  cumulative: one line per factor, last value = prod(1 + r) - 1, ISO dates
        TC-RC-002  correlation: symmetric heatmap with unit diagonal for the chosen session
        TC-RC-003  decomposition: one bar per factor contribution plus specific, annualised;
                   total in the title; unknown kind or empty selection raise ValueError
    """

    def __init__(
        self,
        theme: ChartTheme,
        kind: Kind,
        factors: Sequence[str] = (),
        trade_date: str | None = None,
        portfolio: str | None = None,
        codec: DateCodec | None = None,
        width: int = 960,
        height: int = 520,
    ) -> None:
        super().__init__(theme, width, height)
        if kind not in KINDS:
            raise ValueError(f"unknown kind {kind!r}")
        self.kind = kind
        self.factors = list(factors)
        self.trade_date = trade_date
        self.portfolio = portfolio
        self._codec = codec or DateCodec()

    def build_figure(self, frame: pd.DataFrame) -> go.Figure:
        """
        Purpose:
            The figure for `kind`.

        Contract:
            Input:
                frame: DataFrame  -- FACTOR_RETURN ("cumulative"), FACTOR_COV ("correlation"),
                                     RISK_DECOMP ("decomposition")
            Output:
                plotly Figure
            Raises:
                SchemaError  -- frame is not the kind's schema
                ValueError   -- nothing to draw
        """
        if self.kind == "cumulative":
            return self._build_cumulative(FACTOR_RETURN.validate(frame))
        if self.kind == "correlation":
            return self._build_correlation(FACTOR_COV.validate(frame))
        return self._build_decomposition(RISK_DECOMP.validate(frame))

    def _list_factors(self, available: Sequence[str]) -> list[str]:
        chosen = self.factors or [f for f in available if not f.startswith("ind_")]
        out = [f for f in chosen if f in set(available)]
        if not out:
            raise ValueError("no factors to draw")
        return out

    def _build_cumulative(self, frame: pd.DataFrame) -> go.Figure:
        wide = frame.pivot(index="trade_date", columns="factor", values="ret").sort_index()
        names = self._list_factors(list(wide.columns))
        days = [self._codec.to_date(str(d)).isoformat() for d in wide.index]
        fig = go.Figure()
        for name in names:
            path = (1 + wide[name].fillna(0.0)).cumprod() - 1
            fig.add_trace(go.Scatter(x=days, y=path, mode="lines", name=name, line={"width": 1.5}))
            fig.add_annotation(
                x=days[-1], y=float(path.iloc[-1]), text=name, showarrow=False, xanchor="left"
            )
        fig.update_layout(title="Cumulative factor returns", yaxis={"tickformat": ".0%"})
        return fig

    def _build_correlation(self, frame: pd.DataFrame) -> go.Figure:
        date = self.trade_date or str(frame["trade_date"].max())
        rows = frame[frame["trade_date"] == date]
        if rows.empty:
            raise ValueError(f"no covariance for {date}")
        names = self._list_factors(sorted(rows["factor_i"].unique()))
        cov = rows.pivot(index="factor_i", columns="factor_j", values="cov").loc[names, names]
        sd = np.sqrt(np.diag(cov.to_numpy(float)))
        corr = cov.to_numpy(float) / np.outer(sd, sd)
        t = self.theme
        heat = go.Heatmap(
            z=corr,
            x=names,
            y=names,
            zmin=-1,
            zmax=1,
            colorscale=[[0.0, t.down], [0.5, t.surface], [1.0, t.up]],
        )
        fig = go.Figure(heat)
        fig.update_layout(title=f"Factor correlations {date}", yaxis={"autorange": "reversed"})
        return fig

    def _build_decomposition(self, frame: pd.DataFrame) -> go.Figure:
        portfolio = self.portfolio or str(frame["portfolio"].iloc[0])
        rows = frame[frame["portfolio"] == portfolio].set_index("component")
        if self.trade_date is not None:
            rows = rows[rows["trade_date"] == self.trade_date]
        parts = rows[rows.index.str.startswith("f:")]["risk"].rename(lambda c: c[2:])
        if parts.empty:
            raise ValueError(f"no decomposition for {portfolio}")
        risk = rows["risk"].astype(float)
        spec = float(risk["specific"]) ** 2 / float(risk["total"])
        bars = pd.concat([parts, pd.Series({"specific": spec})]) * ANNUAL
        bars = bars.reindex(bars.abs().sort_values().index)
        t = self.theme
        colors = [t.up if v >= 0 else t.down for v in bars]
        fig = go.Figure(
            go.Bar(x=bars.to_numpy(), y=list(bars.index), orientation="h", marker={"color": colors})
        )
        total = float(risk["total"]) * ANNUAL
        fig.update_layout(
            title=f"{portfolio}: annualised vol {total:.1%} by contribution",
            xaxis={"tickformat": ".1%"},
        )
        return fig
