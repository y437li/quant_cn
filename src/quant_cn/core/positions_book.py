"""The user's holdings, one combined book (plan 15 phase 7d, D-132)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "local.positions.yaml"  # git-ignored by the config/local.*.yaml rule


class Position(BaseModel):
    """
    Purpose:
        One holding: shares and cost per share. Broker snapshot fields (last, market_value,
        floating_pnl) are accepted and ignored; values are recomputed from lake closes.

    Contract:
        Input:
            code:   str    -- ts_code, e.g. "002714.SZ"
            name:   str    -- display name; "" allowed
            shares: float  -- > 0
            cost:   float  -- >= 0, cost per share (CNY)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- non-positive shares, negative cost

    Used by:
        core.PositionsBook  -- rows of the book

    Test cases:
        TC-PB-001  the book loads; snapshot fields ignored; bad shares refused
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    code: str
    name: str = ""
    shares: float = Field(gt=0)
    cost: float = Field(ge=0)


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
        Output:
            frozen pydantic model; `load(repo_root)` -> PositionsBook, `list_codes()` -> list[str]
        Raises:
            pydantic.ValidationError  -- duplicate code, negative cash

    Used by:
        portfolio.HoldingsRiskBuilder  -- the book to value and decompose
        cli.ResearchCommands           -- `holdings-risk` command

    Test cases:
        TC-PB-001  the book loads; snapshot fields ignored; bad shares refused
        TC-PB-002  missing file -> empty book; duplicate code or broken YAML -> ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    as_of: str = ""
    cash: float = Field(default=0.0, ge=0)
    positions: list[Position] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_codes(self) -> PositionsBook:
        codes = self.list_codes()
        if len(codes) != len(set(codes)):
            raise ValueError(f"duplicate codes in the positions book: {sorted(codes)}")
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
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid positions book {path}: {exc}") from exc

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
