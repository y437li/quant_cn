"""Settings of the sector monitor (#sector-monitor, plan 31)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "sector_monitors.yaml"
Metric = Literal[
    "house_price_second_hand", "house_price_new", "contracted_sales", "land_intensity",
    "contract_liab", "impairment", "dividend", "winner_rate", "realized_vol",
    "game_approvals", "revenue_q", "selling_ratio", "app_rank", "sales_yoy",
    "house_price_breadth", "valuation", "revision", "surveys",
]  # fmt: skip


class MonitoredSecurity(BaseModel):
    """
    Purpose:
        One company or index of a monitored sector: ts_code and Chinese name.

    Contract:
        Input:
            code: str (ts_code); name: str
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing field, extra keys

    Used by:
        core.MonitoredSector  -- fields index, companies

    Test cases:
        TC-SMS-001  config/sector_monitors.yaml loads: two sectors, six companies each
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    code: str
    name: str


class MonitoredSector(BaseModel):
    """
    Purpose:
        One sector of the monitor: key, name, Shenwan index, companies and the charts (Metric
        keys) shown for it.

    Contract:
        Input:
            key: str; name: str; index: MonitoredSecurity; companies: list (>= 1);
            metrics: list[Metric] (>= 1); valuation: "pb" | "pe_ttm" (default "pb", plan 33)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- unknown metric, empty lists, extra keys

    Used by:
        portfolio.SectorMonitorBuilder  -- one sector's document
        core.SectorMonitorSettings  -- field sectors

    Test cases:
        TC-SMS-002  an unknown metric key or an empty company list raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str
    name: str
    index: MonitoredSecurity
    companies: list[MonitoredSecurity] = Field(min_length=1)
    metrics: list[Metric] = Field(min_length=1)
    valuation: Literal["pb", "pe_ttm"] = "pb"


class SectorMonitorSettings(BaseModel):
    """
    Purpose:
        Everything the sector monitor reads from `config/sector_monitors.yaml` (plan 31 ph4,
        D-168): the 70-city tier lists (cities not listed form 三线), realised-vol windows and
        percentile window, chart lengths and the monitored sectors.

    Contract:
        Input:
            tiers: dict[str, list[str]]; vol_windows: list[int > 1]; pct_window,
            pct_min_obs, history_sessions, history_quarters, history_months: int > 0;
            app_country: str (App Store home market, default "cn"); app_top: int > 0 (home
            grossing list length, default 20); new_game_days: int > 0 (default 90);
            val_window, val_min_obs (valuation percentile, default 1250 / 250), revision_days,
            survey_days: int > 0 (default 90, plan 33, D-170);
            sectors: list[MonitoredSector] (>= 1)
        Output:
            frozen pydantic model; `load(repo_root)` (classmethod)
        Raises:
            ConfigError  -- unreadable YAML, invalid content or a missing file

    Used by:
        portfolio.SectorMonitorBuilder  -- every setting
        portfolio.SectorMetricReader  -- tiers and chart lengths
        portfolio.AppRankReader  -- app_country, app_top
        portfolio.MarketSignalReader  -- windows and history lengths
        cli.AppServiceBuilder  -- `build_sector_monitor` loads it

    Test cases:
        TC-SMS-001  config/sector_monitors.yaml loads: two sectors, six companies each
        TC-SMS-002  an unknown metric key or an empty company list raises ConfigError;
                    a missing file raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    tiers: dict[str, list[str]]
    vol_windows: list[int] = Field(min_length=1)
    pct_window: int = Field(gt=0)
    pct_min_obs: int = Field(gt=0)
    history_sessions: int = Field(gt=0)
    history_quarters: int = Field(gt=0)
    history_months: int = Field(gt=0)
    app_country: str = "cn"
    app_top: int = Field(default=20, gt=0)
    new_game_days: int = Field(default=90, gt=0)
    val_window: int = Field(default=1250, gt=0)
    val_min_obs: int = Field(default=250, gt=0)
    revision_days: int = Field(default=90, gt=0)
    survey_days: int = Field(default=90, gt=0)
    sectors: list[MonitoredSector] = Field(min_length=1)

    @classmethod
    def load(cls, repo_root: Path) -> SectorMonitorSettings:
        """
        Purpose:
            Read `config/sector_monitors.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                SectorMonitorSettings
            Raises:
                ConfigError  -- unreadable YAML, invalid content or no file
        """
        path = repo_root / FILE
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return cls(**raw)
        except (OSError, yaml.YAMLError, TypeError, ValidationError) as exc:
            raise ConfigError(f"invalid sector monitor settings {path}: {exc}") from exc
