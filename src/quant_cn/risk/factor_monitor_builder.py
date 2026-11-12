"""Daily factor returns and volatility behind the app's 因子监控 page (plan 15 phase 7c, D-132)."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "factor_monitor.json"
ANNUAL = 252
WINDOWS = {"d1": 1, "w1": 5, "m1": 21, "m3": 63, "y1": 252}  # sessions
REALIZED = (21, 63)
_RETURNS = "SELECT trade_date, factor, ret FROM derived.risk_factor_return ORDER BY trade_date"
_VARIANCE = """
SELECT trade_date, factor_i AS factor, cov FROM derived.risk_factor_cov
WHERE factor_i = factor_j ORDER BY trade_date
"""
_LABELS = "SELECT DISTINCT l1_code, l1_name FROM derived.industry_l1 WHERE l1_name IS NOT NULL"
_COUNTRY = "country"
_INDUSTRY = "ind_"


class FactorMonitorBuilder:
    """
    Purpose:
        Turn the stored risk-model frames into the factor monitor: for every factor (country,
        Shenwan L1 industries, styles) its compounded return over 1 d / 1 w / 1 m / 3 m / YTD /
        1 y, forecast volatility (sqrt of the covariance diagonal, annualised with 252),
        realized volatility over 21 and 63 sessions, their ratio, and today's return in units of
        the forecast daily sigma made at the previous close; plus daily series of the cumulative
        return, forecast vol and 21-session realized vol for the last `series_days` sessions.
        No model math: only derived.risk_factor_return and derived.risk_factor_cov are read.

    Contract:
        Input:
            query:       LakeQuery  -- reads derived.risk_factor_return, risk_factor_cov,
                                       industry_l1 (labels; optional)
            model:       str        -- risk model name shown in the document
            series_days: int        -- sessions kept in the daily series (> 0)
        Output:
            instance; `build` -> dict, `write` -> Path
        Raises:
            ValueError  -- series_days < 1

    Used by:
        cli.ResearchCommands  -- `factor-monitor` command

    Test cases:
        TC-FMB-001  window returns compound prod(1 + f) - 1 over the factor's rows in the last n
                    sessions; YTD from Jan 1 of the as-of year; d1 = the as-of return
        TC-FMB-002  forecast vol = sqrt(diag cov at as_of) * sqrt(252); sigma_move uses the cov of
                    the previous session; realized vol = sample sd over 21 / 63 rows * sqrt(252),
                    None with fewer rows; ratio = realized_21 / forecast
        TC-FMB-003  a factor missing on some days: those days are skipped (not zero-filled) and
                    appear as null in the series; series cut to series_days; kinds and labels
        TC-FMB-004  no factor-return view or rows -> LakeError; write puts factor_monitor.json in
                    the directory and a missing directory raises LakeError; series_days 0 raises
    """

    def __init__(self, query: LakeQuery, model: str, series_days: int) -> None:
        if series_days < 1:
            raise ValueError(f"series_days must be positive, got {series_days}")
        self._query = query
        self._model = model
        self._series_days = series_days

    def build(self) -> dict[str, Any]:
        """
        Purpose:
            The factor monitor document as of the last factor-return session.

        Contract:
            Input:
                (none)
            Output:
                dict  -- {as_of, model, n_sessions, dates: [YYYYMMDD], factors: [{factor, label,
                         kind (country / industry / style), ret: {d1, w1, m1, m3, ytd, y1},
                         forecast_vol, realized_vol_21, realized_vol_63, vol_ratio, sigma_move,
                         cum: [..], forecast: [..], realized: [..]}]}; returns and vols as
                         fractions rounded to 6 places; None where not computable; series
                         aligned with `dates`
            Raises:
                LakeError  -- view missing or no rows
        """
        for view in ("derived.risk_factor_return", "derived.risk_factor_cov"):
            if not self._query.has_view(view):
                raise LakeError(f"{view} missing: run make risk-model")
        returns = self._query.sql(_RETURNS).pivot(
            index="trade_date", columns="factor", values="ret"
        )
        if returns.empty:
            raise LakeError("derived.risk_factor_return has no rows: run make risk-model")
        variance = self._query.sql(_VARIANCE).pivot(
            index="trade_date", columns="factor", values="cov"
        )
        variance = variance.reindex(index=returns.index, columns=returns.columns)
        dates = returns.index.tolist()
        shown = dates[-self._series_days :]
        labels = self._read_labels()
        factors = [
            self._build_factor(f, returns[f], variance[f], shown, labels)
            for f in self._list_factors(returns.columns.tolist())
        ]
        return {
            "as_of": dates[-1],
            "model": self._model,
            "n_sessions": len(dates),
            "dates": shown,
            "factors": factors,
        }

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build the document and write it as `factor_monitor.json` for the app's data dir.

        Contract:
            Input:
                out_dir: Path  -- existing directory
            Output:
                Path  -- the written file, UTF-8 JSON
            Raises:
                LakeError  -- as build; also when out_dir is not a directory
        """
        if not out_dir.is_dir():
            raise LakeError(f"factor monitor output directory missing: {out_dir}")
        doc = self.build()
        path = out_dir / FILE_NAME
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        logger.info(
            "factor monitor: %d factors as of %s -> %s", len(doc["factors"]), doc["as_of"], path
        )
        return path

    def _build_factor(
        self,
        factor: str,
        ret: pd.Series,
        var: pd.Series,
        shown: list[str],
        labels: dict[str, str],
    ) -> dict[str, Any]:
        as_of = ret.index[-1]
        sd = np.sqrt(var.clip(lower=0))
        rows = ret.dropna()  # missing days are skipped, not zero-filled
        realized = {n: rows.rolling(n, min_periods=n).std().reindex(ret.index) for n in REALIZED}
        forecast = self._to_number(sd.iloc[-1] * math.sqrt(ANNUAL))
        realized_21 = self._to_number(self._find_last(realized[21]) * math.sqrt(ANNUAL))
        previous = sd.shift(1).iloc[-1]
        cum = (1 + ret.fillna(0)).cumprod().where(ret.notna())
        cum_shown = cum.loc[shown]
        base = cum.loc[: shown[0]].iloc[:-1].dropna()
        cum_shown = cum_shown / (base.iloc[-1] if not base.empty else 1.0) - 1
        return {
            "factor": factor,
            "label": labels.get(factor.removeprefix(_INDUSTRY), factor),
            "kind": self._get_kind(factor),
            "ret": self._compute_window_returns(ret, as_of),
            "forecast_vol": forecast,
            "realized_vol_21": realized_21,
            "realized_vol_63": self._to_number(self._find_last(realized[63]) * math.sqrt(ANNUAL)),
            "vol_ratio": self._to_number(realized_21 / forecast)
            if realized_21 and forecast
            else None,
            "sigma_move": self._to_number(ret.iloc[-1] / previous) if previous else None,
            "cum": [self._to_number(v) for v in cum_shown],
            "forecast": [self._to_number(v * math.sqrt(ANNUAL)) for v in sd.loc[shown]],
            "realized": [self._to_number(v * math.sqrt(ANNUAL)) for v in realized[21].loc[shown]],
        }

    def _compute_window_returns(self, ret: pd.Series, as_of: str) -> dict[str, float | None]:
        out = {k: self._compute_compound(ret.iloc[-n:]) for k, n in WINDOWS.items()}
        out["ytd"] = self._compute_compound(ret[ret.index >= f"{as_of[:4]}0101"])
        return out

    def _compute_compound(self, part: pd.Series) -> float | None:
        rows = part.dropna()
        return self._to_number(float(np.prod(1 + rows.to_numpy()) - 1)) if not rows.empty else None

    def _read_labels(self) -> dict[str, str]:
        if not self._query.has_view("derived.industry_l1"):
            return {}
        rows = self._query.sql(_LABELS)
        return dict(zip(rows["l1_code"], rows["l1_name"], strict=True))

    @staticmethod
    def _get_kind(factor: str) -> str:
        if factor == _COUNTRY:
            return "country"
        return "industry" if factor.startswith(_INDUSTRY) else "style"

    def _list_factors(self, factors: list[str]) -> list[str]:
        order = {"country": 0, "style": 1, "industry": 2}
        return sorted(factors, key=lambda f: (order[self._get_kind(f)], f))

    @staticmethod
    def _find_last(series: pd.Series) -> float:
        value = series.iloc[-1]
        return float(value) if pd.notna(value) else math.nan

    @staticmethod
    def _to_number(value: object) -> float | None:
        if value is None:
            return None
        number = float(value)  # type: ignore[arg-type]
        return None if math.isnan(number) or math.isinf(number) else round(number, 6)
