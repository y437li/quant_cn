"""Settings of the small-cap bottom watch (小盘观察, plan 30)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "smallcap_watch.yaml"
LOCAL_FILE = Path("config") / "local.smallcap_watch.yaml"


class WatchIndex(BaseModel):
    """
    Purpose:
        One index of the watch: ts_code in curated.index_daily and its Chinese name.

    Contract:
        Input:
            code: str (ts_code); name: str
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing field, extra keys

    Used by:
        core.SmallCapWatchSettings  -- fields small_index, large_index, star_index

    Test cases:
        TC-SCS-001  config/smallcap_watch.yaml loads with its three indices and 11 ETFs
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    code: str
    name: str


class WatchEtf(BaseModel):
    """
    Purpose:
        One broad ETF in the flow total; `own_row` also gives it its own row.

    Contract:
        Input:
            code: str (ts_code); name: str; own_row: bool (default False)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing field, extra keys

    Used by:
        core.SmallCapWatchSettings  -- field etfs

    Test cases:
        TC-SCS-001  config/smallcap_watch.yaml loads with its three indices and 11 ETFs
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    code: str
    name: str
    own_row: bool = False


class MarginEpisode(BaseModel):
    """
    Purpose:
        One past 融资余额 去杠杆 episode (month-end high to trough, research
        20261119_margin_drawdown), shown beside the current depth (plan 30 ph7).

    Contract:
        Input:
            name: str; depth: float in (-1, 0) (trough / high - 1); months: int > 0
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing field, extra keys, depth outside (-1, 0)

    Used by:
        core.SmallCapWatchSettings  -- field margin_episodes

    Test cases:
        TC-SCS-005  config/smallcap_watch.yaml loads four episodes; depth 0 is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    name: str
    depth: float = Field(gt=-1, lt=0)
    months: int = Field(gt=0)


class SmallCapWatchSettings(BaseModel):
    """
    Purpose:
        Indices, user levels, triggers and windows of the small-cap bottom watch, read from
        `config/smallcap_watch.yaml` with the git-ignored `config/local.smallcap_watch.yaml`
        overriding it key by key (the user's index levels are personal).

    Contract:
        Input:
            small_index, large_index, star_index: WatchIndex; levels: list[float > 0];
            panic_limit_downs: int > 0; low_window, ma_window, vol_window, pct_window,
            pct_min_obs, history, flow_days: int > 0; low_share_trigger, vol_pct_trigger,
            gap_entry_pct, gap_exit_pct, near_share, near_pct, near_level: float in (0, 1);
            gap_exit_pct < gap_entry_pct;
            etfs: list[WatchEtf] with unique codes;
            margin_dd_trigger: float in (-1, 0) -- financing balance drawdown from its
                margin_high_days high at or below which a margin_turn_days change >= 0 is 企稳;
            margin_turn_days, margin_ma_days: int > 0; margin_high_days: int > 1 (ph4);
            selloff_drop, selloff_near_drop: float in (-1, 0), near above drop -- 中证1000
                daily return at or below which a day with turnover >= selloff_turnover x its
                prior turnover_window mean is 放量大跌 (near at selloff_near_drop and
                selloff_near_turnover); selloff_turnover, selloff_near_turnover: float > 0;
            turnover_window: int > 0; entry_since: str YYYYMMDD | None -- start of the
                建仓档 group (None: no group); entry_bought: int in [0, 3] steps bought (ph5);
            margin_long_start: str YYYYMMDD -- first day of the weekly share chart (ph6);
            margin_episodes: list[MarginEpisode]; margin_speed_span: int > 0 (EMA span of the
                daily balance change); margin_acc_days: int > 0 (acceleration = change of the
                smoothed speed over this many sessions / days); margin_flat_speed: float > 0
                (亿 per day: |speed| at or below it is 走平) (ph7)
        Output:
            frozen pydantic model; `load(repo_root)`
        Raises:
            pydantic.ValidationError  -- missing index, invalid values, duplicate ETF codes,
                                         exit >= entry

    Used by:
        portfolio.SmallCapWatchBuilder  -- windows, indices, ETFs and margin pace (ph7)
        portfolio.SmallCapWatchRows     -- triggers, near rules, row names, episodes (ph7)
        portfolio.SmallCapEntryRows     -- 放量大跌 and 建仓档 fields (ph5)
        cli.ReportCommands              -- `smallcap-watch` command

    Test cases:
        TC-SCS-001  config/smallcap_watch.yaml loads with its three indices and 11 ETFs
        TC-SCS-002  the local file overrides `levels`; missing files raise ConfigError (the
                    indices have no defaults)
        TC-SCS-003  duplicate ETF codes, gap_exit_pct >= gap_entry_pct, near_share 1.5 and a
                    non-positive level are refused; bad YAML raises ConfigError
        TC-SCS-004  ph5: selloff_near_drop below selloff_drop, a bad entry_since and
                    entry_bought 4 are refused; defaults give no 建仓档 group
        TC-SCS-005  ph7: config/smallcap_watch.yaml loads four episodes; depth 0 and
                    margin_flat_speed 0 are refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    small_index: WatchIndex
    large_index: WatchIndex
    star_index: WatchIndex
    levels: list[float] = []
    panic_limit_downs: int = Field(default=500, gt=0)
    low_window: int = Field(default=60, gt=0)
    low_share_trigger: float = Field(default=0.70, gt=0, lt=1)
    ma_window: int = Field(default=20, gt=0)
    vol_window: int = Field(default=20, gt=0)
    pct_window: int = Field(default=750, gt=0)
    pct_min_obs: int = Field(default=250, gt=0)
    vol_pct_trigger: float = Field(default=0.90, gt=0, lt=1)
    gap_entry_pct: float = Field(default=0.90, gt=0, lt=1)
    gap_exit_pct: float = Field(default=0.70, gt=0, lt=1)
    near_share: float = Field(default=0.8, gt=0, lt=1)
    near_pct: float = Field(default=0.05, gt=0, lt=1)
    near_level: float = Field(default=0.03, gt=0, lt=1)
    history: int = Field(default=250, gt=0)
    flow_days: int = Field(default=5, gt=0)
    etfs: list[WatchEtf] = []
    margin_dd_trigger: float = Field(default=-0.10, gt=-1, lt=0)
    margin_turn_days: int = Field(default=5, gt=0)
    margin_high_days: int = Field(default=250, gt=1)
    margin_ma_days: int = Field(default=20, gt=0)
    selloff_drop: float = Field(default=-0.03, gt=-1, lt=0)
    selloff_turnover: float = Field(default=1.3, gt=0)
    selloff_near_drop: float = Field(default=-0.02, gt=-1, lt=0)
    selloff_near_turnover: float = Field(default=1.0, gt=0)
    turnover_window: int = Field(default=20, gt=0)
    entry_since: str | None = Field(default=None, pattern=r"^\d{8}$")
    entry_bought: int = Field(default=0, ge=0, le=3)
    margin_long_start: str = Field(default="20190101", pattern=r"^\d{8}$")
    margin_episodes: list[MarginEpisode] = []
    margin_speed_span: int = Field(default=10, gt=0)
    margin_acc_days: int = Field(default=5, gt=0)
    margin_flat_speed: float = Field(default=20.0, gt=0)

    @model_validator(mode="after")
    def _check(self) -> SmallCapWatchSettings:
        codes = [e.code for e in self.etfs]
        if len(codes) != len(set(codes)):
            raise ValueError(f"duplicate ETF codes: {codes}")
        if self.gap_exit_pct >= self.gap_entry_pct:
            raise ValueError("gap_exit_pct must be below gap_entry_pct")
        if any(level <= 0 for level in self.levels):
            raise ValueError(f"levels must be positive: {self.levels}")
        if self.selloff_near_drop <= self.selloff_drop:
            raise ValueError("selloff_near_drop must be above selloff_drop")
        return self

    @classmethod
    def load(cls, repo_root: Path) -> SmallCapWatchSettings:
        """
        Purpose:
            Read `config/smallcap_watch.yaml`, then apply `config/local.smallcap_watch.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                SmallCapWatchSettings
            Raises:
                ConfigError  -- unreadable YAML, invalid content, or no file (indices missing)
        """
        merged: dict[str, Any] = {}
        for name in (FILE, LOCAL_FILE):
            path = repo_root / name
            if not path.exists():
                continue
            try:
                merged |= yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except (yaml.YAMLError, TypeError) as exc:
                raise ConfigError(f"invalid small-cap watch settings {path}: {exc}") from exc
        try:
            return cls(**merged)
        except (ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid small-cap watch settings: {exc}") from exc
