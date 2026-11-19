"""Contract tests for portfolio.EtfStyleHeat (plan 15 ph7g)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.core.etf_proxy_settings import EtfProxySettings, EtfProxyStyle
from quant_cn.portfolio.etf_style_heat import EtfStyleHeat

BANK = EtfProxyStyle(key="bank", name="银行", benchmark="^中证银行指数", reference="A")
DAYS = [f"202601{d:02d}" for d in range(5, 13)]  # 8 sessions
SETTINGS = EtfProxySettings(styles=[BANK], style_window=2, style_z_days=4, style_hot_z=1.5)


def _build(shares_wan: list[float]) -> dict:
    px = pd.DataFrame({"ts_code": "A", "trade_date": DAYS, "close": 1.0, "pre_close": 1.0})
    sh = pd.DataFrame({"ts_code": "A", "trade_date": DAYS, "fd_share": shares_wan})
    members = pd.DataFrame({"ts_code": ["A"], "index": ["银行"], "is_core": [False]})
    return EtfStyleHeat(SETTINGS).build(px, sh, members)[0]


def test_tc_esh_001_members() -> None:
    """TC-ESH-001"""
    funds = pd.DataFrame(
        [
            ("512800.SH", "银行ETF", "中证银行指数\u00d7100%"),
            ("517900.SH", "银行AH ETF", "中证银行AH价格优选指数\u00d7100%"),
            ("510300.SH", "沪深300ETF", "沪深300指数\u00d7100%"),
        ],
        columns=["ts_code", "name", "benchmark"],
    )
    out = EtfStyleHeat(SETTINGS.model_copy(update={"core": ["512800.SH"]})).build_members(funds)
    assert out.to_dict("records") == [{"ts_code": "512800.SH", "index": "银行", "is_core": False}]


def test_tc_esh_002_flow_and_z() -> None:
    """TC-ESH-002"""
    shares = [100e4 + 1e4 * i for i in range(7)] + [111e4]  # +1 亿 a day, then +5 亿
    s = _build(shares)
    assert s["flow_1d"] == 5.0 and s["flow_window"] == 6.0 and s["aum"] == 111.0
    past = np.array([2 / 103, 2 / 104, 2 / 105, 2 / 106])  # today excluded
    z = (6 / 111 - past.mean()) / past.std(ddof=1)
    assert s["flow_pct"] == round(6 / 111, 4) and s["z"] == round(z, 2)
    assert s["metric"] == "bank_etf_z" and s["status"] == "hot" and s["hot_since"] == DAYS[-1]


def test_tc_esh_003_status() -> None:
    """TC-ESH-003"""
    heat = EtfStyleHeat(SETTINGS)
    z = pd.Series([0.2, 1.5, 0.8, 0.1], index=DAYS[:4])
    assert heat._compute_status(z) == ("hot", DAYS[1])  # stays hot above 0
    assert heat._compute_status(pd.Series([0.2, 1.49], index=DAYS[:2])) == ("normal", "")
    assert heat._compute_status(pd.concat([z, pd.Series([-0.1], index=[DAYS[4]])]))[0] == "cooled"
