"""Settings of company guidance tracking (plan 18, D-124)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GuidanceSettings(BaseModel):
    """
    Purpose:
        Windows and minimum sample of guidance tracking, read from base.yaml `guidance` (D-124).

    Contract:
        Input:
            history_start: str  -- YYYYMMDD; first period end tracked (earnings previews since 2018)
            window_years:  int  -- track record uses period ends within this many years before
                                   as_of; 1..20
            min_outcomes:  int  -- fewer scored periods than this -> track record `sufficient`
                                   False; >= 1
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- out-of-range values, malformed date, extra keys

    Used by:
        core.Config                    -- field `guidance`
        calculation.ForecastTracker    -- history start, window, minimum sample

    Test cases:
        TC-C-019  base.yaml guidance section loads; missing section gives the defaults; bounds
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    history_start: str = Field(default="20180101", pattern=r"^\d{8}$")
    window_years: int = Field(default=3, ge=1, le=20)
    min_outcomes: int = Field(default=3, ge=1)
