from __future__ import annotations

from rich.console import Console

from quant_cn.cli import QuantCnCli
from quant_cn.core.config import Config


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
