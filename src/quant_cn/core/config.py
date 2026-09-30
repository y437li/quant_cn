"""Typed configuration: `config/*.yaml` merged with machine overrides and environment (D-021)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import ConfigError

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_LAKE_ROOT = "QUANT_CN_LAKE_ROOT"
ENV_TOKEN = "TUSHARE_TOKEN"


class LakeConfig(BaseModel):
    """
    Purpose:
        Where the lake lives and whether it may sit inside the repository.

    Contract:
        Input:
            root:              Path         -- absolute after Config.load resolution
            allow_inside_repo: bool         -- False unless explicitly overridden in local.yaml
            backup_target:     Path | None  -- rsync destination for raw/ + fetch log
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config  -- field `lake`

    Test cases:
        TC-C-001  env > local.yaml > base.yaml precedence for lake.lake_root
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: Path
    allow_inside_repo: bool = False
    backup_target: Path | None = None


class TushareConfig(BaseModel):
    """
    Purpose:
        Tushare endpoint, paging, retry and rate-limit settings; the token comes from env only.

    Contract:
        Input:
            url, timeout_s, page_size, retries, retry_sleep_s, rate_limit_sleep_s,
            max_rate_limit_waits, rate_limit_markers, permission_markers  -- see config/README.md
            token: str  -- from TUSHARE_TOKEN; never read from YAML; hidden from repr
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config                 -- field `tushare`
        data_loading.TushareClient  -- all settings

    Test cases:
        TC-C-002  token read from env, never from YAML, not shown in repr
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str
    timeout_s: float = Field(gt=0)
    page_size: int = Field(gt=0)
    retries: int = Field(ge=0)
    retry_sleep_s: float = Field(ge=0)
    rate_limit_sleep_s: float = Field(ge=0)
    max_rate_limit_waits: int = Field(ge=0)
    rate_limit_markers: list[str]
    permission_markers: list[str]
    token: str = Field(default="", repr=False)


class DownloadConfig(BaseModel):
    """
    Purpose:
        Which datasets to download, in what order, and from which start dates (D-015b).

    Contract:
        Input:
            order:                 list[str]  -- dataset names in dependency order
            default_start:         str        -- YYYYMMDD
            long_history_start:    str        -- YYYYMMDD
            long_history_datasets: list[str]  -- datasets that start at long_history_start
            end:                   str | None -- YYYYMMDD; None = today
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config  -- field `download`, `start_for`

    Test cases:
        TC-C-004  start_for applies dataset start, long history, then default
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    order: list[str]
    default_start: str
    long_history_start: str
    long_history_datasets: list[str]
    end: str | None = None


class FactorSpec(BaseModel):
    """
    Purpose:
        One factor of config/factors.yaml: its name, implementing class and parameters.

    Contract:
        Input:
            name:       str             -- FACTOR_PANEL.factor, e.g. "ep_ttm"
            class_name: str             -- BaseFactor subclass name (YAML key `class`)
            params:     dict[str, Any]  -- constructor keyword arguments
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config           -- field `factors`
        factor.FactorFactory  -- builds the instances

    Test cases:
        TC-C-012  config/factors.yaml loads six factors with their classes; missing file = []
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    name: str
    class_name: str = Field(alias="class")
    params: dict[str, Any] = Field(default_factory=dict)


class CampaignConfig(BaseModel):
    """
    Purpose:
        Settings of one factor campaign (config/factors.yaml `campaign`, plan 04 phase 5).

    Contract:
        Input:
            id:          str                -- campaign id (TrialLog, reports)
            start:       str                -- first feature date (YYYYMMDD)
            horizons:    list[int]          -- forward-return horizons in sessions
            winsorize_k: float | None       -- MAD multiple; None skips winsorising
            standardize: bool; neutralize: bool  -- D-093 (Shenwan L1 + log market cap)
            weights:     dict[str, float]   -- factor -> weight of the combined score
            min_factors: int >= 1           -- factors a stock needs for a score
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config  -- field `campaign`

    Test cases:
        TC-C-013  config/factors.yaml campaign loads; missing section gives the defaults
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = "factor_campaign_01"
    start: str = "20190101"
    horizons: list[int] = Field(default_factory=lambda: [1, 5, 10, 20, 60])
    winsorize_k: float | None = 5.0
    standardize: bool = True
    neutralize: bool = True
    weights: dict[str, float] = Field(default_factory=dict)
    min_factors: int = Field(default=3, ge=1)


class UniverseConfig(BaseModel):
    """
    Purpose:
        Rules of the tradeable universe per session (FACTOR_TESTING_DESIGN §11, D-054).

    Contract:
        Input:
            start:        str        -- YYYYMMDD, first session built
            min_sessions: int >= 1   -- sessions since listing before a stock enters
            exchanges:    list[str]  -- ts_code suffixes admitted (BJ excluded by default)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config            -- field `universe`
        pipeline.UniverseStep  -- membership rules

    Test cases:
        TC-C-011  base.yaml universe section loads; missing section gives the defaults
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: str = "20100101"
    min_sessions: int = Field(default=120, ge=1)
    exchanges: list[str] = Field(default_factory=lambda: ["SH", "SZ"])


class FuturesCategory(BaseModel):
    """
    Purpose:
        One member-category label that `fut_holding` lists among real brokers (D-079).

    Contract:
        Input:
            exchange: str        -- CFFEX, SHFE, DCE, CZCE, GFEX
            broker:   str        -- the category label as the vendor spells it
            first:    str | None -- first date seen (documentation)
            last:     str | None -- last date seen (documentation)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config        -- field `futures_categories`
        lake.DerivedViews  -- excluded from derived.fut_holding_brokers

    Test cases:
        TC-C-009  config/futures_categories.yaml loads; a missing file gives an empty list
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    exchange: str
    broker: str
    first: str | None = None
    last: str | None = None


class TickerAlias(BaseModel):
    """
    Purpose:
        One retired code and the code its company trades on afterwards (D-053, D-089).

    Contract:
        Input:
            old_code: str  -- retired ts_code, e.g. "000043.SZ"
            new_code: str  -- surviving ts_code, e.g. "001914.SZ"
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.Config          -- field `ticker_aliases`
        lake.TickerAliasMap  -- floor of derived.ticker_alias
        lake.DerivedViews    -- injected type or call

    Test cases:
        TC-C-010  config/ticker_aliases.yaml loads the three known pairs; missing file = []
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    old_code: str
    new_code: str


class Config(BaseModel):
    """
    Purpose:
        The typed configuration injected everywhere: YAML defaults, machine overrides, environment.

    Contract:
        Input:
            (built by Config.load; direct construction is for tests)
            repo_root:   Path
            lake:        LakeConfig
            tushare:     TushareConfig
            download:    DownloadConfig
            enum_values: dict[str, list[str]]  -- named key lists for enum sweeps (e.g. indices)
            datasets:    dict[str, DatasetSpec]
            futures_categories: list[FuturesCategory]  -- config/futures_categories.yaml (D-079)
            ticker_aliases: list[TickerAlias]  -- config/ticker_aliases.yaml (D-089)
            universe:    UniverseConfig          -- base.yaml `universe` (plan 04 phase 3)
            factors:     list[FactorSpec]        -- config/factors.yaml (plan 04 phase 4)
            campaign:    CampaignConfig          -- config/factors.yaml `campaign` (phase 5)
        Output:
            frozen pydantic model
        Raises:
            ConfigError  -- see load

    Used by:
        cli.QuantCnCli               -- composition root
        data_loading.FetcherFactory  -- enum values
        pipeline.DownloadPipeline    -- dataset order, start dates
        pipeline.CuratePipeline      -- injected type or call
        cli.ServiceBuilder           -- injected type or call

    Test cases:
        TC-C-001  env > local.yaml > base.yaml precedence for lake.lake_root
        TC-C-002  token read from env, never from YAML, not shown in repr
        TC-C-003  lake root inside the repo is refused unless allow_inside_repo
        TC-C-004  start_for applies dataset start, long history, then default
        TC-C-005  unknown dataset name raises ConfigError
        TC-C-006  "~" and relative roots are resolved (relative = repo root)
        TC-C-007  the committed config/ files load and every ordered dataset exists
        TC-C-008  malformed YAML or a dataset whose key differs from its name raises ConfigError
        TC-C-009  config/futures_categories.yaml loads; a missing file gives an empty list
        TC-C-010  config/ticker_aliases.yaml loads the three known pairs; missing file = []
        TC-C-011  base.yaml universe section loads; missing section gives the defaults
        TC-C-012  config/factors.yaml loads six factors with their classes; missing file = []
        TC-C-013  config/factors.yaml campaign loads; missing section gives the defaults
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    repo_root: Path
    lake: LakeConfig
    tushare: TushareConfig
    download: DownloadConfig
    enum_values: dict[str, list[str]] = Field(default_factory=dict)
    datasets: dict[str, DatasetSpec]
    futures_categories: list[FuturesCategory] = Field(default_factory=list)
    ticker_aliases: list[TickerAlias] = Field(default_factory=list)
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    factors: list[FactorSpec] = Field(default_factory=list)
    campaign: CampaignConfig = Field(default_factory=CampaignConfig)

    @classmethod
    def load(
        cls,
        repo_root: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> Config:
        """
        Purpose:
            Build the configuration from `config/base.yaml`, `config/datasets.yaml`, optional
            `config/local.yaml`, the repo `.env` and the process environment.

        Contract:
            Input:
                repo_root: Path | None           -- default: the repository holding this package
                env:       Mapping[str, str] | None  -- default: `.env` overlaid by os.environ
            Output:
                Config  -- lake.lake_root absolute; token from env ("" if unset)
            Raises:
                ConfigError  -- missing/malformed YAML, validation failure, bad dates, dataset
                                name mismatch, lake root inside the repo without opt-in
        """
        root = (repo_root or REPO_ROOT).resolve()
        environ = dict(env) if env is not None else cls._read_environment(root)
        base = cls._read_yaml(root / "config" / "base.yaml", required=True)
        local = cls._read_yaml(root / "config" / "local.yaml", required=False)
        merged = cls._build_merged(base, local)
        datasets = cls._read_yaml(root / "config" / "datasets.yaml", required=True)
        extras = cls._read_extras(root)

        lake = dict(merged.get("lake", {}))
        if environ.get(ENV_LAKE_ROOT):
            lake["root"] = environ[ENV_LAKE_ROOT]
        lake["root"] = cls._normalize_root(root, str(lake.get("root", "")))
        tushare = {**merged.get("tushare", {}), "token": environ.get(ENV_TOKEN, "")}
        try:
            config = cls(
                repo_root=root,
                lake=LakeConfig(**lake),
                tushare=TushareConfig(**tushare),
                download=DownloadConfig(**merged.get("download", {})),
                enum_values=merged.get("enum_values", {}),
                datasets={name: DatasetSpec(name=name, **spec) for name, spec in datasets.items()},
                universe=UniverseConfig(**merged.get("universe", {})),
                **extras,
            )
        except (ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid configuration: {exc}") from exc
        config._check()
        return config

    def get_dataset(self, name: str) -> DatasetSpec:
        """
        Purpose:
            Look up one dataset spec by name.

        Contract:
            Input:
                name: str  -- a key of config/datasets.yaml
            Output:
                DatasetSpec
            Raises:
                ConfigError  -- unknown name
        """
        try:
            return self.datasets[name]
        except KeyError:
            raise ConfigError(f"unknown dataset {name!r}") from None

    def get_start(self, name: str) -> str:
        """
        Purpose:
            Download start date for a dataset: its own `start`, else long-history start if listed,
            else the default start.

        Contract:
            Input:
                name: str  -- known dataset
            Output:
                str  -- YYYYMMDD
            Raises:
                ConfigError  -- unknown name
        """
        spec = self.get_dataset(name)
        if spec.start:
            return spec.start
        if name in self.download.long_history_datasets:
            return self.download.long_history_start
        return self.download.default_start

    def _check(self) -> None:
        codec = DateCodec()
        dates = [self.download.default_start, self.download.long_history_start]
        dates += [s.start for s in self.datasets.values() if s.start]
        dates += [self.download.end] if self.download.end else []
        try:
            for value in dates:
                codec.validate(value)
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc
        unknown = [n for n in self.download.order if n not in self.datasets]
        if unknown:
            raise ConfigError(f"download.order names unknown datasets: {unknown}")
        lake_root = self.lake.root
        if not self.lake.allow_inside_repo and lake_root.is_relative_to(self.repo_root):
            raise ConfigError(
                f"lake root {lake_root} is inside the repository; set QUANT_CN_LAKE_ROOT to a path "
                "outside it (D-021) or lake.allow_inside_repo: true in config/local.yaml"
            )

    @classmethod
    def _read_extras(cls, root: Path) -> dict[str, Any]:
        """The optional list files: futures categories, ticker aliases, factors."""
        categories = cls._read_yaml(root / "config" / "futures_categories.yaml", required=False)
        aliases = cls._read_yaml(root / "config" / "ticker_aliases.yaml", required=False)
        factors = cls._read_yaml(root / "config" / "factors.yaml", required=False)
        return {
            "futures_categories": [FuturesCategory(**c) for c in categories.get("categories", [])],
            "ticker_aliases": [TickerAlias(**a) for a in aliases.get("aliases", [])],
            "factors": [FactorSpec(**f) for f in factors.get("factors", [])],
            "campaign": CampaignConfig(**factors.get("campaign", {})),
        }

    @staticmethod
    def _read_environment(root: Path) -> dict[str, str]:
        values = {k: v for k, v in dotenv_values(root / ".env").items() if v is not None}
        values.update(os.environ)
        return values

    @staticmethod
    def _read_yaml(path: Path, required: bool) -> dict[str, Any]:
        if not path.exists():
            if required:
                raise ConfigError(f"missing config file {path}")
            return {}
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"malformed YAML in {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path} must contain a mapping at top level")
        return data

    @classmethod
    def _build_merged(cls, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        out = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(out.get(key), dict):
                out[key] = cls._build_merged(out[key], value)
            else:
                out[key] = value
        return out

    @staticmethod
    def _normalize_root(repo_root: Path, raw: str) -> Path:
        if not raw:
            raise ConfigError("lake.lake_root is empty")
        path = Path(raw).expanduser()
        return (path if path.is_absolute() else repo_root / path).resolve()
