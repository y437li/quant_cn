"""Contract tests for visualization.MorningReportBuilder (plan 15 ph7e)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from quant_cn.core.exceptions import LakeError
from quant_cn.core.mail_sender import MailContent, MailSender
from quant_cn.visualization.monitor_report_renderer import MonitorReportRenderer
from quant_cn.visualization.morning_report_builder import MorningReportBuilder
from quant_cn.visualization.opportunity_report_renderer import OpportunityReportRenderer
from tests.visualization.report_docs import build_docs


class FakeSender:
    def __init__(self) -> None:
        self.sent: list[MailContent] = []

    def run(self, content: MailContent) -> None:
        self.sent.append(content)


def _write_docs(folder: Path, as_of: str = "20261112") -> Path:
    folder.mkdir(exist_ok=True)
    for name, doc in build_docs(as_of).items():
        if doc is not None:
            (folder / f"{name}.json").write_text(
                json.dumps(doc, ensure_ascii=False), encoding="utf-8"
            )
    return folder


def _build(folder: Path, sender: FakeSender | None = None) -> MorningReportBuilder:
    return MorningReportBuilder(
        folder,
        MonitorReportRenderer(),
        OpportunityReportRenderer(),
        cast(MailSender, sender) if sender else None,
    )


def test_tc_mrb_001_dry_run(tmp_path: Path) -> None:
    """TC-MRB-001"""
    folder = _write_docs(tmp_path / "data")
    builder = _build(folder)
    assert builder.read_documents()["opportunities"] is None
    out = builder.run("20261113", "20261112", tmp_path)
    assert [(o.name, o.action) for o in out] == [("monitor", "written"), ("opportunity", "written")]
    assert (
        (tmp_path / "morning_monitor_20261113.html")
        .read_text(encoding="utf-8")
        .startswith("<!doctype")
    )
    (folder / "etf_proxy.json").write_text("{not json")
    with pytest.raises(LakeError):
        builder.read_documents()


def test_tc_mrb_002_stale(tmp_path: Path) -> None:
    """TC-MRB-002"""
    sender = FakeSender()
    out = _build(_write_docs(tmp_path / "data", "20261111"), sender).run(
        "20261113", "20261112", None
    )
    assert [o.action for o in out] == ["skipped", "skipped"] and sender.sent == []
    assert "holdings_risk 20261111" in out[0].detail and "watchlist 20261111" in out[1].detail


def test_tc_mrb_003_send(tmp_path: Path) -> None:
    """TC-MRB-003"""
    sender = FakeSender()
    out = _build(_write_docs(tmp_path / "data"), sender).run("20261113", "20261112", None)
    assert [o.action for o in out] == ["sent", "sent"] and len(sender.sent) == 2
    assert sender.sent[0].subject.startswith("持仓监测") and sender.sent[1].subject.startswith(
        "机会清单"
    )
    with pytest.raises(LakeError):
        _build(tmp_path / "data").run("20261113", "20261112", None)
