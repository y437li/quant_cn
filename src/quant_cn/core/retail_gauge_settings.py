"""Settings of the 散户温度计 RetailGauge nowcast (plan 21, D-142, D-155, D-167)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "retail_gauge.yaml"
_LAGGED = (
    "dtov",
    "tov_acc",
    "mchg",
    "ret_q",
    "big_cum",
    "dd_qhigh",
    "lg_cum",
    "tov_rel_60",
    "lg_60",
)
_MODEL = {
    "n_estimators": 800,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 200,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.7,
    "reg_lambda": 1.0,
}


class RetailGaugeSettings(BaseModel):
    """
    Purpose:
        Feature windows, model parameters and reading rules of the RetailGauge (散户温度计,
        retail_gauge_v5), read from `config/retail_gauge.yaml` (plan 21, D-142, D-155, D-167).

    Contract:
        Input:
            start: str YYYYMMDD (first session loaded); first_quarter: str YYYYMMDD (the
            quarter end that opens the first feature window); windows, halflives: list[int > 0];
            trel_window, trel_min, slope_window, edge_sessions, year_back, half_year,
            margin_ffill, top_turnover_days, reversal_lag, min_window_sessions: int > 0;
            big_move, limit_move, reversal_min: float > 0;
            lagged: list[str] (features also carried as `<name>_lag1`);
            model: dict (LightGBM regressor params); label_abs_max: float > 0;
            min_train_quarters: int > 0; avoid_pct, leaving_pct, inflow_pct: float in (0, 1);
            persist_n, persist_step: int > 0; retrain_months: list[int 1..12];
            model_version: str
        Output:
            frozen pydantic model; `load(repo_root)`
        Raises:
            pydantic.ValidationError  -- out-of-range values or extra keys

    Used by:
        calculation.RetailGaugeMatrices  -- windows
        calculation.RetailGaugeModel  -- LightGBM params
        calculation.RetailGaugeNowcaster  -- thresholds, retrain months
        calculation.RetailGaugeEvaluator  -- avoid_pct
        cli.GaugeCommands  -- loads it
        calculation.RetailGaugeFeatureBuilder  -- feature windows

    Test cases:
        TC-RGS-001  config/retail_gauge.yaml loads with the v5 values; a missing file gives
                    the defaults; an unknown key or avoid_pct 1.5 is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    start: str = "20191001"
    first_quarter: str = "20201231"
    windows: list[int] = Field(default_factory=lambda: [5, 20, 60, 120])
    halflives: list[int] = Field(default_factory=lambda: [5, 20, 60])
    trel_window: int = Field(default=250, gt=0)
    trel_min: int = Field(default=120, gt=0)
    slope_window: int = Field(default=60, gt=1)
    edge_sessions: int = Field(default=20, gt=0)
    year_back: int = Field(
        default=251, gt=1
    )  # sessions back for 12-month return and the 1-year range
    half_year: int = Field(default=125, gt=1)  # sessions back for the 6-month return
    margin_ffill: int = Field(default=5, gt=0)
    top_turnover_days: int = Field(default=5, gt=0)
    reversal_lag: int = Field(default=5, gt=0)
    big_move: float = Field(default=0.05, gt=0)
    limit_move: float = Field(default=0.095, gt=0)
    reversal_min: float = Field(default=0.03, gt=0)
    min_window_sessions: int = Field(default=15, gt=0)
    lagged: list[str] = Field(default_factory=lambda: list(_LAGGED))
    model: dict[str, float | int] = Field(default_factory=lambda: dict(_MODEL))
    label_abs_max: float = Field(default=2.0, gt=0)
    min_train_quarters: int = Field(default=4, gt=0)
    avoid_pct: float = Field(default=0.9, gt=0, lt=1)
    leaving_pct: float = Field(default=0.3, gt=0, lt=1)
    inflow_pct: float = Field(default=0.8, gt=0, lt=1)
    persist_n: int = Field(default=3, gt=0)
    persist_step: int = Field(default=3, gt=0)
    retrain_months: list[int] = Field(default_factory=lambda: [5, 9, 11])
    model_version: str = "retail_gauge_v5"

    @classmethod
    def load(cls, repo_root: Path) -> RetailGaugeSettings:
        """
        Purpose:
            Read config/retail_gauge.yaml under repo_root.

        Contract:
            Input:
                repo_root: Path
            Output:
                RetailGaugeSettings  -- defaults when the file is missing
            Raises:
                ConfigError  -- unreadable YAML or invalid settings
        """
        path = repo_root / FILE
        if not path.exists():
            return cls()
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return cls.model_validate(raw)
        except (yaml.YAMLError, ValidationError) as exc:
            raise ConfigError(f"{path}: {exc}") from exc
