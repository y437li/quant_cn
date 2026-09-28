from __future__ import annotations

from rich.console import Console

from quant_cn.cli import QuantCnCli
from quant_cn.core.config import Config
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
