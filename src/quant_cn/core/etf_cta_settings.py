"""Settings of the long-only ETF CTA book (plan 27, D-160)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "etf_cta.yaml"
CODE = r"^\d{6}\.(SH|SZ)$"
BONDS = "债券"  # name of the bond sleeve in views and the document


class EtfCtaGroup(BaseModel):
    """
    Purpose:
        One risk group of the book (股票, 黄金, 商品): its ETFs and their capital weights
        inside the group (an ETF joins once it has a price; weights renormalise over live ETFs).

    Contract:
        Input:
            name:    str               -- display name, unique in the settings
            members: dict[str, float]  -- ts_code -> inner weight > 0; at least one
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- empty members, bad ts_code, weight <= 0, extra keys

    Used by:
        core.EtfCtaSettings  -- field `groups`

    Test cases:
        TC-ECS-001  config/etf_cta.yaml loads; a missing file raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    members: dict[str, float] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_members(self) -> EtfCtaGroup:
        bad = [c for c, w in self.members.items() if not re.match(CODE, c) or w <= 0]
        if bad:
            raise ValueError(f"group {self.name}: bad members {bad}")
        return self


class EtfCtaPremium(BaseModel):
    """
    Purpose:
        The premium guard for QDII / LOF lines: close / unit NAV - 1 on the latest date with both.

    Contract:
        Input:
            codes:      list[str]  -- ts_codes guarded (161129.SZ)
            buy_below:  float      -- buy or add only below this premium (0.03)
            high:       float      -- 很高 at or above (0.10)
            switch:     float      -- flag the alternative at or above (0.20)
            alternative: dict[str, str]  -- guarded code -> lower-premium alternative ("" = none)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- thresholds not 0 < buy_below <= high <= switch

    Used by:
        core.EtfCtaSettings  -- field `premium`

    Test cases:
        TC-ECS-002  thresholds out of order are refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    codes: list[str] = Field(default_factory=list)
    buy_below: float = 0.03
    high: float = 0.10
    switch: float = 0.20
    alternative: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_order(self) -> EtfCtaPremium:
        if not 0 < self.buy_below <= self.high <= self.switch:
            raise ValueError("premium thresholds must be 0 < buy_below <= high <= switch")
        return self


class EtfCtaSettings(BaseModel):
    """
    Purpose:
        The ETF CTA book (D-160 update 2026-11-14): `risk_share` of capital across `groups` at
        equal risk (1 / vol, monthly), A股 ETFs scaled weekly by the trend position, `bond_share`
        in `bonds` scaled weekly by the bond trend switch, the rest in `cash`; weekly decisions
        with a per-ETF no-trade band and a premium guard.

    Contract:
        Input:
            groups:        list[EtfCtaGroup]  -- risk groups, equal risk budget
            risk_share:    float in (0, 1]    -- capital share of the groups (0.6)
            bonds:         dict[str, float]   -- bond ETFs and capital weights inside the sleeve
            bond_share:    float in [0, 1)    -- capital share of the bond sleeve (0.4)
            cash:          str                -- money-market ETF ts_code (required)
            timed:         list[str]          -- ETFs scaled by the trend position (A股)
            trend_windows: list[int]          -- sessions of the trend blend (10, 21, 42, 252)
            vol_target:    float > 0          -- size = min(1, vol_target / 60-day vol) (0.20)
            switch_windows: list[int]         -- sessions of the bond switch blend (21, 63, 252)
            vol_window:    int > 1            -- sessions of the vol estimates (60)
            vol_min_obs:   int > 1            -- fewest returns for a group vol (40)
            band:          float >= 0         -- no trade when |target - held| < band (0.02)
            cost:          float >= 0         -- cost per unit traded (0.0015)
            history_start: str YYYYMMDD       -- first day of the back-test record (required)
            paper_start:   str YYYYMMDD       -- first day of the paper book (required)
            group_step:    float > 0          -- flag a group weight change at or above (0.05)
            names:         dict[str, str]     -- ts_code -> short Chinese name for display
            premium:       EtfCtaPremium
            subsets:       dict[str, list[str]]  -- named ETF sets for views (A股, 港股, 5年, 30年)
            views_file:    str | None         -- repo-relative views file (git-ignored), None = none
        Output:
            frozen pydantic model; `list_codes()` -> every ETF the book can hold (cash last);
            `list_members(name)` -> the ETFs a view name stands for
        Raises:
            pydantic.ValidationError  -- shares above 100%, timed ETF outside the groups,
                                         an ETF in two places, duplicate group names, bad dates,
                                         a subset with an ETF outside the book or a clashing name

    Used by:
        portfolio.EtfCtaBook     -- reads the lake for list_codes() and builds the document
        portfolio.EtfCtaWeights  -- weights and overlays
        cli.ReportCommands       -- `etf-cta` loads it
        core.EtfCtaViews         -- list_members checks view targets
        portfolio.EtfCtaViewTilt -- list_members resolves view targets

    Test cases:
        TC-ECS-001  config/etf_cta.yaml loads; a missing file raises ConfigError
        TC-ECS-002  thresholds out of order are refused
        TC-ECS-003  shares above 100%, an ETF in two groups or a timed ETF outside are refused
        TC-ECS-004  list_members resolves groups, 债券, subsets and codes; unknown name raises;
                    a bad subset is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    groups: list[EtfCtaGroup] = Field(default_factory=list)
    risk_share: float = Field(default=0.6, gt=0, le=1)
    bonds: dict[str, float] = Field(default_factory=dict)
    bond_share: float = Field(default=0.4, ge=0, lt=1)
    cash: str = Field(pattern=CODE)
    timed: list[str] = Field(default_factory=list)
    trend_windows: list[int] = Field(default_factory=lambda: [10, 21, 42, 252], min_length=1)
    vol_target: float = Field(default=0.20, gt=0)
    switch_windows: list[int] = Field(default_factory=lambda: [21, 63, 252], min_length=1)
    vol_window: int = Field(default=60, gt=1)
    vol_min_obs: int = Field(default=40, gt=1)
    band: float = Field(default=0.02, ge=0)
    cost: float = Field(default=0.0015, ge=0)
    history_start: str = Field(pattern=r"^\d{8}$")
    paper_start: str = Field(pattern=r"^\d{8}$")
    group_step: float = Field(default=0.05, gt=0)
    names: dict[str, str] = Field(default_factory=dict)
    premium: EtfCtaPremium = Field(default_factory=EtfCtaPremium)
    subsets: dict[str, list[str]] = Field(default_factory=dict)
    views_file: str | None = None

    @model_validator(mode="after")
    def _check_book(self) -> EtfCtaSettings:
        if self.risk_share + self.bond_share > 1 + 1e-9:
            raise ValueError("risk_share + bond_share must not exceed 1")
        names = [g.name for g in self.groups]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate group names {names}")
        placed = [c for g in self.groups for c in g.members] + list(self.bonds) + [self.cash]
        if len(set(placed)) != len(placed):
            raise ValueError("an ETF appears in more than one group, the bonds or cash")
        grouped = {c for g in self.groups for c in g.members}
        if not set(self.timed) <= grouped:
            raise ValueError(f"timed ETFs outside the groups: {set(self.timed) - grouped}")
        held = grouped | set(self.bonds)
        for name, codes in self.subsets.items():
            if name in {*names, BONDS} or not codes or not set(codes) <= held:
                raise ValueError(f"subset {name}: clashing name or ETFs outside the book")
        return self

    def list_members(self, name: str) -> list[str]:
        """
        Purpose:
            The ETFs a view name stands for: a group name, 债券 (the bond sleeve), a subset
            name or one ts_code held by the book (not cash).

        Contract:
            Input:
                name: str
            Output:
                list[str]  -- ts_codes, at least one
            Raises:
                ConfigError  -- the name is none of these
        """
        found = {g.name: list(g.members) for g in self.groups} | {BONDS: list(self.bonds)}
        found |= self.subsets
        if name in found:
            return list(found[name])
        if name in self.list_codes()[:-1]:
            return [name]
        raise ConfigError(f"unknown ETF CTA view target {name!r}")

    def list_codes(self) -> list[str]:
        """
        Purpose:
            Every ETF the book can hold, groups first, then bonds, cash last.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- unique ts_codes
            Raises:
                (none)
        """
        return [c for g in self.groups for c in g.members] + list(self.bonds) + [self.cash]

    @classmethod
    def load(cls, repo_root: Path) -> EtfCtaSettings:
        """
        Purpose:
            Read `<repo_root>/config/etf_cta.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                EtfCtaSettings
            Raises:
                ConfigError  -- missing file, unreadable YAML or invalid content
        """
        path = repo_root / FILE
        if not path.exists():
            raise ConfigError(f"missing ETF CTA settings {path}")
        try:
            return cls(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid ETF CTA settings {path}: {exc}") from exc
