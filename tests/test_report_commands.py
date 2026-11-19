"""Contract tests for ReportCommands (`morning-report` ph7e, `macro-monitor` ph7h)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console

from quant_cn.cli import QuantCnCli
from quant_cn.core.config import Config
from quant_cn.core.message_sender import MessageSender
from quant_cn.lake.compactor import Compactor
from quant_cn.report_commands import ReportCommands
from tests.calculation.test_futures_monitor_builder import _write
from tests.calculation.test_macro_monitor_builder import _write_all
from tests.calculation.test_rates_fx_monitor_builder import _write as _write_rates_fx
from tests.calculation.test_volatility_monitor_builder import _write as _write_volatility
from tests.portfolio.test_etf_cta_book import _write as _write_etf
from tests.portfolio.test_small_cap_watch_builder import _write as _write_smallcap
from tests.support import MiniLake, Sample, SampleFactorLake
from tests.visualization.test_morning_report_builder import _write_docs


def _write_calendar(lake: MiniLake, config: Config) -> None:
    spec = config.get_dataset("trade_cal")
    days = Sample.build_trade_cal(["20261111", "20261112", "20261113"])
    lake.writer.write_raw(spec, "all", days)
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)
    lake.catalog.close()


def _run(config: Config, data: Path, out: Path) -> str:
    console = Console(record=True, width=300)
    argv = [
        "morning-report",
        "--dry-run",
        "--data",
        str(data),
        "--out",
        str(out),
        "--today",
        "20261113",
    ]
    assert QuantCnCli(config, console).run(argv) == 0
    return console.export_text()


def test_tc_rpc_001_dry_run(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-001"""
    _write_calendar(lake, config)
    text = _run(config, _write_docs(tmp_path / "data"), tmp_path)
    assert "monitor: written" in text and "opportunity: written" in text
    assert (tmp_path / "morning_opportunity_20261113.html").exists()


def test_tc_rpc_002_stale(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-002"""
    _write_calendar(lake, config)
    text = _run(config, _write_docs(tmp_path / "data", "20261111"), tmp_path)
    assert "monitor: skipped data older than 20261112" in text
    assert not (tmp_path / "morning_monitor_20261113.html").exists()


def test_tc_rpc_003_macro_monitor(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-003"""
    _write_all(lake, config)
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert QuantCnCli(config, console).run(["macro-monitor", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "macro_monitor.json").exists()
    assert "macro monitor ->" in console.export_text()


def test_tc_rpc_004_futures_monitor(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-004"""
    _write(lake, config)
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert QuantCnCli(config, console).run(["futures-monitor", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "futures_monitor.json").exists()
    assert "futures monitor:" in console.export_text()


def test_tc_rpc_005_volatility_monitor(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-005"""
    _write_volatility(lake, config)
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert QuantCnCli(config, console).run(["volatility-monitor", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "volatility_monitor.json").exists()
    assert "volatility monitor:" in console.export_text()


def test_tc_rpc_011_etf_cta(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-011"""
    source = Path(__file__).resolve().parents[1] / "config" / "etf_cta.yaml"
    (config.repo_root / "config" / "etf_cta.yaml").write_text(source.read_text(encoding="utf-8"))
    _write_etf(lake, config)
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert QuantCnCli(config, console).run(["etf-cta", "--out", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "etf_cta.json").read_text(encoding="utf-8"))
    assert doc["decision_date"] == "20261030" and "etf cta:" in console.export_text()


class FakeSender(MessageSender):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def run(self, handle: str, text: str, images: Sequence[Path] = ()) -> None:
        self.sent.append((handle, text))
        self.images = list(images)


def test_tc_rpc_006_notify(config: Config) -> None:
    """TC-RPC-006"""
    (config.repo_root / "config" / "local.notify.yaml").write_text(
        "recipients:\n  - {name: Ella, handle: '+10000000000'}\n  - {name: 妈妈, handle: '+86'}\n",
        encoding="utf-8",
    )
    sender, console = FakeSender(), Console(record=True, width=300)
    cmd = ReportCommands(console, sender)
    args = argparse.Namespace(text="测试", to="ella", dry_run=False)
    assert cmd._run_notify(config, args) == 0
    assert sender.sent == [("+10000000000", "测试")]
    assert cmd._run_notify(config, argparse.Namespace(text="x", to=None, dry_run=True)) == 0
    assert len(sender.sent) == 1 and "dry run" in console.export_text()


def test_tc_rpc_007_notify_from_documents(config: Config, tmp_path: Path) -> None:
    """TC-RPC-007"""
    (config.repo_root / "config" / "local.notify.yaml").write_text(
        "recipients:\n  - {name: 妈妈, handle: '+86'}\n", encoding="utf-8"
    )
    wl = {"entries": [{"code": "601398.SH", "name": "工商银行", "price": 7.98, "buy_low": 7.4,
                       "buy_high": 8.0, "status": "in", "condition_status": "wait"}]}  # fmt: skip
    (tmp_path / "watchlist.json").write_text(json.dumps(wl, ensure_ascii=False), encoding="utf-8")
    sender = FakeSender()
    cmd = ReportCommands(Console(record=True, width=300), sender)
    args = argparse.Namespace(text=None, to=None, dry_run=False, sample=False, data=tmp_path,
                              today="20261113",
                              node=None, shot_script=None, images=tmp_path / "pics",
                              app_url="")  # fmt: skip
    assert cmd._run_notify(config, args) == 0
    assert len(sender.sent) == 1 and "工商银行今天收在 7.98 元" in sender.sent[0][1]
    assert cmd._run_notify(config, args) == 0 and len(sender.sent) == 1  # sent once
    pics = tmp_path / "pics"
    pic = pics / "p.png"

    def shoot(*_: object) -> list[Path]:
        pics.mkdir(exist_ok=True)
        pic.write_bytes(b"png")
        return [pic]

    cmd._build_images = shoot  # type: ignore[method-assign]
    (tmp_path / "notify_sent.json").write_text("[]", encoding="utf-8")
    assert cmd._run_notify(config, args) == 0 and sender.images == [pic]
    assert pic.exists()  # kept while Messages uploads it
    cmd._run_notify(config, args)
    assert not pic.exists() and not pics.exists()  # cleaned up by the next run


def test_tc_rpc_009_margin_panel(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-009"""
    w = SampleFactorLake.write
    day = "20261112"
    w(
        lake,
        config,
        "margin_detail",
        [
            {
                "ts_code": "A",
                "trade_date": day,
                "rzye": 1e9,
                "rzmre": 1e7,
                "rzche": 1e7,
                "rqye": 1e6,
                "rqyl": 1e4,
                "rqmcl": 100.0,
            }
        ],
    )
    w(lake, config, "daily", [{"ts_code": "A", "trade_date": day, "close": 10.0}])
    w(lake, config, "daily_basic", [{"ts_code": "A", "trade_date": day, "circ_mv": 1e6}])
    lake.catalog.close()
    console = Console(record=True, width=300)
    argv = ["margin-panel", "--out", str(tmp_path), "--today", "20261113"]
    assert QuantCnCli(config, console).run(argv) == 0
    assert (
        tmp_path / "margin" / "A.json"
    ).exists() and "margin panel: 1 stocks" in console.export_text()


def test_tc_rpc_008_notify_sample(config: Config, tmp_path: Path) -> None:
    """TC-RPC-008"""
    (config.repo_root / "config" / "local.notify.yaml").write_text(
        "recipients:\n  - {name: 我, handle: me@example.com}\n", encoding="utf-8"
    )
    macro = {"new_prints": [], "series": [{"key": "cpi", "value": 0.7, "month": "202610"}]}
    (tmp_path / "macro_monitor.json").write_text(json.dumps(macro), encoding="utf-8")
    sender = FakeSender()
    cmd = ReportCommands(Console(record=True, width=300), sender)
    args = argparse.Namespace(text=None, to="我", dry_run=False, sample=True, data=tmp_path,
                              today="20261113", node=None, shot_script=None,
                              images=tmp_path / "pics", app_url="")  # fmt: skip
    assert cmd._run_notify(config, args) == 0
    assert "样例" in sender.sent[0][1] and "10 月物价" in sender.sent[0][1]
    assert not (tmp_path / "notify_sent.json").exists()


def test_tc_rpc_010_buyback_events(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-010"""
    w = SampleFactorLake.write
    w(
        lake,
        config,
        "repurchase",
        [{"ts_code": "A", "ann_date": "20261112", "proc": "预案", "amount": 3e9}],
    )
    w(lake, config, "stock_basic", [{"ts_code": "A", "name": "甲", "list_status": "L"}])
    w(
        lake,
        config,
        "daily_basic",
        [{"ts_code": "A", "trade_date": "20261112", "total_mv": 1e7, "close": 10.0}],
    )
    w(lake, config, "daily", [{"ts_code": "A", "trade_date": "20261112", "close": 10.0}])
    w(lake, config, "stk_holdertrade", [{"ts_code": "A", "ann_date": "20261112", "in_de": "IN",
                                         "holder_name": "甲", "change_vol": 1.0}])  # fmt: skip
    w(lake, config, "cninfo_keyword_announcements",
      [{"ann_id": "1", "sec_code": "B", "ann_date": "20261112", "title": "限制"}])  # fmt: skip
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert (
        QuantCnCli(config, console).run(
            ["buyback-events", "--out", str(tmp_path), "--today", "20261113"]
        )
        == 0
    )
    doc = json.loads((tmp_path / "buybacks.json").read_text(encoding="utf-8"))
    assert doc["large_plans"][0]["pct"] == 3.0
    monitor = json.loads((tmp_path / "buyback_monitor.json").read_text(encoding="utf-8"))
    assert monitor["buyback"]["totals"]["all"]["count"] == 0  # no price cap, no label: dropped
    assert monitor["increase"]["live"] == []


def test_tc_rpc_012_smallcap_watch(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-012"""
    source = Path(__file__).resolve().parents[1] / "config" / "smallcap_watch.yaml"
    target = config.repo_root / "config" / "smallcap_watch.yaml"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    _write_smallcap(lake, config)
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert QuantCnCli(config, console).run(["smallcap-watch", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "smallcap_watch.json").exists()
    assert "small-cap watch:" in console.export_text()


def test_tc_rpc_013_rates_fx_monitor(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    """TC-RPC-013"""
    source = Path(__file__).resolve().parents[1] / "config" / "rates_fx_monitor.yaml"
    target = config.repo_root / "config" / "rates_fx_monitor.yaml"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    _write_rates_fx(lake, config)
    lake.catalog.close()
    console = Console(record=True, width=300)
    assert QuantCnCli(config, console).run(["rates-fx-monitor", "--out", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "rates_fx_monitor.json").read_text(encoding="utf-8"))
    assert {r["key"] for r in doc["rows"]} >= {"cn_10y", "usdcnh"}
    assert "rates-fx monitor:" in console.export_text()
