"""The plan 28 graph tables as parquet under derived/graph/ (D-161)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from quant_cn.core.exceptions import SchemaError
from quant_cn.lake.parquet_writer import ParquetWriter

logger = logging.getLogger(__name__)

ROOT = "graph"
TABLES = (
    "entity_map",
    "company_edge",
    "edge_span",
    "company_period",
    "node_member",
    "node_lineage",
    "node_edge",
    "game_alias",
    "game_company",
)


class GraphStore:
    """
    Purpose:
        Hold the plan 28 graph tables (D-161 updates 7 and 9) as one parquet file each under
        `derived/graph/<table>.parquet`: `entity_map` (counterparty name -> entity id),
        `company_edge` (one row per observed edge), `edge_span` (one row per edge life cycle),
        `company_period` (the company leaf: one row per company, period, label set and
        document), `node_member` (company -> taxonomy node by period and revenue weight) and
        `node_lineage` (what each taxonomy version changed), `node_edge` (supplier segment ->
        buyer segment per year, evidenced vs prior), and for plan 31 `game_alias`
        (model proposals for game licence holders) and `game_company` (approved game ->
        company).
        A write replaces the whole table atomically (ParquetWriter); rows are written in the
        order given, so the same frame gives the same file. Only TABLES are allowed.

    Contract:
        Input:
            writer:    ParquetWriter  -- atomic parquet writes into derived/
            lake_root: Path
        Output:
            instance; `write(table, frame) -> Path`, `read(table, columns=None) -> DataFrame`,
            `list_tables() -> list[str]`
        Raises:
            (none at construction)

    Used by:
        cli.AppServiceBuilder  -- `build_sector_monitor`
        portfolio.SectorMetricReader  -- game_company
        industry_graph.GraphQuery  -- reads the tables
        industry_graph.GraphBuilder  -- reads entity_map, writes company_edge and edge_span
        cli.DocumentCommands         -- `build-graph` (node_member, node_lineage, node_edge)
        lake meta/runs/plan28_entities.py (writes entity_map)

    Test cases:
        TC-GS-001  write then read returns the frame (same columns, rows, order); a second
                   write replaces the table
        TC-GS-002  read of a table not written yet gives an empty frame; columns selects
        TC-GS-003  a table outside TABLES raises SchemaError; list_tables lists written tables
    """

    def __init__(self, writer: ParquetWriter, lake_root: Path) -> None:
        self._writer = writer
        self._root = lake_root / "derived" / ROOT

    def write(self, table: str, frame: pd.DataFrame) -> Path:
        """
        Purpose:
            Replace one graph table.

        Contract:
            Input:
                table: str (TABLES); frame: DataFrame
            Output:
                Path  -- the file written
            Raises:
                SchemaError  -- unknown table
                LakeError    -- the write failed
        """
        self._check_table(table)
        path = self._writer.write_table("derived", f"{ROOT}/{table}.parquet", frame)
        logger.info("graph %s: %d rows", table, len(frame))
        return path

    def read(self, table: str, columns: list[str] | None = None) -> pd.DataFrame:
        """
        Purpose:
            One graph table.

        Contract:
            Input:
                table: str (TABLES); columns: list[str] | None (all)
            Output:
                DataFrame  -- empty when the table was not written yet
            Raises:
                SchemaError  -- unknown table
        """
        self._check_table(table)
        path = self._root / f"{table}.parquet"
        if not path.exists():
            return pd.DataFrame(columns=columns or [])
        return pd.read_parquet(path, columns=columns)

    def list_tables(self) -> list[str]:
        """
        Purpose:
            The graph tables written so far.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- in TABLES order
            Raises:
                (none)
        """
        return [t for t in TABLES if (self._root / f"{t}.parquet").exists()]

    @staticmethod
    def _check_table(table: str) -> None:
        if table not in TABLES:
            raise SchemaError(f"unknown graph table {table!r}; expected one of {TABLES}")
