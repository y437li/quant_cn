"""Settings of the sector earnings-season top signal (财报季信号, plan 35, D-172)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "sector_earnings_signal.yaml"


class SectorEarningsSignalSettings(BaseModel):
    """
    Purpose:
        Windows and thresholds of the earnings events and the sector top signal, read from
        `config/sector_earnings_signal.yaml` (plan 35, D-172).

    Contract:
        Input:
            start: str YYYYMMDD; sue_window, sue_min: int > 0; top_decile: int 0..9;
            min_events: int > 0; pre_window, react_window, back_window: int > 0;
            fwd_windows: list[int > 0]; report_share: float in (0, 1]; pre_min, react_max,
            rally_min: float (%); max_abs_log_return: float > 0; history_quarters: int > 0;
            exclude_exchanges: list[str] (ts_code suffixes)
        Output:
            frozen pydantic model; `load(repo_root)`
        Raises:
            pydantic.ValidationError  -- out-of-range values or extra keys

    Used by:
        calculation.EarningsEventBuilder       -- SUE and event windows
        portfolio.SectorEarningsSignalBuilder  -- sector thresholds
        cli.AppServiceBuilder                  -- `build_sector_earnings_signal`

    Test cases:
        TC-SES-001  config/sector_earnings_signal.yaml loads with the D-172 values; a missing
                    file gives the defaults; an unknown key or report_share 0 is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    start: str = "20190101"
    sue_window: int = Field(default=8, gt=0)
    sue_min: int = Field(default=4, gt=0)
    top_decile: int = Field(default=8, ge=0, le=9)
    min_events: int = Field(default=5, gt=0)
    pre_window: int = Field(default=60, gt=0)
    react_window: int = Field(default=1, ge=0)
    back_window: int = Field(default=120, gt=0)
    fwd_windows: list[int] = Field(default_factory=lambda: [60, 120])
    report_share: float = Field(default=0.8, gt=0, le=1)
    pre_min: float = 15.0
    react_max: float = 1.0
    rally_min: float = 20.0
    max_abs_log_return: float = Field(default=0.25, gt=0)
    history_quarters: int = Field(default=8, gt=0)
    exclude_exchanges: list[str] = Field(default_factory=lambda: ["BJ"])

    @classmethod
    def load(cls, repo_root: Path) -> SectorEarningsSignalSettings:
        """
        Purpose:
            Read config/sector_earnings_signal.yaml under repo_root.

        Contract:
            Input:
                repo_root: Path
            Output:
                SectorEarningsSignalSettings  -- defaults when the file is missing
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
