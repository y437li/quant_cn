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
        core.Config                      -- field `lake`
        cli.QuantCnCli                   -- lake root for every lake class, doctor, backup

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
        core.Config                      -- field `tushare`
        data_loading.TushareClient       -- all settings

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
        core.Config                      -- field `download`, `start_for`
        pipeline.DownloadPipeline.run    -- order and end date

    Test cases:
        TC-C-004  start_for applies dataset start, long history, then default
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    order: list[str]
    default_start: str
    long_history_start: str
    long_history_datasets: list[str]
    end: str | None = None


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
        Output:
            frozen pydantic model
        Raises:
            ConfigError  -- see load

    Used by:
        cli.QuantCnCli                   -- composition root
        data_loading.FetcherFactory      -- enum values
        pipeline.DownloadPipeline        -- dataset order, start dates

    Test cases:
        TC-C-001  env > local.yaml > base.yaml precedence for lake.lake_root
        TC-C-002  token read from env, never from YAML, not shown in repr
        TC-C-003  lake root inside the repo is refused unless allow_inside_repo
        TC-C-004  start_for applies dataset start, long history, then default
        TC-C-005  unknown dataset name raises ConfigError
        TC-C-006  "~" and relative roots are resolved (relative = repo root)
        TC-C-007  the committed config/ files load and every ordered dataset exists
        TC-C-008  malformed YAML or a dataset whose key differs from its name raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    repo_root: Path
    lake: LakeConfig
    tushare: TushareConfig
    download: DownloadConfig
    enum_values: dict[str, list[str]] = Field(default_factory=dict)
    datasets: dict[str, DatasetSpec]

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
