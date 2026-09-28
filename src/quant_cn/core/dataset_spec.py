"""Typed view of one `config/datasets.yaml` entry: endpoint, sweep, keys, curated layout."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quant_cn.core.schema import Schema

SweepKind = Literal[
    "none", "list_status", "ts_code", "exchange", "trade_date", "ann_date", "period"
]


class SweepSpec(BaseModel):
    """
    Purpose:
        How a dataset is swept so each call returns the whole market for one key.

    Contract:
        Input:
            kind:           SweepKind        -- "none" = one call, key "all"
            values:         list[str] | None -- explicit keys for list_status/ts_code/exchange
            values_from:    str | None       -- name of a list in Config.enum_values instead
            range_params:   bool             -- also pass start_date/end_date to the endpoint
            extra_params:   dict[str, str]   -- constant parameters (e.g. exchange)
            refetch_recent: int >= 0         -- always refetch the newest N keys (late filers)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- unknown kind or wrong types

    Used by:
        core.DatasetSpec  -- field `sweep`

    Test cases:
        TC-DS-001  datasets.yaml entries parse into DatasetSpec
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: SweepKind
    values: list[str] | None = None
    values_from: str | None = None
    range_params: bool = False
    extra_params: dict[str, str] = Field(default_factory=dict)
    refetch_recent: int = Field(default=0, ge=0)

    @property
    def param(self) -> str | None:
        """
        Purpose:
            API parameter name carrying the key (None for single-call datasets).

        Contract:
            Input:
                (none)
            Output:
                str | None
            Raises:
                (none)
        """
        return None if self.kind == "none" else self.kind


class CuratedSpec(BaseModel):
    """
    Purpose:
        Where a dataset lands in `curated/` and which date column drives its yearly partition.

    Contract:
        Input:
            path:         str        -- relative to curated/, e.g. "daily", "reference/trade_cal"
            partition_by: str | None -- date column for `year=YYYY` partitions; None = single file
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.DatasetSpec  -- field `curated`

    Test cases:
        TC-DS-001  datasets.yaml entries parse into DatasetSpec
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    partition_by: str | None = None


class DatasetSpec(BaseModel):
    """
    Purpose:
        Everything the lake and the fetchers need to know about one dataset, as data (D-012).

    Contract:
        Input:
            name:        str           -- dataset key, also the raw/ folder name
            endpoint:    str           -- Tushare api_name
            sweep:       SweepSpec
            primary_key: list[str]     -- subset of fields
            known_on:    str | None    -- PIT date column (CODING_STANDARD §2.7); None for calendars
            refresh:     "append" | "overwrite"  -- overwrite = refetch every key on every run
            fields:      list[str]     -- requested columns, non-empty
            text_fields: list[str]     -- subset stored as text; all other fields are numeric
            start:       str | None    -- dataset-specific download start (YYYYMMDD)
            curated:     CuratedSpec
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing keys, or key/text/known_on/partition columns
                                         not in fields

    Used by:
        core.Config                        -- `datasets` mapping and `dataset()`
        core.BaseFetcher                   -- endpoint, fields, refresh
        core.BaseStore                     -- write targets
        lake.ParquetWriter                 -- raw filename, schema
        lake.LakeCatalog                   -- views and dataset_meta
        lake.Compactor.rebuild             -- schema, partitioning, primary key
        data_loading.FetcherFactory.build  -- sweep dispatch
        data_loading.DateSweepFetcher      -- injected type or call
        data_loading.EnumFetcher           -- injected type or call
        data_loading.PeriodSweepFetcher    -- injected type or call
        pipeline.CompactStep               -- injected type or call
        lake.DerivedViews                  -- injected type or call
        lake.ProjectCatalog                -- injected type or call

    Test cases:
        TC-DS-001  datasets.yaml entries parse into DatasetSpec
        TC-DS-002  raw_filename is "all.parquet" for single calls, "<param>=<key>.parquet" otherwise
        TC-DS-003  primary key or known_on outside fields raises ValidationError
        TC-DS-004  frame_schema() mirrors fields, text_fields and primary_key
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    endpoint: str
    sweep: SweepSpec
    primary_key: list[str]
    known_on: str | None
    refresh: Literal["append", "overwrite"] = "append"
    fields: list[str]
    text_fields: list[str]
    start: str | None = None
    curated: CuratedSpec

    @model_validator(mode="after")
    def _check_columns(self) -> DatasetSpec:
        declared = set(self.fields)
        used = set(self.primary_key) | set(self.text_fields)
        if self.known_on:
            used.add(self.known_on)
        if self.curated.partition_by:
            used.add(self.curated.partition_by)
        missing = used - declared
        if missing:
            raise ValueError(f"{self.name}: columns not in fields: {sorted(missing)}")
        return self

    def get_raw_filename(self, key: str) -> str:
        """
        Purpose:
            Hive-style raw file name for one fetch key.

        Contract:
            Input:
                key: str  -- "all" for single calls, else the sweep value
            Output:
                str  -- "all.parquet" or "<param>=<key>.parquet"
            Raises:
                (none)
        """
        param = self.sweep.param
        return "all.parquet" if param is None else f"{param}={key}.parquet"

    def build_schema(self) -> Schema:
        """
        Purpose:
            The dataset's Schema (fields, text fields, primary key).

        Contract:
            Input:
                (none)
            Output:
                Schema
            Raises:
                SchemaError  -- only if the spec is inconsistent (prevented by validation)
        """
        return Schema(self.name, self.fields, self.text_fields, self.primary_key)
