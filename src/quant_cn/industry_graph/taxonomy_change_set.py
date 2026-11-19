"""One accepted version of taxonomy changes, applied on top of config/industry_chain (D-161)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

CHANGES_DIR = "_changes"


class TaxonomyChange(BaseModel):
    """
    Purpose:
        One change of a taxonomy version (plan 28 ph3b-4): `upsert` a node (a new node, or
        name / segment / parent of an existing one, with aliases added and `drop_aliases`
        removed) or `retire` a node in favour of `successor` (its products move to the
        successor, its id resolves to it). `kind` (new / split / merge / rename / retire /
        alias) and `split_from` only feed the lineage; `sector` is the Shenwan L1 code a new
        node belongs to.

    Contract:
        Input:
            op: "upsert" | "retire"; node: dict | None (upsert: id, type, name, segment?,
            parent?, aliases?); id: str | None (retire); successor: str | None (retire);
            drop_aliases: list[str]; sector: str | None; kind: str; split_from: list[str];
            reason: str
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- upsert without node id / type / name, retire without
                                         id and successor, unknown keys

    Used by:
        industry_graph.TaxonomyChangeSet  -- its changes
        industry_graph.ProductTaxonomy  -- applies them
        industry_graph.NodeLineageBuilder  -- lineage rows per change

    Test cases:
        TC-TCS-001  (via TaxonomyChangeSet) valid upsert and retire load; bad ones refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    op: Literal["upsert", "retire"]
    node: dict[str, Any] | None = None
    id: str | None = None
    successor: str | None = None
    drop_aliases: list[str] = []
    sector: str | None = None
    kind: str = "alias"
    split_from: list[str] = []
    reason: str = ""

    @model_validator(mode="after")
    def _check_op(self) -> TaxonomyChange:
        if self.op == "upsert" and not (
            self.node and all(self.node.get(k) for k in ("id", "type", "name"))
        ):
            raise ValueError("upsert needs node with id, type and name")
        if self.op == "retire" and not (self.id and self.successor):
            raise ValueError("retire needs id and successor")
        return self

    @property
    def node_id(self) -> str:
        """
        Purpose:
            The id the change is about.

        Contract:
            Input:
                (none)
            Output:
                str
            Raises:
                (none)
        """
        return str(self.node["id"]) if self.node else str(self.id)


class TaxonomyChangeSet(BaseModel):
    """
    Purpose:
        One accepted taxonomy version (plan 28 ph3b-4, D-161): the changes Opus curation
        proposed and the user accepted, effective from `effective_period`. Stored as
        config/industry_chain/_changes/<version>.yaml; versions apply in name order on top of
        the v0 files, so a version can be read, diffed and reverted on its own.

    Contract:
        Input:
            version: str; effective_period: str (YYYYMMDD); note: str; changes:
            list[TaxonomyChange]
        Output:
            frozen pydantic model; `read_all(folder) -> list[TaxonomyChangeSet]` (classmethod)
        Raises:
            ConfigError  -- a version file that does not parse or validate

    Used by:
        industry_graph.ProductTaxonomy  -- applied at load
        industry_graph.NodeLineageBuilder  -- lineage rows per version
        cli.DocumentCommands  -- `build-graph` loads them

    Test cases:
        TC-TCS-001  read_all loads versions in name order; a missing folder gives []
        TC-TCS-002  a bad change raises ConfigError naming the file
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    effective_period: str
    note: str = ""
    changes: list[TaxonomyChange]

    @classmethod
    def read_all(cls, folder: Path) -> list[TaxonomyChangeSet]:
        """
        Purpose:
            Every version under folder/_changes, in name order.

        Contract:
            Input:
                folder: Path  -- config/industry_chain
            Output:
                list[TaxonomyChangeSet]
            Raises:
                ConfigError  -- a file that does not parse or validate
        """
        out = []
        for path in sorted((folder / CHANGES_DIR).glob("*.yaml")):
            try:
                out.append(cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))))
            except (yaml.YAMLError, ValidationError) as exc:
                raise ConfigError(f"{path.name}: {exc}") from exc
        return out
