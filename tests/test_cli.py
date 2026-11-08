from __future__ import annotations

import json

import pandas as pd
import pytest
from rich.console import Console

from quant_cn.cli import QuantCnCli
from quant_cn.core.config import Config
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.parquet_writer import ParquetWriter
from tests.support import Sample


# TC-QCC-001
def test_tc_qcc_001_doctor_hides_token(config: Config) -> None:
    config.lake.root.mkdir(parents=True)
    console = Console(record=True, width=200)
    code = QuantCnCli(config, console).run(["doctor"])
    text = console.export_text()
    assert str(config.lake.root) in text and "set" in text
    assert "test-token" not in text and code == 0


# TC-QCC-002
def test_tc_qcc_002_dry_run(config: Config) -> None:
    console = Console(record=True, width=200)
    code = QuantCnCli(config, console).run(
        ["download", "--dry-run", "--no-progress", "--end", "20260828"]
    )
    assert code == 0 and "stock_basic" in console.export_text()


# TC-QCC-003
def test_tc_qcc_003_curate(config: Config) -> None:
    writer = ParquetWriter(config.lake.root)
    writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(["20260828"]))
    LakeCatalog(config.lake.root, config.datasets).close()
    first = Console(record=True, width=200)
    assert QuantCnCli(config, first).run(["curate", "--no-progress"]) == 0
    second = Console(record=True, width=200)
    assert QuantCnCli(config, second).run(["curate", "--no-progress"]) == 0
    assert "CHANGED" not in second.export_text()


# TC-QCC-004
def test_tc_qcc_004_query(config: Config) -> None:
    catalog = LakeCatalog(config.lake.root, config.datasets)
    assert catalog.connection is not None
    catalog.close()
    console = Console(record=True, width=200)
    assert QuantCnCli(config, console).run(["query", "SELECT 41 + 1 AS answer"]) == 0
    assert "42" in console.export_text()
    assert (
        QuantCnCli(config, Console(record=True)).run(["query", "CREATE TABLE meta.t (a INT)"]) == 1
    )


# TC-QCC-005
def test_tc_qcc_005_calendar_horizon(config: Config) -> None:
    writer = ParquetWriter(config.lake.root)
    writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(["20260105"]))
    QuantCnCli(config, Console(record=True)).run(["curate", "--no-progress"])
    console = Console(record=True, width=200)
    QuantCnCli(config, console).run(["doctor"])
    text = console.export_text()
    assert "calendar horizon" in text and "20260105" in text and "refresh trade_cal" in text


# TC-QCC-006
def test_tc_qcc_006_prefect_unreachable(config: Config, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PREFECT_API_URL", "http://127.0.0.1:9/api")
    console = Console(record=True, width=200)
    code = QuantCnCli(config, console).run(["doctor"])
    assert "unreachable" in console.export_text()
    assert code == QuantCnCli(config, Console(record=True)).run(["doctor"])


# TC-QCC-007
def test_tc_qcc_007_rebuild_orphans(config: Config) -> None:
    writer = ParquetWriter(config.lake.root)
    writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(["20260105"]))
    QuantCnCli(config, Console(record=True)).run(["curate", "--no-progress"])
    catalog = LakeCatalog(config.lake.root, config.datasets)
    FetchLog(catalog).mark_done("trade_cal", "gone", 3, None)
    FetchLog(catalog).save()
    catalog.close()
    console = Console(record=True, width=200)
    assert QuantCnCli(config, console).run(["rebuild"]) == 0
    assert "1 orphan rows" in console.export_text()
    record = json.loads(
        (config.lake.root / "meta" / "manifest" / "fetch_log_orphans.json").read_text()
    )
    assert record["removed"] == {"trade_cal": ["gone"]}


# TC-QCC-008
def test_tc_qcc_008_release_lags(config: Config) -> None:
    spec = config.get_dataset("macro_release_pmi")
    rows = pd.DataFrame(
        [
            {
                "series": "pmi",
                "release_date": "20221007",
                "actual": 50.1,
                "forecast": None,
                "previous": None,
            }
        ]
    )
    ParquetWriter(config.lake.root).write_raw(spec, "all", rows)
    QuantCnCli(config, Console(record=True)).run(["curate", "--no-progress"])
    console = Console(record=True, width=200)
    assert QuantCnCli(config, console).run(["release-lags"]) == 0
    text = console.export_text()
    assert "cn_pmi: rule 7d, observed max 7d over 1 releases -> ok" in text


# TC-QCC-009
def test_tc_qcc_009_evaluate_empty(config: Config) -> None:
    console = Console(record=True, width=200)
    assert QuantCnCli(config, console).run(["evaluate", "--no-progress"]) == 0
    assert "0 factors" in console.export_text()
    assert not (config.lake.root / "derived" / "reports").exists()


# TC-QCC-010
def test_tc_qcc_010_download_docs_dry_run(config: Config) -> None:
    folder = config.lake.root / "curated" / "documents" / "em_industry_reports" / "year=2026"
    folder.mkdir(parents=True)
    rows = {"info_code": ["A1", "A2"], "em_industry_code": ["101", "102"], "title": ["x", "y"],
            "publish_date": ["20261031", "20261101"]}  # fmt: skip
    pd.DataFrame(rows).to_parquet(folder / "part-0.parquet")
    catalog = LakeCatalog(config.lake.root, config.datasets)
    catalog.refresh_views()
    catalog.close()
    console = Console(record=True, width=200)
    argv = ["download-docs", "--sources", "em_industry", "--dry-run"]
    assert QuantCnCli(config, console).run(argv) == 0
    text = console.export_text()
    assert "em_industry: 2 to download" in text and "industry_report: 2" in text
