"""Settings of the rates and RMB monitor: lines, sources and alerts (plan 34, D-171)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "rates_fx_monitor.yaml"
Kind = Literal["curve", "us", "shibor", "fx", "fixing", "equity_ep", "combo"]


class RatesFxLine(BaseModel):
    """
    Purpose:
        One monitored series: key, Chinese name, group (债市 / 汇率), source kind and its
        parameters (curve + field, field, code, or combo op + a + b), unit (yield, bp, rate,
        gap), whether it is shown, and its optional alerts.

    Contract:
        Input:
            key, name, group: str; kind: Kind; curve, field, code, op, a, b: str | None;
            unit: "yield" | "bp" | "rate" | "gap"; show: bool;
            week_move, week_widen, pct_above, abs_above, below, above: float | None;
            extreme: bool
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- unknown kind or unit, a kind without its parameters,
                                         extra keys

    Used by:
        core.RatesFxMonitorSettings          -- field `lines`
        calculation.RatesFxSeriesReader      -- source of each line
        calculation.RatesFxMonitorBuilder    -- one document row each

    Test cases:
        TC-RFS-001  config/rates_fx_monitor.yaml loads; a combo without b, a curve without
                    field, an unknown unit and duplicate keys are refused; a combo naming an
                    unknown or later line is refused; a missing file gives no lines
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str
    name: str
    group: str
    kind: Kind
    unit: Literal["yield", "bp", "rate", "gap"]
    curve: str | None = None
    field: str | None = None
    code: str | None = None
    op: Literal["diff", "mul", "div", "gap"] | None = None
    a: str | None = None
    b: str | None = None
    show: bool = True
    week_move: float | None = Field(default=None, gt=0)
    week_widen: float | None = Field(default=None, gt=0)
    pct_above: float | None = Field(default=None, gt=0, lt=1)
    abs_above: float | None = Field(default=None, gt=0)
    below: float | None = None
    above: float | None = None
    extreme: bool = False

    @model_validator(mode="after")
    def _check_source(self) -> RatesFxLine:
        need = {"curve": ("curve", "field"), "us": ("field",), "shibor": ("field",),
                "fx": ("code",), "fixing": ("field",), "equity_ep": ("code",),
                "combo": ("op", "a", "b")}[self.kind]  # fmt: skip
        missing = [n for n in need if getattr(self, n) is None]
        if missing:
            raise ValueError(f"line {self.key}: kind {self.kind} needs {missing}")
        return self


class RatesFxMonitorSettings(BaseModel):
    """
    Purpose:
        The rates and RMB monitor's lines, percentile window, history start, staleness limit
        and the curve drawn on the page, read from `config/rates_fx_monitor.yaml`.

    Contract:
        Input:
            pct_years: int > 0; min_obs: int > 0; history_start: str (YYYYMMDD);
            stale_days: int > 0; curve: {curve: str, fields: list[str]};
            lines: list[RatesFxLine], unique keys, each combo naming earlier lines
        Output:
            frozen pydantic model; `load(repo_root)`
        Raises:
            pydantic.ValidationError  -- invalid values, duplicate keys, bad combo references

    Used by:
        cli.ReportCommands                 -- `rates-fx-monitor` command
        calculation.RatesFxSeriesReader    -- sources and history start
        calculation.RatesFxMonitorBuilder  -- lines and thresholds

    Test cases:
        TC-RFS-001  config/rates_fx_monitor.yaml loads; a combo without b, a curve without
                    field, an unknown unit and duplicate keys are refused; a combo naming an
                    unknown or later line is refused; a missing file gives no lines
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    pct_years: int = Field(default=5, gt=0)
    min_obs: int = Field(default=250, gt=0)
    history_start: str = "20210101"
    stale_days: int = Field(default=4, gt=0)
    curve: dict[str, str | list[str]] = Field(default_factory=dict)
    lines: list[RatesFxLine] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_lines(self) -> RatesFxMonitorSettings:
        seen: set[str] = set()
        for line in self.lines:
            if line.key in seen:
                raise ValueError(f"duplicate line key {line.key}")
            if line.kind == "combo" and not {line.a, line.b} <= seen:
                raise ValueError(f"line {line.key}: a and b must be earlier lines")
            seen.add(line.key)
        return self

    @classmethod
    def load(cls, repo_root: Path) -> RatesFxMonitorSettings:
        """
        Purpose:
            Read config/rates_fx_monitor.yaml under repo_root.

        Contract:
            Input:
                repo_root: Path
            Output:
                RatesFxMonitorSettings  -- no lines when the file is missing
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
