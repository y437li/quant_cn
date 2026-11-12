"""Hand-entered cycle series as a data source (plan 20, D-139): Clarksons newbuild index, TiO2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.exceptions import ConfigError

PUBLIC_FILE = Path("config") / "manual_series.yaml"
LICENSED_FILE = Path("config") / "local.manual_series.yaml"  # git-ignored (config/local.*.yaml)
ENDPOINT = "series"
COLUMNS = [
    "series", "name", "unit", "freq", "kind", "date", "value", "published",
    "source_url", "note", "licensed", "revision",
]  # fmt: skip
_DATE = r"^\d{8}$"


class ManualSeriesDef(BaseModel):
    """
    Purpose:
        One hand-entered series: what it measures and how often it is published.

    Contract:
        Input:
            id: str; name: str; unit: str; freq: "daily" | "weekly" | "monthly" | "quarterly";
            kind: "index" | "price" | "spread" | "count"; links: list[str]  -- ts_codes it drives
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- unknown keys or values

    Used by:
        data_loading.ManualSeriesClient  -- series definitions
        data_loading.ManualSeriesFile    -- field type

    Test cases:
        TC-MSC-001  both files load into one frame with series metadata on every row
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    unit: str
    freq: str = Field(pattern=r"^(daily|weekly|monthly|quarterly)$")
    kind: str = Field(pattern=r"^(index|price|spread|count)$")
    links: list[str] = Field(default_factory=list)


class ManualObservation(BaseModel):
    """
    Purpose:
        One value of a series as published on a date, with the page it was read from.

    Contract:
        Input:
            series: str; date: YYYYMMDD (the period the value describes); value: float;
            published: YYYYMMDD (>= date; the day it became public, the PIT date);
            source_url: str (http...); note: str = ""; revision: bool = False
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- bad dates, published before date, missing URL

    Used by:
        data_loading.ManualSeriesClient  -- observations
        data_loading.ManualSeriesFile    -- field type

    Test cases:
        TC-MSC-002  published before date, unknown series, or a duplicate without revision fail
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    series: str
    date: str = Field(pattern=_DATE)
    value: float
    published: str = Field(pattern=_DATE)
    source_url: str = Field(pattern=r"^https?://")
    note: str = ""
    revision: bool = False

    @model_validator(mode="after")
    def _check_published(self) -> ManualObservation:
        if self.published < self.date:
            raise ValueError(f"{self.series} {self.date}: published {self.published} before date")
        return self


class ManualSeriesFile(BaseModel):
    """
    Purpose:
        The content of one manual-series YAML file.

    Contract:
        Input:
            series: list[ManualSeriesDef]; observations: list[ManualObservation]
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- invalid entries

    Used by:
        data_loading.ManualSeriesClient  -- one per file

    Test cases:
        TC-MSC-001  both files load into one frame with series metadata on every row
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    series: list[ManualSeriesDef] = Field(default_factory=list)
    observations: list[ManualObservation] = Field(default_factory=list)


class ManualSeriesClient(BaseApiClient):
    """
    Purpose:
        Serve the hand-entered series in `config/manual_series.yaml` (public rows, committed) and
        `config/local.manual_series.yaml` (licensed exports, git-ignored) as one vendor frame, so
        the normal download / compact path writes them to curated `alt/manual_series` with
        known_on = published (D-139). Every row keeps its source URL.

    Contract:
        Input:
            repo_root: Path  -- repository root holding config/
        Output:
            instance; `query(api_name, params, fields)` -> DataFrame with COLUMNS
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "manual"

    Test cases:
        TC-MSC-001  both files load into one frame with series metadata on every row; licensed
                    rows are flagged; a missing local file gives public rows only
        TC-MSC-002  published before date, unknown series, or a duplicate (series, date,
                    published) fail with ConfigError naming the row; a revision on a later
                    published date is kept next to the original
        TC-MSC-003  an endpoint other than "series" or broken YAML raises ConfigError
    """

    def __init__(self, repo_root: Path) -> None:
        self._root = repo_root

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            All observations of both files, validated, one row per (series, date, published).

        Contract:
            Input:
                api_name: str  -- must be "series"; params, fields: ignored
            Output:
                DataFrame  -- COLUMNS; licensed / revision as 0 / 1
            Raises:
                ConfigError  -- unknown endpoint, unreadable YAML, invalid or duplicate rows
        """
        if api_name != ENDPOINT:
            raise ConfigError(f"manual series: unknown endpoint {api_name!r}")
        files = [(self._read_file(PUBLIC_FILE), 0), (self._read_file(LICENSED_FILE), 1)]
        defs = {d.id: d for f, _ in files for d in f.series}
        rows = [self._to_row(o, defs, licensed) for f, licensed in files for o in f.observations]
        frame = pd.DataFrame(rows, columns=COLUMNS)
        dup = frame[frame.duplicated(["series", "date", "published"], keep=False)]
        if not dup.empty:
            first = dup.iloc[0]
            raise ConfigError(
                f"manual series: duplicate {first['series']} {first['date']} "
                f"published {first['published']}"
            )
        return frame.sort_values(["series", "date", "published"]).reset_index(drop=True)

    def _read_file(self, rel: Path) -> ManualSeriesFile:
        path = self._root / rel
        if not path.exists():
            return ManualSeriesFile()
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return ManualSeriesFile(**data)
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigError(f"invalid manual series file {path}: {exc}") from exc

    @staticmethod
    def _to_row(
        obs: ManualObservation, defs: Mapping[str, ManualSeriesDef], licensed: int
    ) -> list[object]:
        meta = defs.get(obs.series)
        if meta is None:
            raise ConfigError(f"manual series: unknown series {obs.series!r} on {obs.date}")
        return [
            obs.series, meta.name, meta.unit, meta.freq, meta.kind, obs.date, obs.value,
            obs.published, obs.source_url, obs.note, licensed, int(obs.revision),
        ]  # fmt: skip
