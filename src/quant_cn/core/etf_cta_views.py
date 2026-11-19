"""The user's views on the ETF CTA book: bounded tilts, git-ignored file (plan 27 ph5, D-163)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_cta_settings import CODE, EtfCtaSettings
from quant_cn.core.exceptions import ConfigError

MAX_DAYS = 92  # longest life of a view
MAX_POINTS = 0.05  # largest capital move of one relative view
LOW, HIGH = 0.5, 2.0  # multiplier bounds


class EtfCtaWhen(BaseModel):
    """
    Purpose:
        Price condition of a view: the view waits until an ETF closes below (or above) a level
        on a decision date, then stays on until it expires.

    Contract:
        Input:
            code:  str           -- ts_code whose close is checked
            below: float | None  -- level > 0; exactly one of below / above
            above: float | None
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- bad code, both or neither level, level <= 0

    Used by:
        core.EtfCtaView  -- field `when`

    Test cases:
        TC-ECV-002  bad multiplier, points, expiry, condition or missing fields are refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(pattern=CODE)
    below: float | None = Field(default=None, gt=0)
    above: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _check_level(self) -> EtfCtaWhen:
        if (self.below is None) == (self.above is None):
            raise ValueError("a condition needs exactly one of below / above")
        return self


class EtfCtaView(BaseModel):
    """
    Purpose:
        One view. kind `scale`: multiply the weight of `target` (a group, 债券, a subset or an
        ETF) by `multiplier`. kind `relative`: move `points` of capital from `under` to `over`.
        Both need a reason, a start and an expiry at most 92 days after the start; `when` is an
        optional price condition.

    Contract:
        Input:
            kind:       "scale" | "relative"
            target:     str | None    -- scale only
            multiplier: float | None  -- scale only, 0.5..2
            over, under: str | None   -- relative only, different names
            points:     float | None  -- relative only, (0, 0.05]
            when:       EtfCtaWhen | None
            reason:     str           -- non-empty
            start, expires: str YYYYMMDD  -- start <= expires <= start + 92 days
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- fields missing for the kind or out of bounds

    Used by:
        core.EtfCtaViews          -- field `views`
        portfolio.EtfCtaViewTilt  -- reads each view

    Test cases:
        TC-ECV-002  bad multiplier, points, expiry, condition or missing fields are refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["scale", "relative"]
    target: str | None = None
    multiplier: float | None = Field(default=None, ge=LOW, le=HIGH)
    over: str | None = None
    under: str | None = None
    points: float | None = Field(default=None, gt=0, le=MAX_POINTS)
    when: EtfCtaWhen | None = None
    reason: str = Field(min_length=1)
    start: str = Field(pattern=r"^\d{8}$")
    expires: str = Field(pattern=r"^\d{8}$")

    @model_validator(mode="after")
    def _check_view(self) -> EtfCtaView:
        if self.kind == "scale" and (self.target is None or self.multiplier is None):
            raise ValueError("a scale view needs target and multiplier")
        relative = (self.over, self.under, self.points)
        if self.kind == "relative" and (None in relative or self.over == self.under):
            raise ValueError("a relative view needs different over / under and points")
        codec = DateCodec()
        days = (codec.to_date(self.expires) - codec.to_date(self.start)).days
        if not 0 <= days <= MAX_DAYS:
            raise ValueError(f"expires must be 0..{MAX_DAYS} days after start")
        return self

    def list_names(self) -> list[str]:
        """
        Purpose:
            The set names this view refers to (target, or over and under; plus the condition
            code).

        Contract:
            Input:
                (none)
            Output:
                list[str]
            Raises:
                (none)
        """
        names = [self.target] if self.kind == "scale" else [self.over, self.under]
        return [n for n in names if n is not None] + ([self.when.code] if self.when else [])


class EtfCtaViews(BaseModel):
    """
    Purpose:
        All views of the user (D-163): the list and an optional A股 floor (keep at least this
        share of the untimed A股 weight when the trend position is lower). Lives in the
        git-ignored `views_file` of the settings; a missing file means no views.

    Contract:
        Input:
            views:         list[EtfCtaView]
            a_share_floor: float | None  -- 0..1, None = no floor
        Output:
            frozen pydantic model; `load(repo_root, settings)` -> EtfCtaViews
        Raises:
            pydantic.ValidationError  -- as the fields

    Used by:
        portfolio.EtfCtaViewTilt  -- applies the views
        portfolio.EtfCtaBook      -- the 含观点 track
        cli.ReportCommands        -- `etf-cta` loads it

    Test cases:
        TC-ECV-001  a missing file or no views_file gives no views; a file loads
        TC-ECV-002  bad multiplier, points, expiry, condition or missing fields are refused
        TC-ECV-003  an unknown target or condition code, or bad YAML, raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    views: list[EtfCtaView] = Field(default_factory=list)
    a_share_floor: float | None = Field(default=None, ge=0, le=1)

    @classmethod
    def load(cls, repo_root: Path, settings: EtfCtaSettings) -> EtfCtaViews:
        """
        Purpose:
            Read `<repo_root>/<settings.views_file>` and check every name against the book.

        Contract:
            Input:
                repo_root: Path
                settings:  EtfCtaSettings
            Output:
                EtfCtaViews  -- empty when views_file is None or the file is missing
            Raises:
                ConfigError  -- unreadable YAML, invalid content, unknown target or code
        """
        if settings.views_file is None or not (repo_root / settings.views_file).exists():
            return cls()
        path = repo_root / settings.views_file
        try:
            views = cls(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid ETF CTA views {path}: {exc}") from exc
        for view in views.views:
            for name in view.list_names():
                settings.list_members(name)  # raises ConfigError for an unknown name
        return views
