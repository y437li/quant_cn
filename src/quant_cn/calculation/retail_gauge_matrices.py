"""Daily wide matrices and the path / multi-scale features of the RetailGauge (plan 21 ph2)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.retail_gauge_settings import RetailGaugeSettings

MATRIX_NAMES = ("px", "tov", "cmv", "lg", "elg", "sm", "rz")


class RetailGaugeMatrices:
    """
    Purpose:
        Hold the daily (session x ts_code) matrices of the RetailGauge and compute, at any as-of
        session, the v3 / v4 path features over a quarter window and the v5 multi-scale features
        (plan 21 ph2, D-142; an OOP port of research_space/prototypes/holder_nowcast):
        - path (window (a, b]): returns over the quarter, 6 and 12 months, drawdowns, big days,
          reversals, volatility, turnover level / change / acceleration / concentration,
          large + extra-large order flow and runs, margin change and runs, log float cap;
          order-size split (large, extra-large, small);
        - scale (as of b): per window n the mean relative turnover (log of turnover over its
          own rolling mean), log return, large-order flow per float cap, volatility, log margin
          change; EWMA of relative turnover and flow; 60-session slopes.
        Money flows are 万元 and circ_mv is 万元, so flow / cap ratios are unitless. Only rows
        on or before b are read (point in time).

    Contract:
        Input:
            settings: RetailGaugeSettings
            frames:   dict[str, DataFrame]  -- MATRIX_NAMES, index trade_date (YYYYMMDD str,
                                               sorted), columns ts_code: px adjusted close,
                                               tov turnover_rate_f, cmv circ_mv, lg / elg / sm
                                               net buy amount of large / extra-large / small
                                               orders, rz financing balance (raw, NaN gaps)
        Output:
            instance; `compute_path(a, b)`, `compute_scale(b)` -> DataFrame indexed by ts_code
            (+-inf replaced by NaN); `sessions` (Index)
        Raises:
            KeyError  -- a frame missing

    Used by:
        calculation.RetailGaugeFeatureBuilder  -- feature rows

    Test cases:
        TC-RGM-001  compute_path on a 2-stock fixture: ret_q, dd_qhigh, n_bigup, tov_acc,
                    big_cum, out_maxrun, mchg, lg_inrun equal hand values; a window with too
                    few sessions -> empty frame
        TC-RGM-002  compute_scale: ret_n, lg_n, rz_n, tov_slope equal hand values; a value
                    dated after b never changes the result (PIT)
    """

    def __init__(self, settings: RetailGaugeSettings, frames: dict[str, pd.DataFrame]) -> None:
        self._s = settings
        px = frames["px"].sort_index()
        self.sessions = px.index
        codes = px.columns
        self._m = {k: frames[k].reindex(index=self.sessions, columns=codes) for k in MATRIX_NAMES}
        self._m["px"] = px
        self._ret = px.pct_change(fill_method=None)
        self._log_ret = pd.DataFrame(np.log(px), index=px.index, columns=codes).diff()
        tov = self._m["tov"]
        mean = tov.rolling(settings.trel_window, min_periods=settings.trel_min).mean()
        self._trel = pd.DataFrame(np.log(tov / mean), index=px.index, columns=codes)
        self._lgn = self._m["lg"] / self._m["cmv"]
        self._rz5 = self._m["rz"].ffill(limit=settings.margin_ffill)
        self._log_rz = pd.DataFrame(np.log(self._rz5), index=px.index, columns=codes)
        self._ewm = {
            (name, h): frame.ewm(halflife=h, min_periods=h).mean()
            for h in settings.halflives
            for name, frame in (("tov", self._trel), ("lg", self._lgn))
        }

    def compute_path(self, a: str, b: str) -> pd.DataFrame:
        """
        Purpose:
            v3 / v4 path features over the sessions in (a, b].

        Contract:
            Input:
                a, b: str  -- YYYYMMDD, a < b (a = previous quarter end)
            Output:
                DataFrame  -- one row per ts_code; empty when the window has fewer than
                              min_window_sessions sessions or no session before it
            Raises:
                (none)
        """
        s, m = self._s, self._m
        idx = np.where((self.sessions > a) & (self.sessions <= b))[0]
        if len(idx) < s.min_window_sessions or idx[0] == 0:
            return pd.DataFrame()
        e, first, last = idx[-1], idx[: s.edge_sessions], idx[-s.edge_sessions :]
        px, pb = m["px"], m["px"].iloc[e]
        rw = self._ret.iloc[idx]
        big = m["lg"] + m["elg"]
        cmv = m["cmv"].iloc[idx].mean()
        hist = px.iloc[max(0, e - s.year_back) : e + 1]
        f = pd.DataFrame(index=px.columns)
        f["ret_q"] = np.log(pb / px.iloc[idx[0] - 1])
        f["ret_6m"] = np.log(pb / px.iloc[max(0, e - s.half_year)])
        f["ret_12m"] = np.log(pb / px.iloc[max(0, e - s.year_back)])
        f["dd_high252"] = pb / hist.max() - 1
        f["up_low252"] = pb / hist.min() - 1
        f["dd_qhigh"] = pb / px.iloc[idx].max() - 1
        f["ret_last20"] = np.log(pb / px.iloc[last[0] - 1])
        f["n_bigup"] = (rw >= s.big_move).sum()
        f["n_bigdn"] = (rw <= -s.big_move).sum()
        f["limitups"] = (rw >= s.limit_move).sum()
        r5 = pd.DataFrame(np.log(px.iloc[idx]), columns=px.columns).diff(s.reversal_lag)
        sign = pd.DataFrame(
            np.sign(r5.where(r5.abs() > s.reversal_min)), index=r5.index, columns=r5.columns
        )
        f["reversals"] = (sign.ffill().diff().abs() > 0).sum()
        f["vol_q"] = rw.std()
        f["vol_acc"] = self._ret.iloc[last].std() / self._ret.iloc[first].std()
        self._add_turnover(f, idx, first, last)
        self._add_flow(f, big, "big", idx, first, last, cmv)
        self._add_margin(f, idx, last)
        f["lmv"] = np.log(cmv)
        self._add_order_split(f, idx, first, last, cmv)
        return f.replace([np.inf, -np.inf], np.nan)

    def compute_scale(self, b: str) -> pd.DataFrame:
        """
        Purpose:
            v5 multi-scale, EWMA and slope features as of the last session on or before b.

        Contract:
            Input:
                b: str  -- YYYYMMDD
            Output:
                DataFrame  -- one row per ts_code; NaN where a window reaches before the start
            Raises:
                (none)
        """
        s = self._s
        e = int(np.where(self.sessions <= b)[0][-1])
        f = pd.DataFrame(index=self._m["px"].columns)
        for n in s.windows:
            rows = slice(e - n + 1, e + 1) if e >= n else slice(0, 0)
            f[f"tov_rel_{n}"] = self._trel.iloc[rows].mean()
            f[f"ret_{n}"] = self._log_ret.iloc[rows].sum()
            f[f"lg_{n}"] = self._lgn.iloc[rows].sum()
            f[f"vol_{n}"] = self._log_ret.iloc[rows].std()
            back = self._rz5.iloc[e - n] if e >= n else np.nan
            f[f"rz_{n}"] = np.log(self._rz5.iloc[e] / back)
        for h in s.halflives:
            f[f"tov_ewm_{h}"] = self._ewm[("tov", h)].iloc[e]
            f[f"lg_ewm_{h}"] = self._ewm[("lg", h)].iloc[e]
        f[f"tov_slope{s.slope_window}"] = self._compute_slope(self._trel, e)
        f[f"rz_slope{s.slope_window}"] = self._compute_slope(self._log_rz, e)
        return f.replace([np.inf, -np.inf], np.nan)

    def _add_flow(
        self,
        f: pd.DataFrame,
        flow: pd.DataFrame,
        name: str,
        idx: np.ndarray,
        first: np.ndarray,
        last: np.ndarray,
        cmv: pd.Series,
    ) -> None:
        window = flow.iloc[idx]
        f[f"{name}_cum"] = window.sum() / cmv
        f[f"{name}_last20"] = flow.iloc[last].sum() / cmv
        f[f"{name}_trend"] = (flow.iloc[last].sum() - flow.iloc[first].sum()) / cmv
        f["out_frac"] = (window < 0).sum() / window.notna().sum().replace(0, np.nan)
        f["out_maxrun"] = self._compute_max_run(window < 0)

    def _add_turnover(
        self, f: pd.DataFrame, idx: np.ndarray, first: np.ndarray, last: np.ndarray
    ) -> None:
        all_tov = self._m["tov"]
        tov = all_tov.iloc[idx]
        f["tov"] = tov.mean()
        f["tov_acc"] = np.log(all_tov.iloc[last].mean() / all_tov.iloc[first].mean())
        before = all_tov.iloc[max(0, idx[0] - len(idx)) : idx[0]]
        f["dtov"] = np.log(tov.mean() / before.mean())
        top = np.sort(tov.fillna(0).to_numpy(), axis=0)[-self._s.top_turnover_days :]
        f["tov_top5"] = top.mean(0)
        f["tov_conc"] = top.sum(0) / tov.sum().replace(0, np.nan)

    def _add_order_split(
        self, f: pd.DataFrame, idx: np.ndarray, first: np.ndarray, last: np.ndarray, cmv: pd.Series
    ) -> None:
        m = self._m
        f["lg_cum"] = m["lg"].iloc[idx].sum() / cmv
        f["lg_last20"] = m["lg"].iloc[last].sum() / cmv
        f["lg_trend"] = (m["lg"].iloc[last].sum() - m["lg"].iloc[first].sum()) / cmv
        f["lg_inrun"] = self._compute_max_run(m["lg"].iloc[idx] > 0)
        f["lg_outrun"] = self._compute_max_run(m["lg"].iloc[idx] < 0)
        f["elg_cum"] = m["elg"].iloc[idx].sum() / cmv
        f["sm_cum"] = m["sm"].iloc[idx].sum() / cmv
        f["sm_last20"] = m["sm"].iloc[last].sum() / cmv

    def _add_margin(self, f: pd.DataFrame, idx: np.ndarray, last: np.ndarray) -> None:
        rz = self._m["rz"]
        z = rz.iloc[idx]
        f["mchg"] = z.ffill().iloc[-1] / z.bfill().iloc[0] - 1
        f["m_last20"] = rz.iloc[last].ffill().iloc[-1] / rz.iloc[last].bfill().iloc[0] - 1
        f["m_uprun"] = self._compute_max_run(z.diff() > 0)

    def _compute_slope(self, frame: pd.DataFrame, e: int) -> pd.Series:
        n = self._s.slope_window
        if e < n - 1:
            return pd.Series(np.nan, index=frame.columns)
        y = frame.iloc[e - n + 1 : e + 1]
        x = np.arange(n) - (n - 1) / 2
        return y.mul(x, axis=0).sum() / (x**2).sum()

    @staticmethod
    def _compute_max_run(mask: pd.DataFrame) -> pd.Series:
        """Longest run of consecutive True per column."""
        rows = mask.to_numpy().astype(np.int8)
        best = np.zeros(rows.shape[1])
        cur = np.zeros(rows.shape[1])
        for row in rows:
            cur = (cur + 1) * row
            best = np.maximum(best, cur)
        return pd.Series(best, index=mask.columns)
