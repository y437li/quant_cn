"""Rules of the daily opportunity list (plan 21 ph4; file shared with plan 16 ph3)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "discovery_rules.yaml"
SECTION = "opportunity"
RULES = ("retail_leaving", "inflow", "earnings", "valuation", "fit")


class OpportunitySettings(BaseModel):
    """
    Purpose:
        Universe, rule thresholds and list sizes of the daily opportunity list, read from the
        `opportunity` section of `config/discovery_rules.yaml` (plan 21 ph4, D-155, D-167).
        The rules (RULES):
        - retail_leaving: the latest RetailGauge reading has `retail_leaving` (D-167);
        - inflow: large-order net inflow in >= inflow_weeks of the last 4 weeks;
        - earnings: single-quarter profit YoY >= np_yoy_min and QoQ >= np_qoq_min;
        - valuation: `valuation_field` > 0 and below its own median of `valuation_years`;
        - fit: adding the stock at `fit_weight` does not raise the absolute exposure of the
          book's `fit_styles` largest styles.
        A name with the D-155 `avoid` flag is never listed, not even as a near-miss.

    Contract:
        Input:
            min_circ_mv: float > 0 (亿); exclude_st: bool; gauge_max_age_days: int > 0;
            inflow_weeks: int 1..4; np_yoy_min, np_qoq_min: float; valuation_field: "pb" |
            "pe_ttm"; valuation_years: int 1..20; fit_weight: float in (0, 1);
            fit_styles: int > 0; required: list of RULES names (a near-miss never misses
            them); top_n, near_n: int >= 0
        Output:
            frozen pydantic model; `load(repo_root)`
        Raises:
            pydantic.ValidationError  -- out-of-range values, extra keys, unknown rule name

    Used by:
        portfolio.OpportunityDocument  -- rule thresholds for the page legend
        portfolio.OpportunityRules   -- thresholds, required rules, list sizes
        portfolio.OpportunityScreen  -- universe, windows
        portfolio.StyleFitChecker    -- fit weight and styles
        cli.GaugeCommands            -- loads it

    Test cases:
        TC-OPS-001  config/discovery_rules.yaml loads; a missing file gives the defaults; an
                    unknown key or an unknown required rule is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    min_circ_mv: float = Field(default=50.0, gt=0)
    exclude_st: bool = True
    gauge_max_age_days: int = Field(default=45, gt=0)
    inflow_weeks: int = Field(default=3, ge=1, le=4)
    np_yoy_min: float = 0.2
    np_qoq_min: float = 0.0
    valuation_field: str = Field(default="pb", pattern="^(pb|pe_ttm)$")
    valuation_years: int = Field(default=5, ge=1, le=20)
    fit_weight: float = Field(default=0.05, gt=0, lt=1)
    fit_styles: int = Field(default=2, gt=0)
    required: list[str] = Field(default_factory=lambda: ["retail_leaving"])
    top_n: int = Field(default=10, ge=0)
    near_n: int = Field(default=5, ge=0)

    @field_validator("required")
    @classmethod
    def validate_required(cls, value: list[str]) -> list[str]:
        """
        Purpose:
            Refuse unknown names in `required`.

        Contract:
            Input:
                value: list[str]
            Output:
                list[str]  -- unchanged
            Raises:
                ValueError  -- a name not in RULES (surfaces as ValidationError)
        """
        unknown = sorted(set(value) - set(RULES))
        if unknown:
            raise ValueError(f"unknown required rules: {unknown}")
        return value

    @classmethod
    def load(cls, repo_root: Path) -> OpportunitySettings:
        """
        Purpose:
            Read the `opportunity` section of config/discovery_rules.yaml under repo_root.

        Contract:
            Input:
                repo_root: Path
            Output:
                OpportunitySettings  -- defaults when the file or the section is missing
            Raises:
                ConfigError  -- unreadable YAML or invalid settings
        """
        path = repo_root / FILE
        if not path.exists():
            return cls()
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return cls.model_validate(raw.get(SECTION) or {})
        except (yaml.YAMLError, ValidationError) as exc:
            raise ConfigError(f"{path}: {exc}") from exc
