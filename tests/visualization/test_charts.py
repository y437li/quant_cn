from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.exceptions import SchemaError
from quant_cn.core.frames import PRICE_PANEL
from quant_cn.visualization.chart_theme import ChartTheme, Mode
from quant_cn.visualization.price_chart import PriceChart


@pytest.fixture
def prices() -> pd.DataFrame:
    rows = [
        {
            "trade_date": d,
            "ts_code": "000001.SZ",
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": c,
            "pre_close": 10.0,
            "vol": 1000.0,
            "amount": 1.0,
            "adj_factor": 2.0,
            "close_adj": c * 2.0,
        }
        for d, c in (("20260827", 10.5), ("20260828", 9.5), ("20260831", 10.0))
    ]
    return PRICE_PANEL.normalize(pd.DataFrame(rows), strict=True)


def build_chart(adjusted: bool = True, mode: Mode = "light") -> PriceChart:
    return PriceChart(ChartTheme.from_mode(mode), "000001.SZ", DateCodec(), adjusted=adjusted)


# TC-CT-001
def test_tc_ct_001_modes() -> None:
    light, dark = ChartTheme.from_mode("light"), ChartTheme.from_mode("dark")
    assert light.surface != dark.surface and (light.up, dark.up) == ("#e34948", "#e66767")
    with pytest.raises(ValueError):
        ChartTheme.from_mode(cast(Mode, "sepia"))


# TC-BCA-001
def test_tc_bca_001_theme_applied(prices: pd.DataFrame) -> None:
    fig = build_chart(mode="dark").render(prices)
    assert fig.layout.paper_bgcolor == "#1a1a19" and fig.layout.font.color == "#ffffff"
    assert fig.layout.xaxis.gridcolor == "#383835" and fig.layout.width == 960


# TC-BCA-002
def test_tc_bca_002_exports(prices: pd.DataFrame, tmp_path: Path) -> None:
    chart = build_chart()
    html = chart.to_html(prices)
    assert "<div" in html and "plotly" in html and "<html" not in html
    out = chart.write_html(prices, tmp_path / "out" / "chart.html")
    assert out.exists() and "plotly" in out.read_text()


# TC-PC-001
def test_tc_pc_001_structure(prices: pd.DataFrame) -> None:
    fig = build_chart().render(prices)
    assert [t.type for t in fig.data] == ["candlestick", "bar"]
    assert list(fig.data[0].x) == ["2026-08-27", "2026-08-28", "2026-08-31"]
    assert fig.layout.xaxis.type == "category"


# TC-PC-002
def test_tc_pc_002_adjustment(prices: pd.DataFrame) -> None:
    adjusted = build_chart(adjusted=True).build_figure(prices).data[0]
    raw = build_chart(adjusted=False).build_figure(prices).data[0]
    assert list(adjusted.close) == pytest.approx([21.0, 19.0, 20.0])
    assert list(raw.close) == pytest.approx([10.5, 9.5, 10.0])


# TC-PC-003
def test_tc_pc_003_errors(prices: pd.DataFrame) -> None:
    other = PriceChart(ChartTheme.from_mode(), "600000.SH", DateCodec())
    with pytest.raises(ValueError):
        other.build_figure(prices)
    with pytest.raises(SchemaError):
        build_chart().build_figure(prices.drop(columns="close_adj"))
