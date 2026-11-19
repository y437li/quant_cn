"""Settings of the volatility monitor: watched VIX lines and their alerts (plan 03 ph6, D-152)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "volatility_monitor.yaml"


class VolatilityLine(BaseModel):
    """
    Purpose:
        One monitored volatility index: key, Chinese name, display group, source kind ("cboe" =
        a curated.cboe_vix index_code, "option" = an opt_basic opt_code whose VIX is computed),
        and its optional alerts: level (value at or above), jump (one-day rise at or above this
        fraction), pct (value at or above this percentile of the window).

    Contract:
        Input:
            key, name, group, code: str; kind: "cboe" | "option";
            alert_level: float > 0 | None; alert_jump: float > 0 | None;
            alert_pct: float in (0, 1) | None
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- unknown kind, out-of-range alert, extra keys

    Used by:
        core.VolatilityMonitorSettings        -- field `lines`
        calculation.VolatilityMonitorBuilder  -- one document line each

    Test cases:
        TC-VMS-001  config/volatility_monitor.yaml loads; an unknown kind or alert_pct 1.5 is
                    refused; duplicate keys are refused; a missing file gives no lines
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str
    name: str
    group: str
    kind: Literal["cboe", "option"]
    code: str
    alert_level: float | None = Field(default=None, gt=0)
    alert_jump: float | None = Field(default=None, gt=0)
    alert_pct: float | None = Field(default=None, gt=0, lt=1)


class VolatilityMonitorSettings(BaseModel):
    """
    Purpose:
        The volatility monitor's lines, percentile window and calculator setting, read from
        `config/volatility_monitor.yaml`.

    Contract:
        Input:
            window: int > 0 (sessions); min_obs: int > 0; min_days: int >= 0;
            lines: list[VolatilityLine] with unique keys
        Output:
            frozen pydantic model; `load(repo_root)`
        Raises:
            pydantic.ValidationError  -- invalid values, duplicate line keys

    Used by:
        cli.ReportCommands                    -- `volatility-monitor` command
        calculation.VolatilityMonitorBuilder  -- lines and thresholds

    Test cases:
        TC-VMS-001  config/volatility_monitor.yaml loads; an unknown kind or alert_pct 1.5 is
                    refused; duplicate keys are refused; a missing file gives no lines
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    window: int = Field(default=250, gt=0)
    min_obs: int = Field(default=120, gt=0)
    min_days: int = Field(default=7, ge=0)
    lines: list[VolatilityLine] = []

    @model_validator(mode="after")
    def _check_keys(self) -> VolatilityMonitorSettings:
        keys = [line.key for line in self.lines]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate volatility line keys: {keys}")
        return self

    @classmethod
    def load(cls, repo_root: Path) -> VolatilityMonitorSettings:
        """
        Purpose:
            Read `<repo_root>/config/volatility_monitor.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                VolatilityMonitorSettings  -- no lines when the file is missing
            Raises:
                ConfigError  -- unreadable YAML or invalid content
        """
        path = repo_root / FILE
        if not path.exists():
            return cls()
        try:
            return cls(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid volatility monitor settings {path}: {exc}") from exc
