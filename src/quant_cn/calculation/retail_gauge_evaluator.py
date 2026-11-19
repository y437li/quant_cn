"""Quarterly scoring of the RetailGauge against holder counts and returns (plan 21 ph3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter

REPORT = "reports/retail_gauge/evaluation.parquet"
FWD_SESSIONS = 60
HIT_RANK = 0.7  # a top-decile call is a hit when the realised change ranks in the top 30%
LOW_IC = 0.4  # plan 21 risk: a quarter below this rank IC is flagged
TOP, BOTTOM = 0.9, 0.1  # decile edges of the hit rates
MIN_LABELS = 3  # fewer labelled rows -> no IC
_PRICES = """
SELECT d.ts_code, d.trade_date, d.close * a.adj_factor AS v
FROM curated.daily d JOIN curated.adj_factor a USING (ts_code, trade_date)
WHERE d.trade_date >= ?
"""


class RetailGaugeEvaluator:
    """
    Purpose:
        Score each walk-forward quarter of the RetailGauge (plan 21 ph3, D-142, D-155):
        - rank IC of pct against the realised holder change y;
        - top-decile hit: share of pct >= 0.9 whose y ranks in the top 30% of the quarter;
          bottom-decile hit: pct < 0.1 and y in the bottom 30%;
        - avoid excess: mean 60-session return (adjusted close, from the as-of close) of the
          avoid names (pct >= avoid_pct) minus the equal-weight mean of all scored names, in %;
          NaN until 60 sessions have passed;
        - ic_low when the IC is below 0.4.
        Written to derived/reports/retail_gauge/evaluation.parquet.

    Contract:
        Input:
            settings: RetailGaugeSettings
            query:    LakeQuery      -- curated daily, adj_factor
            writer:   ParquetWriter  -- write_table
        Output:
            instance; `run(backtest)` -> DataFrame q, as_of, n, ic, hit_top, hit_bottom,
            avoid_n, avoid_excess, ic_low; `compute_scores(backtest, fwd)` (static)
        Raises:
            LakeError  -- query or write failure

    Used by:
        cli.GaugeCommands  -- `retail-gauge-backtest`

    Test cases:
        TC-RGE-001  compute_scores on a hand quarter: IC 1 for a perfect ranking, hit shares,
                    avoid excess = avoid mean minus all mean; a quarter without labels has
                    NaN IC; ic_low below 0.4
    """

    def __init__(
        self, settings: RetailGaugeSettings, query: LakeQuery, writer: ParquetWriter
    ) -> None:
        self._s = settings
        self._query = query
        self._writer = writer

    def run(self, backtest: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Score every quarter of a walk-forward table and store the report.

        Contract:
            Input:
                backtest: DataFrame  -- ts_code, q, as_of, y, pct (RetailGaugeNowcaster)
            Output:
                DataFrame  -- one row per quarter (see class)
            Raises:
                LakeError  -- query or write failure
        """
        px = self._query.sql(_PRICES, [str(backtest["as_of"].min())])
        px["ts_code"] = px["ts_code"].astype(str)
        px["trade_date"] = px["trade_date"].astype(str)
        wide = px.pivot(index="trade_date", columns="ts_code", values="v").sort_index()
        ret = (wide.shift(-FWD_SESSIONS) / wide - 1).rename_axis("as_of").reset_index()
        fwd = ret.melt(id_vars="as_of", var_name="ts_code", value_name="fwd").dropna()
        out = self.compute_scores(backtest, fwd, self._s.avoid_pct)
        self._writer.write_table("derived", REPORT, out)
        return out

    @staticmethod
    def compute_scores(backtest: pd.DataFrame, fwd: pd.DataFrame, avoid_pct: float) -> pd.DataFrame:
        """
        Purpose:
            The per-quarter scores from readings and forward returns.

        Contract:
            Input:
                backtest:  DataFrame  -- ts_code, q, as_of, y, pct
                fwd:       DataFrame  -- ts_code, as_of, fwd (60-session return, fraction)
                avoid_pct: float
            Output:
                DataFrame  -- see class
            Raises:
                (none)
        """
        frame = backtest.merge(fwd, on=["ts_code", "as_of"], how="left")
        rows = []
        for q, g in frame.groupby("q"):
            yr = g["y"].rank(pct=True)
            top, bottom, avoid = g["pct"] >= TOP, g["pct"] < BOTTOM, g["pct"] >= avoid_pct
            excess = (
                (g.loc[avoid, "fwd"].mean() - g["fwd"].mean()) * 100
                if g["fwd"].notna().any()
                else np.nan
            )
            ic = (
                g["pct"].corr(g["y"], method="spearman")
                if g["y"].notna().sum() >= MIN_LABELS
                else np.nan
            )
            rows.append(
                {
                    "q": q,
                    "as_of": g["as_of"].iloc[0],
                    "n": len(g),
                    "ic": ic,
                    "hit_top": (yr[top & g["y"].notna()] >= HIT_RANK).mean(),
                    "hit_bottom": (yr[bottom & g["y"].notna()] <= 1 - HIT_RANK).mean(),
                    "avoid_n": int(avoid.sum()),
                    "avoid_excess": excess,
                    "ic_low": bool(ic < LOW_IC) if not np.isnan(ic) else False,
                }
            )
        return pd.DataFrame(rows)
