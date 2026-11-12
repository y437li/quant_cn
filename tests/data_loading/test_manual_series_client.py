"""Contract tests for data_loading.ManualSeriesClient (plan 20 phase 1, D-139)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.exceptions import ConfigError
from quant_cn.data_loading.manual_series_client import COLUMNS, ManualSeriesClient

SERIES = """
series:
  - {id: clarksons_newbuild, name: 克拉克森新造船价格指数, unit: point, freq: weekly, kind: index,
     links: ["600150.SH"]}
  - {id: tio2_rutile, name: 钛白粉金红石型, unit: CNY/t, freq: weekly, kind: price}
"""
URL = "https://example.com/a"


def _write(root: Path, name: str, text: str) -> None:
    (root / "config").mkdir(exist_ok=True)
    (root / "config" / name).write_text(text, encoding="utf-8")


def _build_obs(series: str, date: str, value: float, published: str, extra: str = "") -> str:
    return (
        f"  - {{series: {series}, date: '{date}', value: {value}, published: '{published}', "
        f"source_url: '{URL}'{extra}}}\n"
    )


# TC-MSC-001
def test_tc_msc_001_loads_both_files(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "manual_series.yaml",
        SERIES
        + "observations:\n"
        + _build_obs("clarksons_newbuild", "20261030", 187.2, "20261102"),
    )
    client = ManualSeriesClient(tmp_path)
    public = client.query("series", {}, [])
    assert list(public.columns) == COLUMNS and len(public) == 1
    assert public.iloc[0]["name"] == "克拉克森新造船价格指数" and public.iloc[0]["licensed"] == 0
    _write(
        tmp_path,
        "local.manual_series.yaml",
        "observations:\n" + _build_obs("tio2_rutile", "20261031", 13500, "20261031"),
    )
    both = client.query("series", {}, [])
    tio2 = both[both["series"] == "tio2_rutile"].iloc[0]
    assert len(both) == 2 and tio2["licensed"] == 1 and tio2["unit"] == "CNY/t"


# TC-MSC-002
def test_tc_msc_002_invalid_rows(tmp_path: Path) -> None:
    client = ManualSeriesClient(tmp_path)
    cases = [
        _build_obs("clarksons_newbuild", "20261030", 1.0, "20261029"),  # published before date
        _build_obs("nope", "20261030", 1.0, "20261030"),  # unknown series
        _build_obs("clarksons_newbuild", "20261030", 1.0, "20261030") * 2,  # duplicate
    ]
    for body in cases:
        _write(tmp_path, "manual_series.yaml", SERIES + "observations:\n" + body)
        with pytest.raises(ConfigError):
            client.query("series", {}, [])
    revised = _build_obs("clarksons_newbuild", "20261030", 1.0, "20261030") + _build_obs(
        "clarksons_newbuild", "20261030", 1.1, "20261106", ", revision: true"
    )
    _write(tmp_path, "manual_series.yaml", SERIES + "observations:\n" + revised)
    frame = client.query("series", {}, [])
    assert frame["value"].tolist() == [1.0, 1.1] and frame["revision"].tolist() == [0, 1]


# TC-MSC-003
def test_tc_msc_003_endpoint_and_yaml(tmp_path: Path) -> None:
    client = ManualSeriesClient(tmp_path)
    assert client.query("series", {}, []).empty
    with pytest.raises(ConfigError):
        client.query("other", {}, [])
    _write(tmp_path, "manual_series.yaml", "series: [unclosed\n")
    with pytest.raises(ConfigError):
        client.query("series", {}, [])
