"""Settings of the futures monitor: families and value-chain spreads (plan 15 ph7i, D-145)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "futures_monitor.yaml"
FAMILY = r"^[A-Z]+\.(SHF|DCE|ZCE|INE|GFE|CFX)$"
RATIO_LEGS = 2


class FuturesFamily(BaseModel):
    """
    Purpose:
        One contract family to watch: "<fut_code>.<suffix>", Chinese name and display group.

    Contract:
        Input:
            family: str (e.g. "CU.SHF"); name: str; group: str
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- family not "<CODE>.<suffix>", extra keys

    Used by:
        core.FuturesMonitorSettings  -- field `families`
        calculation.FuturesMonitorBuilder  -- family code and names

    Test cases:
        TC-FMS-001  config/futures_monitor.yaml loads; a bad family code is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    family: str = Field(pattern=FAMILY)
    name: str = Field(min_length=1)
    group: str = Field(min_length=1)


class FuturesSpreadLeg(BaseModel):
    """
    Purpose:
        One leg of a spread: a family and its coefficient on the dominant price.

    Contract:
        Input:
            family: str; coef: float
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- bad family code, extra keys

    Used by:
        core.FuturesSpread  -- field `legs`

    Test cases:
        TC-FMS-001  (via FuturesMonitorSettings)
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    family: str = Field(pattern=FAMILY)
    coef: float


class FuturesSpread(BaseModel):
    """
    Purpose:
        A value-chain spread: sum of coef × leg price, or for kind "ratio"
        (coef 1 × leg 1) / (coef 2 × leg 2), e.g. 金银比 = 1000 × 黄金(元/克) / 白银(元/千克).

    Contract:
        Input:
            key, name, unit: str; kind: "sum" | "ratio"; legs: list[FuturesSpreadLeg] (≥ 2);
            reversion: bool  -- the spread tested mean-reverting out of sample (research run
                                20261114_mean_reversion): flag a one-year z beyond `reversion_z`;
            half_life_d: int > 0 | None  -- measured half-life in sessions, for the message
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- fewer than two legs, a ratio without exactly two legs

    Used by:
        core.FuturesMonitorSettings  -- field `spreads`

    Test cases:
        TC-FMS-002  a ratio needs exactly two legs; a leg family not in `families` is refused
        TC-FMS-003  reversion and half_life_d load; half_life_d 0 is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1)
    unit: str = ""
    kind: Literal["sum", "ratio"] = "sum"
    legs: list[FuturesSpreadLeg] = Field(min_length=2)
    reversion: bool = False
    half_life_d: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _check_ratio(self) -> FuturesSpread:
        if self.kind == "ratio" and len(self.legs) != RATIO_LEGS:
            raise ValueError(f"spread {self.key}: a ratio has exactly two legs")
        return self


class IndexFuturesProduct(BaseModel):
    """
    Purpose:
        One CFFEX index-futures product and the index it is based on (plan 15 ph7k).

    Contract:
        Input:
            product: str (IF, IH, IC, IM); name: str; index: str (index ts_code, e.g. 000300.SH)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- bad product or index code, extra keys

    Used by:
        core.FuturesMonitorSettings        -- field `index_futures`

    Test cases:
        TC-FMS-001  (via FuturesMonitorSettings) the four products load
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    product: str = Field(pattern=r"^[A-Z]{2}$")
    name: str = Field(min_length=1)
    index: str = Field(pattern=r"^\d{6}\.(SH|SZ)$")


class FuturesMonitorSettings(BaseModel):
    """
    Purpose:
        What the futures monitor watches and when it flags: families, spreads, the open-interest
        floor of a curve point, the percentile bounds and the open-interest z bound.

    Contract:
        Input:
            min_oi: float ≥ 0; flag_low, flag_high: float in (0, 1); oi_z: float > 0;
            reversion_z: float > 0  -- |one-year z| at which a reversion spread is flagged;
            families: list[FuturesFamily]; spreads: list[FuturesSpread];
            index_futures: list[IndexFuturesProduct]  -- 股指期货 watched (ph7k)
        Output:
            frozen pydantic model; `load(repo_root)` -> settings (empty when no file)
        Raises:
            ConfigError  -- unreadable YAML or invalid content (from load)
            pydantic.ValidationError  -- a spread leg not among the families, duplicate family

    Used by:
        calculation.FuturesMonitorBuilder  -- families, spreads, bounds
        calculation.IndexFuturesMonitor    -- index products and bounds
        calculation.FuturesBrokerNets      -- families and bounds
        calculation.SpreadReversion        -- reversion_z
        cli.ReportCommands                 -- loads it for `futures-monitor`

    Test cases:
        TC-FMS-001  config/futures_monitor.yaml loads; missing file gives empty settings
        TC-FMS-002  a spread leg not among the families is refused
        TC-FMS-003  reversion and half_life_d load; half_life_d 0 is refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_oi: float = Field(default=1000.0, ge=0)
    flag_low: float = Field(default=0.05, gt=0, lt=1)
    flag_high: float = Field(default=0.95, gt=0, lt=1)
    oi_z: float = Field(default=2.0, gt=0)
    reversion_z: float = Field(default=2.0, gt=0)
    families: list[FuturesFamily] = Field(default_factory=list)
    spreads: list[FuturesSpread] = Field(default_factory=list)
    index_futures: list[IndexFuturesProduct] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_legs(self) -> FuturesMonitorSettings:
        known = [f.family for f in self.families]
        if len(set(known)) != len(known):
            raise ValueError("futures monitor: a family is listed twice")
        for s in self.spreads:
            missing = [leg.family for leg in s.legs if leg.family not in known]
            if missing:
                raise ValueError(f"spread {s.key}: legs {missing} are not in families")
        return self

    @classmethod
    def load(cls, repo_root: Path) -> FuturesMonitorSettings:
        """
        Purpose:
            Read `<repo_root>/config/futures_monitor.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                FuturesMonitorSettings  -- empty families and spreads when the file is missing
            Raises:
                ConfigError  -- unreadable YAML or invalid content
        """
        path = repo_root / FILE
        if not path.exists():
            return cls()
        try:
            return cls(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid futures monitor settings {path}: {exc}") from exc
