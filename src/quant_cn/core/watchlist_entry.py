"""The user's watchlist targets and the watchlist page settings (plan 15 phase 7, D-120)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WatchlistEntry(BaseModel):
    """
    Purpose:
        One stock the user watches and the price range at which they would buy it (D-120).

    Contract:
        Input:
            code:     str    -- ts_code, e.g. "002507.SZ"
            buy_low:  float  -- > 0, lower edge of the buy range (unadjusted price, CNY)
            buy_high: float  -- >= buy_low; equal to buy_low for a single target price
            added:    str    -- YYYYMMDD the target was set
            thesis:   str    -- why the stock is on the list; "" allowed
            watch:    str    -- signals to follow; "" allowed
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- non-positive price, buy_high < buy_low, extra keys

    Used by:
        core.Config                     -- field `watchlist`
        portfolio.WatchlistBuilder      -- rows of the watchlist document

    Test cases:
        TC-C-015  config/local.watchlist.yaml loads; missing file = []; buy_high < buy_low refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    buy_low: float = Field(gt=0)
    buy_high: float = Field(gt=0)
    added: str
    thesis: str = ""
    watch: str = ""

    @model_validator(mode="after")
    def _check_range(self) -> WatchlistEntry:
        if self.buy_high < self.buy_low:
            raise ValueError(f"{self.code}: buy_high {self.buy_high} < buy_low {self.buy_low}")
        return self


class WatchlistSettings(BaseModel):
    """
    Purpose:
        Thresholds and windows of the watchlist page (base.yaml `watchlist`, D-120).

    Contract:
        Input:
            near_pct:       float  -- in (0, 1); price within this share above buy_high = "near"
            history_days:   int    -- > 0; calendar days for the 52-week range and weekly line
            consensus_days: int    -- > 0; calendar days of report_rc forecasts in the consensus
        Output:
            frozen pydantic model; defaults 0.10 / 365 / 30
        Raises:
            pydantic.ValidationError  -- out-of-range values

    Used by:
        core.Config                 -- field `watchlist_settings`
        portfolio.WatchlistBuilder  -- thresholds and windows

    Test cases:
        TC-C-016  base.yaml watchlist section loads; missing section gives the defaults
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    near_pct: float = Field(default=0.10, gt=0, lt=1)
    history_days: int = Field(default=365, gt=0)
    consensus_days: int = Field(default=30, gt=0)
