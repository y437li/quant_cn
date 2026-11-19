"""Settings of the national-team ETF proxy (plan 15 phase 7b, D-126)."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EtfProxyIndex(BaseModel):
    """
    Purpose:
        One broad index whose ETFs are summed into the proxy, and how its ETFs are found.

    Contract:
        Input:
            name:      str  -- display name, e.g. "沪深300"; unique within the settings
            benchmark: str  -- regular expression searched in `fund_basic.benchmark`
            reference: str  -- ts_code of the ETF whose price deflates positions (the largest)
            exclude:   str  -- regular expression; a benchmark matching it is skipped ("" = none)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- invalid regular expression, empty name, extra keys

    Used by:
        core.EtfProxySettings  -- field `indices`
        core.EtfProxyStyle     -- subclass

    Test cases:
        TC-C-020  config/etf_proxies.yaml loads; missing file gives empty settings; a bad regex
                  is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    benchmark: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    exclude: str = ""

    @field_validator("benchmark", "exclude")
    @classmethod
    def _check_pattern(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"benchmark pattern {value!r}: {exc}") from exc
        return value


class EtfProxyStyle(EtfProxyIndex):
    """
    Purpose:
        A style group of ETFs (银行, 红利) whose flows are watched for crowding, kept apart from
        the national-team core / other totals (plan 15 ph7g).

    Contract:
        Input:
            key: str  -- lower-case id; the condition metric is "<key>_etf_z" (e.g. bank_etf_z)
            plus the EtfProxyIndex fields (name, benchmark, reference, exclude)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- bad key or regex, extra keys

    Used by:
        core.EtfProxySettings      -- field `styles`

    Test cases:
        TC-C-021  styles load with keys; a style ETF is never a core / other member
    """

    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")


class EtfProxySettings(BaseModel):
    """
    Purpose:
        Which ETFs make up the national-team proxy and how far back it is built (D-126).

    Contract:
        Input:
            start:       str                  -- YYYYMMDD, first day of the output series
            core:        list[str]            -- ts_codes counted as the national-team proxy
            indices:     list[EtfProxyIndex]  -- tried in order; the first matching pattern wins
            recent_days: int                  -- > 0; trading days listed one by one
            rhythm_weeks: int                 -- > 0; weeks summed into each index's recent
                                                 flow column (5)
            pct_window_days: int > 1          -- sessions the 近3月 position percentile and
                                                 range are measured over (63, ph7o)
            matrix_weeks: int > 0             -- weeks shown in the per-index weekly flow
                                                 matrix (14, ph7o)
            name_contains:      str        -- an ETF's name must contain it ("ETF")
            name_excludes:      list[str]  -- names with any of these are dropped (feeder, enhanced)
            benchmark_contains: str        -- benchmark must contain it (default: the
                                              multiplication sign + "100%", pure trackers)
            styles:      list[EtfProxyStyle]  -- style groups watched for crowding (ph7g)
            style_window: int > 0      -- sessions summed into the flow (20)
            style_z_days: int > 1      -- past sessions the z-score is measured against (250)
            style_hot_z:  float > 0    -- z at or above which a style is 过热 (1.5)
        Output:
            frozen pydantic model; default = no indices (the builder then writes an empty document)
        Raises:
            pydantic.ValidationError  -- duplicate index names, bad start, extra keys

    Used by:
        core.Config                  -- field `etf_proxy`
        portfolio.EtfProxyBuilder    -- start and window
        portfolio.EtfFlowCalculator  -- indices, core list and member rules
        portfolio.EtfStyleHeat       -- styles and their windows

    Test cases:
        TC-C-020  (see EtfProxyIndex)
        TC-C-021  repo YAML loads styles and the ph7o windows (rhythm 4, 近3月 63, matrix 14)
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: str = Field(default="20220101", pattern=r"^\d{8}$")
    core: list[str] = Field(default_factory=list)
    indices: list[EtfProxyIndex] = Field(default_factory=list)
    recent_days: int = Field(default=20, gt=0)
    rhythm_weeks: int = Field(default=5, gt=0)
    pct_window_days: int = Field(default=63, gt=1)
    matrix_weeks: int = Field(default=14, gt=0)
    name_contains: str = "ETF"
    name_excludes: list[str] = Field(default_factory=lambda: ["联接", "增强"])
    benchmark_contains: str = "\u00d7100%"
    styles: list[EtfProxyStyle] = Field(default_factory=list)
    style_window: int = Field(default=20, gt=0)
    style_z_days: int = Field(default=250, gt=1)
    style_hot_z: float = Field(default=1.5, gt=0)

    @model_validator(mode="after")
    def _check_names(self) -> EtfProxySettings:
        names = [i.name for i in self.indices]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate index names in etf_proxies: {names}")
        return self
