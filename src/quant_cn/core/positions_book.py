"""The user's holdings as one combined book, with per-position notes and size rules (ph7d, 7f)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.condition import Condition
from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "local.positions.yaml"  # git-ignored by the config/local.*.yaml rule


class Position(BaseModel):
    """
    Purpose:
        One holding: shares and cost per share. Broker snapshot fields (last, market_value,
        floating_pnl) are accepted and ignored; values are recomputed from lake closes. After a
        partial sell the cost is the diluted cost (摊薄成本, D-166), so the realised P&L of a
        still-held stock stays in its floating P&L; it may be zero or negative once paid back.

    Contract:
        Input:
            code:   str    -- ts_code, e.g. "002714.SZ"
            name:   str    -- display name; "" allowed
            shares: float  -- > 0
            cost:   float  -- cost per share (CNY), diluted; <= 0 allowed (paid back)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- non-positive shares

    Used by:
        core.PositionsBook  -- rows of the book

    Test cases:
        TC-PB-001  the book loads; snapshot fields ignored; bad shares refused; negative cost
                   accepted
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    code: str
    name: str = ""
    shares: float = Field(gt=0)
    cost: float


class PositionNote(BaseModel):
    """
    Purpose:
        Why a position is held and what would make the user act: thesis, falsifier, stop and
        target prices, the planned action, what to watch, the last review date and structured
        conditions (plan 15 ph7f).

    Contract:
        Input:
            thesis, falsifier, action, watch: str  -- "" allowed
            stop:       float | None  -- > 0; close at or below it = stop flag
            target:     float | None  -- > 0; close at or above it = target flag
            reviewed:   str           -- YYYYMMDD of the last review; "" = never
            conditions: list[Condition]
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- non-positive stop / target, bad condition, extra keys

    Used by:
        core.PositionsBook           -- `notes`, `closed`
        portfolio.PositionReviewer   -- note, flags and conditions per position

    Test cases:
        TC-PB-003  notes and rules load; a note for a code not held is refused; old YAML loads
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    thesis: str = ""
    falsifier: str = ""
    stop: float | None = Field(default=None, gt=0)
    target: float | None = Field(default=None, gt=0)
    action: str = ""
    watch: str = ""
    reviewed: str = ""
    conditions: list[Condition] = Field(default_factory=list)


class BookRules(BaseModel):
    """
    Purpose:
        Position-size and process rules of the book: single-name weight cap with named
        exceptions, the checklist before any buy, and the review interval.

    Contract:
        Input:
            max_weight:        float      -- in (0, 1]
            weight_exceptions: list[str]  -- codes allowed above max_weight
            before_buy:        list[str]  -- checklist items, e.g. thesis, falsifier, stop
            review_every_days: int        -- > 0
        Output:
            frozen pydantic model; defaults 0.20 / [] / [] / 30
        Raises:
            pydantic.ValidationError  -- out-of-range values, extra keys

    Used by:
        core.PositionsBook           -- `rules`

    Test cases:
        TC-PB-003  notes and rules load; a note for a code not held is refused; old YAML loads
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_weight: float = Field(default=0.20, gt=0, le=1)
    weight_exceptions: list[str] = Field(default_factory=list)
    before_buy: list[str] = Field(default_factory=list)
    review_every_days: int = Field(default=30, gt=0)


class PositionsBook(BaseModel):
    """
    Purpose:
        The user's holdings as one combined book (the two broker accounts are managed together):
        cash and positions, read from `config/local.positions.yaml`. It is loaded here, not by
        core.Config, because config.py is at its size limit (§2.6).

    Contract:
        Input:
            as_of:     str             -- YYYYMMDD of the broker snapshot
            cash:      float           -- >= 0, CNY
            positions: list[Position]  -- codes unique
            notes:     dict[str, PositionNote]  -- keyed by a held code (plan 15 ph7f)
            closed:    dict[str, PositionNote]  -- notes of sold positions, kept for history
            rules:     BookRules
        Output:
            frozen pydantic model; `load(repo_root)` -> PositionsBook, `list_codes()` -> list[str]
        Raises:
            pydantic.ValidationError  -- duplicate code, negative cash, note for a code not held

    Used by:
        portfolio.OpportunityScreen  -- held codes excluded, fit weights
        cli.GaugeCommands  -- loads it
        portfolio.HoldingsRiskBuilder  -- the book to value and decompose
        cli.ResearchCommands           -- `holdings-risk` command
        core.docs.ContractLinter      -- held codes for the research privacy check
        cli.AppServiceBuilder  -- wires it
        portfolio.PositionReviewer  -- notes and rules
        cli.ReportCommands  -- held codes for `buyback-events`

    Test cases:
        TC-PB-001  the book loads; snapshot fields ignored; bad shares refused
        TC-PB-002  missing file -> empty book; duplicate code or broken YAML -> ConfigError
        TC-PB-003  notes and rules load; a note for a code not held is refused; old YAML loads
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    as_of: str = ""
    cash: float = Field(default=0.0, ge=0)
    positions: list[Position] = Field(default_factory=list)
    notes: dict[str, PositionNote] = Field(default_factory=dict)
    closed: dict[str, PositionNote] = Field(default_factory=dict)
    rules: BookRules = Field(default_factory=BookRules)

    @model_validator(mode="after")
    def _check_codes(self) -> PositionsBook:
        codes = self.list_codes()
        if len(codes) != len(set(codes)):
            raise ValueError(f"duplicate codes in the positions book: {sorted(codes)}")
        stray = sorted(set(self.notes) - set(codes))
        if stray:
            raise ValueError(f"notes for codes not held (move them to `closed`): {stray}")
        return self

    @classmethod
    def load(cls, repo_root: Path) -> PositionsBook:
        """
        Purpose:
            Read the book from `<repo_root>/config/local.positions.yaml`.

        Contract:
            Input:
                repo_root: Path  -- repository root
            Output:
                PositionsBook  -- empty when the file does not exist
            Raises:
                ConfigError  -- unreadable YAML or invalid content
        """
        path = repo_root / FILE
        if not path.exists():
            return cls()
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return cls(**data)
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid positions book {path}: {exc}") from exc
        except (ValidationError, TypeError) as exc:  # messages only: never echo private values
            raise ConfigError(f"invalid positions book {path}: {cls._format_errors(exc)}") from None

    def list_codes(self) -> list[str]:
        """
        Purpose:
            The ts_codes held, in file order.

        Contract:
            Input:
                (none)
            Output:
                list[str]
            Raises:
                (none)
        """
        return [p.code for p in self.positions]

    @staticmethod
    def _format_errors(exc: Exception) -> str:
        if isinstance(exc, ValidationError):
            return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return type(exc).__name__
