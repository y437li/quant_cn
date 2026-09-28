"""The repository as SQL: schema `project` in the lake catalog, rebuilt from docs + code (D-017)."""

from __future__ import annotations

import logging
from collections.abc import Mapping

import duckdb
import pandas as pd

from quant_cn.core.clock import Clock
from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.core.docs.code_table_builder import CodeTableBuilder
from quant_cn.core.docs.contract_linter import ContractLinter
from quant_cn.core.docs.doc_table_builder import DocTableBuilder
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_catalog import LakeCatalog

logger = logging.getLogger(__name__)
SCHEMA = "project"
DATASET_COLUMNS = [
    "name",
    "endpoint",
    "sweep_kind",
    "primary_key",
    "known_on",
    "refresh",
    "zone",
    "partition_raw",
    "partition_curated",
    "curated_path",
]
LINT_COLUMNS = ["check", "path", "line", "message", "run_at"]
VIEWS = {
    "tree": f"""
        WITH RECURSIVE t AS (
            SELECT path, name, purpose, depth, '' AS sort FROM {SCHEMA}.folders WHERE parent IS NULL
            UNION ALL
            SELECT f.path, f.name, f.purpose, f.depth, t.sort || '/' || f.name
            FROM {SCHEMA}.folders f JOIN t ON f.parent = t.path
        )
        SELECT repeat('  ', depth) || name || '/' AS entry, path, purpose FROM t ORDER BY sort""",
    "class_graph": f"""
        SELECT u.callee_class, ce.module AS callee_module, u.caller_class, u.caller_method,
               cr.module AS caller_module, u.caller, u.note
        FROM {SCHEMA}.used_by u
        LEFT JOIN {SCHEMA}.classes ce ON ce.name = u.callee_class
        LEFT JOIN {SCHEMA}.classes cr ON cr.name = u.caller_class""",
    "stale": f"""
        SELECT 'file' AS kind, path AS item, 'not in its folder INDEX.md' AS reason
        FROM {SCHEMA}.files WHERE NOT in_index
        UNION ALL SELECT 'folder', path, 'no INDEX.md' FROM {SCHEMA}.folders WHERE NOT has_index
        UNION ALL SELECT 'class', name, 'not in CLASS_REGISTRY.md' FROM {SCHEMA}.classes
        WHERE NOT in_registry
        UNION ALL SELECT 'method', class || '.' || name, 'not in the registry method table'
        FROM {SCHEMA}.methods m WHERE NOT in_registry
          AND EXISTS (SELECT 1 FROM {SCHEMA}.classes c WHERE c.name = m.class AND c.in_registry)
        UNION ALL SELECT 'lint', path || ':' || line, message FROM {SCHEMA}.lint_findings""",
    "todo": f"""
        SELECT p.plan, pl.title AS plan_title, p.n, p.phase, p.status, p.depends_on,
               p.done_criterion
        FROM {SCHEMA}.phases p JOIN {SCHEMA}.plans pl ON pl.nn = p.plan
        WHERE lower(p.status) NOT LIKE 'done%'
        ORDER BY p.plan, try_cast(p.n AS INTEGER), p.n""",
}


class ProjectCatalog:
    """
    Purpose:
        Rebuild schema `project` in the lake's DuckDB from the repository: folders, files, classes,
        methods, used_by, contracts, test_cases, decisions, plans, phases, datasets, lint_findings,
        plus views tree, class_graph, stale and todo. Markdown and code stay the source of truth;
        the schema is dropped and rebuilt, never edited.

    Contract:
        Input:
            catalog:  LakeCatalog                -- read-write connection
            code:     CodeTableBuilder
            docs:     DocTableBuilder
            datasets: Mapping[str, DatasetSpec]  -- Config.datasets
            linter:   ContractLinter             -- fills lint_findings
            clock:    Clock                      -- run_at
        Output:
            instance; `rebuild(run_lint=True) -> dict[str, int]`
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- `project-catalog` (make project-catalog, make check)

    Test cases:
        TC-PJC-001  every table and view exists after rebuild; class count equals registry rows
        TC-PJC-002  rebuild is idempotent (same row counts, same tree)
        TC-PJC-003  stale lists an unindexed file and an unregistered class; empty on a clean repo
        TC-PJC-004  todo lists only phases not done
    """

    def __init__(
        self,
        catalog: LakeCatalog,
        code: CodeTableBuilder,
        docs: DocTableBuilder,
        datasets: Mapping[str, DatasetSpec],
        linter: ContractLinter,
        clock: Clock,
    ) -> None:
        self._catalog = catalog
        self._code = code
        self._docs = docs
        self._datasets = dict(datasets)
        self._linter = linter
        self._clock = clock

    def rebuild(self, run_lint: bool = True) -> dict[str, int]:
        """
        Purpose:
            Drop and recreate every table and view of schema `project` in one transaction.

        Contract:
            Input:
                run_lint: bool  -- False leaves lint_findings empty (faster; used by tests)
            Output:
                dict[str, int]  -- rows per table
            Raises:
                LakeError     -- DuckDB failure (schema left as before: the transaction rolls back)
                RuntimeError  -- git listing failed
        """
        tables = {**self._code.build_tables(), **self._docs.build_tables()}
        tables["datasets"] = self._build_datasets()
        tables["lint_findings"] = (
            self._build_lint() if run_lint else pd.DataFrame(columns=LINT_COLUMNS)
        )
        con = self._catalog.connection
        try:
            con.execute("BEGIN TRANSACTION")
            con.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
            con.execute(f"CREATE SCHEMA {SCHEMA}")
            for name, frame in tables.items():
                self._write_table(con, name, frame)
            for name, sql in VIEWS.items():
                con.execute(f"CREATE VIEW {SCHEMA}.{name} AS {sql}")
            con.execute("COMMIT")
        except duckdb.Error as exc:
            con.execute("ROLLBACK")
            raise LakeError(f"project catalog rebuild failed: {exc}") from exc
        counts = {name: len(frame) for name, frame in tables.items()}
        logger.info("project catalog rebuilt: %s", counts)
        return counts

    def _write_table(self, con: duckdb.DuckDBPyConnection, name: str, frame: pd.DataFrame) -> None:
        view = f"_project_{name}"
        con.register(view, frame)
        try:
            con.execute(f"CREATE TABLE {SCHEMA}.{name} AS SELECT * FROM {view}")
        finally:
            con.unregister(view)

    def _build_datasets(self) -> pd.DataFrame:
        rows = [
            [
                s.name,
                s.endpoint,
                s.sweep.kind,
                ", ".join(s.primary_key),
                s.known_on,
                s.refresh,
                "raw",
                s.sweep.param or "all",
                s.curated.partition_by,
                s.curated.path,
            ]
            for s in self._datasets.values()
        ]
        return pd.DataFrame(rows, columns=DATASET_COLUMNS)

    def _build_lint(self) -> pd.DataFrame:
        run_at = self._clock.get_now()
        rows = [[f.rule, f.path, f.line, f.message, run_at] for f in self._linter.run()]
        return pd.DataFrame(rows, columns=LINT_COLUMNS)
