"""Contract tests for core.AppPublisherSettings (plan 19 ph2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.app_publisher_settings import FILE, AppPublisherSettings
from quant_cn.core.exceptions import ConfigError

REPO = Path(__file__).resolve().parents[2]


# TC-APS-001
def test_tc_aps_001_repo_map_loads() -> None:
    settings = AppPublisherSettings.load(REPO)
    by_artist = settings.get_by_artist()
    assert len(by_artist) == len(settings.publishers)
    assert by_artist["542097913"].code == "002558.SZ"
    assert by_artist["1467190250"].code is None  # miHoYo, not listed
    a_share = settings.get_a_share()
    assert a_share["300533.SZ"] == "冰川网络" and "00700.HK" not in a_share


# TC-APS-002
def test_tc_aps_002_duplicate_and_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        AppPublisherSettings.load(tmp_path)
    (tmp_path / FILE).parent.mkdir(parents=True)
    row = '{artist_id: "1", artist: a, company: 甲, code: "A.SZ"}'
    (tmp_path / FILE).write_text(f"publishers: [{row}, {row}]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate"):
        AppPublisherSettings.load(tmp_path)
