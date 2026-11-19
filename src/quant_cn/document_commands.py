"""Document CLI commands: `download-docs` (plan 12), `import-labels`, `build-graph` (plan 28)."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd
from rich.console import Console

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import LakeError
from quant_cn.core.label_source import LabelSource
from quant_cn.core.ticker_normalizer import TickerNormalizer
from quant_cn.data_loading.document_downloader import DocumentDownloader
from quant_cn.industry_graph.base_edge_reader import BaseEdgeReader
from quant_cn.industry_graph.company_period_builder import CompanyPeriodBuilder
from quant_cn.industry_graph.counterparty_edge_reader import CounterpartyEdgeReader
from quant_cn.industry_graph.deal_edge_reader import DealEdgeReader
from quant_cn.industry_graph.edge_span_builder import EdgeSpanBuilder
from quant_cn.industry_graph.entity_resolver import EntityResolver
from quant_cn.industry_graph.game_company_builder import ALIAS_COLUMNS, GameCompanyBuilder
from quant_cn.industry_graph.graph_builder import GraphBuilder
from quant_cn.industry_graph.legacy_label_importer import LegacyLabelImporter
from quant_cn.industry_graph.node_edge_builder import NodeEdgeBuilder
from quant_cn.industry_graph.node_lineage_builder import NodeLineageBuilder
from quant_cn.industry_graph.node_member_builder import NodeMemberBuilder
from quant_cn.industry_graph.product_matcher import ProductMatcher
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy
from quant_cn.industry_graph.taxonomy_change_set import TaxonomyChangeSet
from quant_cn.industry_graph.top_five_edge_reader import TopFiveEdgeReader
from quant_cn.lake.document_views import DocumentViews
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.label_store import LabelStore
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter


class DocumentCommands:
    """
    Purpose:
        The document-side CLI command `download-docs` (plan 12 phase 2, D-101): for each source,
        list the PDFs not yet in the manifest (counts per doc type), release the catalog, then
        download them (unless `--dry-run`) and refresh `meta.documents`.
        `import-labels` (plan 28 ph0, D-161) imports the label files of config/label_sources.yaml
        (optionally only `--sets`) into derived/labels parquet and prints rows per set.
        `build-graph` (plan 28 ph4) rebuilds derived/graph company_edge, edge_span and
        company_period from the label store and entity_map with GraphBuilder (A-share full,
        current and former short names from curated stock_company / stock_basic / namechange
        when those views exist; `--as-of` for point-in-time spans), then node_member
        (NodeMemberBuilder over curated fina_mainbz_p with the companies' Shenwan L2 / L3 codes
        and the annual reports' dates, taxonomy v0 plus the accepted versions of
        config/industry_chain/_changes), node_edge (NodeEdgeBuilder over company_edge and
        node_member, plan 28 ph4d) and node_lineage (NodeLineageBuilder), then (plan 31
        ph2, when curated game_license exists) game_company from the 版号 lists and the
        game_alias table (GameCompanyBuilder), and prints rows per table.

    Contract:
        Input:
            console: Console
        Output:
            instance; `build_parser`, `_run_download_docs`, `_run_import_labels`,
            `_run_build_graph` (dispatched by QuantCnCli.run)
        Raises:
            (none at construction)

    Used by:
        cli.QuantCnCli  -- dispatch fallback

    Test cases:
        TC-QCC-010  download-docs --dry-run prints counts per type to download and exits 0
        TC-QCC-015  import-labels --sets filters config label sources and prints rows per set
        TC-QCC-016  build-graph writes company_edge and edge_span from the label store and
                    prints rows per table; it runs without the reference views
    """

    def __init__(self, console: Console) -> None:
        self._console = console

    @staticmethod
    def build_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
        """
        Purpose:
            Add the `download-docs`, `import-labels` and `build-graph` subcommands and their
            options to the CLI parser.

        Contract:
            Input:
                sub: argparse subparsers of QuantCnCli
            Output:
                None
            Raises:
                (none)
        """
        dd = sub.add_parser("download-docs", help="download listed PDFs into documents/ (D-101)")
        dd.add_argument(
            "--sources", required=True, help="comma-separated config/documents.yaml keys"
        )
        dd.add_argument("--types", help="comma-separated doc types (default: all of the source)")
        dd.add_argument("--start", help="publication date from, YYYYMMDD")
        dd.add_argument("--end", help="publication date to, YYYYMMDD")
        dd.add_argument("--limit", type=int, help="at most this many downloads per source")
        dd.add_argument(
            "--workers", type=int, help="override the source's workers in documents.yaml"
        )
        dd.add_argument("--dry-run", action="store_true", help="count candidates per type only")
        il = sub.add_parser("import-labels", help="label files -> derived/labels parquet (plan 28)")
        il.add_argument("--sets", help="comma-separated label sets (default: every source)")
        bg = sub.add_parser("build-graph", help="label store -> derived/graph tables (plan 28)")
        bg.add_argument("--as-of", help="spans as known on this date, YYYYMMDD")

    def _run_download_docs(self, config: Config, args: argparse.Namespace) -> int:
        types = self._parse_list(args.types)
        sources = self._parse_list(args.sources) or []
        catalog = LakeCatalog(config.lake.root, config.datasets)
        downloader = DocumentDownloader(
            config.lake.root,
            LakeQuery(catalog),
            config.documents,
            Clock(),
            workers_override=args.workers,
        )
        try:
            todo = {s: downloader.list_todo(s, types, args.start, args.end) for s in sources}
        finally:
            catalog.close()  # downloads need no catalog: a metadata sweep may run meanwhile
        for source, frame in todo.items():
            counts = frame["doc_type"].value_counts().sort_index()
            self._console.print(f"{source}: {len(frame)} to download")
            for doc_type, n in counts.items():
                self._console.print(f"  {doc_type}: {n}")
            if not args.dry_run:
                report = downloader.run(frame, args.limit)
                self._console.print(f"{report.name}: {report.message}, {report.rows / 1e6:.1f} MB")
        if not args.dry_run:
            self._refresh_views(config)
        return 0

    def _run_import_labels(self, config: Config, args: argparse.Namespace) -> int:
        wanted = self._parse_list(args.sets)
        listed = LabelSource.read_all(config.repo_root / "config" / "label_sources.yaml")
        sources = [s for s in listed if wanted is None or s.label_set in wanted]
        store = LabelStore(ParquetWriter(config.lake.root), config.lake.root, DateCodec())
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            importer = LegacyLabelImporter(
                store, LakeQuery(catalog), config.lake.root, TickerNormalizer()
            )
            written = importer.run(sources)
        finally:
            catalog.close()
        for label_set, rows in written.items():
            self._console.print(f"{label_set}: {rows} rows")
        return 0

    def _run_build_graph(self, config: Config, args: argparse.Namespace) -> int:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            query = LakeQuery(catalog)
            full = self._read_pairs(query, "curated.stock_company", "com_name", "TRUE")
            short = self._read_pairs(query, "curated.stock_basic", "name", "TRUE")
            short += self._read_pairs(query, "curated.namechange", "name", "end_date IS NULL")
            former = self._read_pairs(query, "curated.namechange", "name", "end_date IS NOT NULL")
            revenue, sw_codes = self._read_revenue(query)
            licenses = (
                query.sql("SELECT * FROM curated.game_license")
                if query.has_view("curated.game_license")
                else pd.DataFrame()
            )
        finally:
            catalog.close()
        writer = ParquetWriter(config.lake.root)
        items = CounterpartyEdgeReader("items")
        readers: dict[str, BaseEdgeReader] = {
            "report_parse": TopFiveEdgeReader(),
            "applications": CounterpartyEdgeReader("counterparties"),
            "inquiry_counterparties": items,
            "prospectus_counterparties": items,
            "ir_counterparties": items,
            "broker_counterparties": items,
            "deals": DealEdgeReader(),
        }
        labels = LabelStore(writer, config.lake.root, DateCodec())
        builder = GraphBuilder(
            labels,
            GraphStore(writer, config.lake.root),
            readers,
            EdgeSpanBuilder(DateCodec()),
            CompanyPeriodBuilder(labels),
        )
        counts = builder.build(full, short, former, args.as_of)
        folder = config.repo_root / "config" / "industry_chain"
        if folder.exists():  # node_member and node_lineage need the taxonomy
            counts["node_member"] = self._write_members(config, labels, folder, revenue, sw_codes)
            counts["node_edge"] = self._write_node_edges(config, folder, args.as_of)
            lineage = NodeLineageBuilder(folder).build_lineage(TaxonomyChangeSet.read_all(folder))
            GraphStore(writer, config.lake.root).write("node_lineage", lineage)
            counts["node_lineage"] = len(lineage)
        if not licenses.empty:
            counts["game_company"] = self._write_games(config, licenses, full, short, former)
        for table, rows in counts.items():
            self._console.print(f"{table}: {rows} rows")
        return 0

    @staticmethod
    def _write_games(
        config: Config,
        licenses: pd.DataFrame,
        full: list[tuple[str, str]],
        short: list[tuple[str, str]],
        former: list[tuple[str, str]],
    ) -> int:
        store = GraphStore(ParquetWriter(config.lake.root), config.lake.root)
        proposals = (
            store.read("game_alias") if "game_alias" in store.list_tables() else pd.DataFrame()
        )
        aliases = {
            str(r["name"]): {c: r.get(c) for c in ALIAS_COLUMNS}
            for r in proposals.to_dict("records")
        }
        builder = GameCompanyBuilder(EntityResolver(full, short, former_names=former), aliases)
        links = builder.build_links(licenses)
        store.write("game_company", links)
        return len(links)

    @staticmethod
    def _write_members(
        config: Config,
        labels: LabelStore,
        folder: Path,
        revenue: pd.DataFrame,
        sw_codes: dict[str, list[str]],
    ) -> int:
        taxonomy = ProductTaxonomy(folder, TaxonomyChangeSet.read_all(folder))
        nodes = NodeMemberBuilder(ProductMatcher(taxonomy), taxonomy, DateCodec())
        filed = labels.read("report_parse")
        keys = zip(filed["ts_code"], filed["period"], strict=True)
        members = nodes.build_members(
            revenue, sw_codes, dict(zip(keys, filed["known_on"], strict=True))
        )
        GraphStore(ParquetWriter(config.lake.root), config.lake.root).write("node_member", members)
        return len(members)

    @staticmethod
    def _write_node_edges(config: Config, folder: Path, as_of: str | None) -> int:
        store = GraphStore(ParquetWriter(config.lake.root), config.lake.root)
        taxonomy = ProductTaxonomy(folder, TaxonomyChangeSet.read_all(folder))
        builder = NodeEdgeBuilder(taxonomy, DateCodec())
        cols = ["src", "dst", "relation", "period", "known_on"]
        node_edges = builder.build_node_edges(
            store.read("company_edge", columns=cols), store.read("node_member"), as_of
        )
        store.write("node_edge", node_edges)
        return len(node_edges)

    @staticmethod
    def _read_revenue(query: LakeQuery) -> tuple[pd.DataFrame, dict[str, list[str]]]:
        empty = pd.DataFrame(columns=["ts_code", "end_date", "bz_item", "bz_sales"])
        if not query.has_view("curated.fina_mainbz_p"):
            return empty, {}
        revenue = query.sql(
            "SELECT ts_code, end_date, bz_item, bz_sales FROM curated.fina_mainbz_p "
            "WHERE bz_sales IS NOT NULL"
        )
        codes: dict[str, list[str]] = {}
        if query.has_view("curated.index_member_all") and query.has_view("curated.index_classify"):
            frame = query.sql(
                "SELECT m.ts_code, c2.industry_code AS l2, c3.industry_code AS l3 "
                "FROM curated.index_member_all m "
                "LEFT JOIN curated.index_classify c2 ON c2.index_code = m.l2_code "
                "LEFT JOIN curated.index_classify c3 ON c3.index_code = m.l3_code "
                "WHERE m.out_date IS NULL OR m.out_date = ''"
            )
            for ts, l2, l3 in frame.itertuples(index=False):
                codes[str(ts)] = [str(c) for c in (l2, l3) if isinstance(c, str)]
        return revenue, codes

    @staticmethod
    def _read_pairs(query: LakeQuery, view: str, column: str, where: str) -> list[tuple[str, str]]:
        if not query.has_view(view):
            return []
        sql = f"SELECT ts_code, {column} FROM {view} WHERE {column} IS NOT NULL AND {where}"
        frame = query.sql(sql)
        return [(str(ts), str(name)) for ts, name in frame.itertuples(index=False)]

    @staticmethod
    def _parse_list(value: str | None) -> list[str] | None:
        return [v.strip() for v in value.split(",") if v.strip()] if value else None

    def _refresh_views(self, config: Config) -> None:
        catalog = LakeCatalog(config.lake.root, config.datasets)
        try:
            DocumentViews(config.lake.root, catalog.connection).refresh()
        except (LakeError, duckdb.Error) as exc:  # catalog busy: views refresh on the next run
            self._console.print(f"[yellow]meta.documents not refreshed:[/yellow] {exc}")
        finally:
            catalog.close()
