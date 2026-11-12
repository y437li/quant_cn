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
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- invalid regular expression, empty name, extra keys

    Used by:
        core.EtfProxySettings  -- field `indices`

    Test cases:
        TC-C-020  config/etf_proxies.yaml loads; missing file gives empty settings; a bad regex
                  is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    benchmark: str = Field(min_length=1)
    reference: str = Field(min_length=1)

    @field_validator("benchmark")
    @classmethod
    def _check_pattern(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"benchmark pattern {value!r}: {exc}") from exc
        return value


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
            name_contains:      str        -- an ETF's name must contain it ("ETF")
            name_excludes:      list[str]  -- names with any of these are dropped (feeder, enhanced)
            benchmark_contains: str        -- benchmark must contain it (default: the
                                              multiplication sign + "100%", pure trackers)
        Output:
            frozen pydantic model; default = no indices (the builder then writes an empty document)
        Raises:
            pydantic.ValidationError  -- duplicate index names, bad start, extra keys

    Used by:
        core.Config                  -- field `etf_proxy`
        portfolio.EtfProxyBuilder    -- start and window
        portfolio.EtfFlowCalculator  -- indices, core list and member rules

    Test cases:
        TC-C-020  (see EtfProxyIndex)
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: str = Field(default="20220101", pattern=r"^\d{8}$")
    core: list[str] = Field(default_factory=list)
    indices: list[EtfProxyIndex] = Field(default_factory=list)
    recent_days: int = Field(default=20, gt=0)
    name_contains: str = "ETF"
    name_excludes: list[str] = Field(default_factory=lambda: ["联接", "增强"])
    benchmark_contains: str = "\u00d7100%"

    @model_validator(mode="after")
    def _check_names(self) -> EtfProxySettings:
        names = [i.name for i in self.indices]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate index names in etf_proxies: {names}")
        return self
