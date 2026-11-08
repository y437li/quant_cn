"""Typed view of one `config/datasets.yaml` entry: endpoint, sweep, keys, curated layout."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quant_cn.core.schema import Schema

SweepKind = Literal[
    "none",
    "list_status",
    "ts_code",
    "exchange",
    "is_new",
    "trade_date",
    "ann_date",
    "nav_date",
    "period",
    "date_window",
]
DATE_KINDS = ("trade_date", "ann_date", "nav_date")
ENUM_KINDS = ("list_status", "ts_code", "exchange", "is_new")
Source = Literal["tushare", "fred", "akshare", "baostock", "cninfo", "eastmoney"]
KnownOnRule = Literal["as_is", "next_session", "period_end_lag", "period_start_lag"]
Days = Literal["sessions", "weekdays", "all"]
Window = Literal["month", "year"]


class ValuesFromDataset(BaseModel):
    """
    Purpose:
        Enumerate sweep keys from another curated dataset (e.g. every ETF code in fund_basic).

    Contract:
        Input:
            dataset: str        -- curated dataset name
            column:  str        -- column holding the keys
            where:   str | None -- optional SQL filter on that dataset, e.g. "fund_type = 'ETF'"
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError

    Used by:
        core.SweepSpec  -- field `values_from_dataset`

    Test cases:
        TC-FF-003  values_from_dataset keys resolved from a curated dataset with a filter
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset: str
    column: str
    where: str | None = None


class SweepSpec(BaseModel):
    """
    Purpose:
        How a dataset is swept so each call returns the whole market for one key.

    Contract:
        Input:
            kind:           SweepKind        -- "none" = one call, key "all"
            values:         list[str] | None -- explicit keys for the enum kinds (ENUM_KINDS)
            values_from:    str | None       -- name of a list in Config.enum_values instead
            range_params:   bool             -- also pass start_date/end_date to the endpoint
            extra_params:   dict[str, str]   -- constant parameters (e.g. exchange)
            refetch_recent: int >= 0         -- always refetch the newest N keys (late filers)
            values_from_dataset: ValuesFromDataset | None -- keys from another curated dataset
            window:         "month" | "year" | None  -- calendar window for kind date_window
            param_name:     str | None       -- API parameter carrying the key when it differs
                                                from the kind (disclosure_date: end_date); for
                                                date_window the window key itself is sent (D-081)
            days:           "sessions" | "weekdays" | "all" | None  -- date sweeps: which days;
                                                None = sessions for trade_date/nav_date, else
                                                weekdays (event data also publishes on weekends)
            key_field:      str | None       -- column set to the sweep key when the response
                                                lacks it (SZSE margin list has no date; D-087)
            value_param:    str | None       -- date_window only: API parameter swept per window
                                                with the values (keys "<window>_<value>", D-069)
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
    values_from_dataset: ValuesFromDataset | None = None
    window: Window | None = None
    value_param: str | None = None
    param_name: str | None = None
    days: Days | None = None
    key_field: str | None = None

    @model_validator(mode="after")
    def _check_window(self) -> SweepSpec:
        if (self.kind == "date_window") != (self.window is not None):
            raise ValueError("sweep.window is required exactly when kind is date_window")
        if self.value_param and self.kind != "date_window":
            raise ValueError("sweep.value_param is only valid with kind date_window")
        has_values = bool(self.values or self.values_from or self.values_from_dataset)
        if self.kind == "date_window" and has_values != bool(self.value_param):
            raise ValueError("date_window: sweep.value_param and a values source go together")
        if self.days and self.kind not in DATE_KINDS:
            raise ValueError("sweep.days is only valid with a date kind")
        if self.param_name and self.value_param:
            raise ValueError("sweep.param_name and sweep.value_param are exclusive")
        return self

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
        if self.kind == "none":
            return None
        if self.param_name:
            return self.param_name
        return "window" if self.kind == "date_window" else self.kind


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
            source:      "tushare" | "fred" | "akshare" | "baostock" | "cninfo" | "eastmoney"  --
                                          API client (D-063, D-096)
            known_on_rule: "as_is" | "next_session" | "period_end_lag" | "period_start_lag"  --
                                          how known_on becomes
                                          the first usable session (EffectiveDateResolver)
            release_dates: str | None  -- dataset of observed release dates that checks the
                                          period_end_lag rule (ReleaseLagChecker, D-086)
            rename:       dict[str, str] -- vendor column -> field, applied before the raw write
                                          (AkShare / BaoStock columns; D-087)
            key_defaults: dict[str, str] -- value filled into a NULL text primary-key column before
                                          validation (report_rc: rating-only reports, quarter "")
            lag_sessions: int >= 1     -- next_session rule: usable from the N-th session after
                                          known_on (stk_surv: 2, visits disclosed 1-2 days later)
            release_lag_days: int >= 0 -- days after period end a value is published
                                          (period_end_lag rule; monthly macro)
            extend_days: int >= 0      -- fetch this many calendar days past the run end
                                          (trade_cal: future sessions for expiry and next-day maths)
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
        data_loading.DateWindowFetcher     -- injected type or call
        lake.EffectiveDateResolver         -- injected type or call
        lake.ReleaseLagChecker             -- injected type or call
        lake.LakeReader                    -- injected type or call

    Test cases:
        TC-DS-001  datasets.yaml entries parse into DatasetSpec
        TC-DS-002  raw_filename is "all.parquet" for single calls, "<param>=<key>.parquet" otherwise
        TC-DS-003  primary key or known_on outside fields raises ValidationError
        TC-DS-004  build_schema() mirrors fields, text_fields and primary_key
        TC-DS-005  source / known_on_rule / release_lag_days / date_window validation
        TC-DS-006  param_name renames the key parameter; days only with date kinds
        TC-DS-007  lag_sessions other than 1 requires known_on_rule next_session
        TC-DS-008  key_defaults only on text primary-key columns
        TC-DS-009  rename targets and sweep.key_field must be declared fields
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
    source: Source = "tushare"
    known_on_rule: KnownOnRule = "as_is"
    release_lag_days: int = Field(default=0, ge=0)
    lag_sessions: int = Field(default=1, ge=1)
    key_defaults: dict[str, str] = Field(default_factory=dict)
    rename: dict[str, str] = Field(default_factory=dict)
    release_dates: str | None = None
    extend_days: int = Field(default=0, ge=0)
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
        if self.sweep.key_field and self.sweep.key_field not in declared:
            raise ValueError(f"{self.name}: sweep.key_field {self.sweep.key_field} not in fields")
        if self.known_on_rule != "as_is" and not self.known_on:
            raise ValueError(f"{self.name}: known_on_rule {self.known_on_rule} needs known_on")
        if self.release_lag_days and not self.known_on_rule.startswith("period_"):
            raise ValueError(f"{self.name}: release_lag_days needs a period_*_lag known_on_rule")
        unknown = set(self.rename.values()) - declared
        if unknown:
            raise ValueError(f"{self.name}: rename targets not in fields: {sorted(unknown)}")
        bad_defaults = set(self.key_defaults) - (set(self.primary_key) & set(self.text_fields))
        if bad_defaults:
            raise ValueError(
                f"{self.name}: key_defaults on non-text-key columns {sorted(bad_defaults)}"
            )
        if self.lag_sessions != 1 and self.known_on_rule != "next_session":
            raise ValueError(f"{self.name}: lag_sessions needs known_on_rule next_session")
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
