"""Settings of the opportunity-discovery pipeline (plan 16, D-121)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DiscoverySettings(BaseModel):
    """
    Purpose:
        Thresholds and windows of the discovery pipeline, read from base.yaml `discovery` (D-121).

    Contract:
        Input:
            history_years: int  -- annual reports used for the cycle norm (10-year median profit,
                                   max margin); 3..30
            min_years:     int  -- fewer annual reports than this -> cycle columns are NaN; >= 2
            normal_pe:     float -- PE of normal (10-year median) profit, primary base of years
                                    priced (D-121); 4..40
            discount_rate: float -- excess-profit and reverse-DCF discount rate; 0.02..0.25
            dcf_years:     int  -- reverse-DCF years before the normal-PE exit; 3..20
            max_years:     float -- years priced above this are reported as this cap; 10..200
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- out-of-range values, extra keys

    Used by:
        core.Config                       -- field `discovery`
        calculation.CompanyCyclePanel     -- history window
        calculation.ImpliedExpectations   -- normal PE, discount rate, DCF horizon, years cap

    Test cases:
        TC-C-017  base.yaml discovery section loads; missing section gives the defaults
        TC-C-018  implied-expectation keys load with defaults and bounds
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    history_years: int = Field(default=10, ge=3, le=30)
    min_years: int = Field(default=5, ge=2)
    normal_pe: float = Field(default=12.0, ge=4, le=40)
    discount_rate: float = Field(default=0.09, ge=0.02, le=0.25)
    dcf_years: int = Field(default=10, ge=3, le=20)
    max_years: float = Field(default=50.0, ge=10, le=200)
