"""One existing label file to import into the parquet label store (plan 28 ph0, D-161)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from quant_cn.core.exceptions import ConfigError

_SET_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class LabelSource(BaseModel):
    """
    Purpose:
        Describe one label file under the lake (jsonl from an LLM run, or a parse parquet) so the
        importer can turn its records into label-store rows: which label set it feeds, which
        period it describes, and where each record's document key and public date come from.

    Contract:
        Input:
            label_set:   str         -- lower snake case, e.g. "applications"
            path:        str         -- relative to the lake root, ".jsonl" or ".parquet"
            period:      str | None  -- YYYYMMDD for the whole file; None = the record's `period`
            doc_type:    str | None  -- fixed doc type; None = record `doc_type`, else key prefix
            key_field:   str | None  -- record field holding the document key ("key", "doc_id")
            key_prefix:  str | None  -- prefix added to a bare key ("annual" -> "annual:<id>")
            date_field:  str | None  -- record field holding the public date (YYYYMMDD)
            anchor_set:  str | None  -- take doc_key / doc_type / known_on from this set's row of
                                        the same company and period (for records without a key)
            taxonomy_version: str | None  -- taxonomy the record's node ids came from
            exclude_file: str | None  -- csv in the lake with a `key` column: records whose
                                         key_field value is listed are not imported
        Output:
            frozen pydantic model; `is_parquet` -> bool; `read_all(path)` -> list[LabelSource]
        Raises:
            pydantic.ValidationError  -- bad set name, bad suffix, extra keys

    Used by:
        industry_graph.LegacyLabelImporter  -- reads the files it names
        cli.DocumentCommands                -- `import-labels` reads config/label_sources.yaml

    Test cases:
        TC-LSR-001  a jsonl and a parquet source load; is_parquet follows the suffix
        TC-LSR-002  an upper-case set name, another suffix or an extra key are refused
        TC-LSR-004  exclude_file must be a .csv in the lake; it needs key_field
        TC-LSR-003  read_all loads config/label_sources.yaml in order, anchors listed first;
                    a missing file gives []; a bad entry raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    label_set: str
    path: str
    period: str | None = None
    doc_type: str | None = None
    key_field: str | None = None
    key_prefix: str | None = None
    date_field: str | None = None
    anchor_set: str | None = None
    taxonomy_version: str | None = None
    exclude_file: str | None = None

    @field_validator("label_set", "anchor_set")
    @classmethod
    def _check_set(cls, value: str | None) -> str | None:
        if value is not None and not _SET_NAME.match(value):
            raise ValueError(f"label set {value!r} must be lower snake case")
        return value

    @field_validator("path")
    @classmethod
    def _check_path(cls, value: str) -> str:
        if not value.endswith((".jsonl", ".parquet")) or ".." in value.split("/"):
            raise ValueError(f"label source {value!r} must be a .jsonl or .parquet in the lake")
        return value

    @field_validator("exclude_file")
    @classmethod
    def _check_exclude(cls, value: str | None) -> str | None:
        if value is not None and (not value.endswith(".csv") or ".." in value.split("/")):
            raise ValueError(f"exclude file {value!r} must be a .csv in the lake")
        return value

    @model_validator(mode="after")
    def _check_exclude_key(self) -> LabelSource:
        if self.exclude_file is not None and self.key_field is None:
            raise ValueError("exclude_file needs key_field")
        return self

    @property
    def is_parquet(self) -> bool:
        """
        Purpose:
            Whether the file is parquet (else jsonl).

        Contract:
            Input:
                (none)
            Output:
                bool
            Raises:
                (none)
        """
        return self.path.endswith(".parquet")

    @classmethod
    def read_all(cls, path: Path) -> list[LabelSource]:
        """
        Purpose:
            The sources listed in a label-sources YAML file (`sources:` list), in file order.

        Contract:
            Input:
                path: Path  -- e.g. <repo>/config/label_sources.yaml
            Output:
                list[LabelSource]  -- [] when the file does not exist
            Raises:
                ConfigError  -- malformed YAML or an invalid entry
        """
        if not path.exists():
            return []
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return [cls(**entry) for entry in data.get("sources", [])]
        except (yaml.YAMLError, ValidationError, TypeError, AttributeError) as exc:
            raise ConfigError(f"bad label sources in {path}: {exc}") from exc
