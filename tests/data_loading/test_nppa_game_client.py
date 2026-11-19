"""Contract tests for data_loading.NppaGameClient (plan 31 ph1)."""

from __future__ import annotations

import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.data_loading.nppa_game_client import BASE_URL, COLUMNS, NppaGameClient
from tests.data_loading.test_nbs_house_price_client import FakeTransport
from tests.support import FakeClock

DOMESTIC = BASE_URL + "gcwlyxspxx/"
IMPORTED = BASE_URL + "jkwlyxspxx/"
COLS = ["序号", "名称", "申报类别", "出版单位", "运营单位", "批复文号", "出版物号", "批准时间"]
HEAD = "".join(f"<td>{h}</td>" for h in COLS)
ROW = ("<tr><td>{i}</td><td>{name}</td><td></td><td><script>var _sblb = '{cat}';</script>"
       '" + _sblb + "</td><td>{pub}</td><td>{op}</td><td>国新出审\u30142026\u3015{no}号</td>'
       "<td>ISBN 978-7-498-{no}</td><td>2026年09月29日</td></tr>")  # fmt: skip


def build_list(*games: tuple[str, str, str], base: int = 2200) -> str:
    rows = "".join(ROW.format(i=i, name=n, cat=c, pub="某出版社", op=op, no=base + i)
                   for i, (n, c, op) in enumerate(games, start=1))  # fmt: skip
    return f"<table><tr>{HEAD}</tr>{rows}</table>"


def build_client(pages: dict[str, str]) -> NppaGameClient:
    return NppaGameClient(FakeClock(), FakeTransport(pages), min_interval_s=0, retries=0,
                          retry_sleep_s=0)  # fmt: skip


LISTS = {
    DOMESTIC: '<a href="./202609/t20260930_1.html">2026年9月份国产网络游戏审批信息</a>'
              '<a href="./202608/t20260831_2.html">2026年8月份国产网络游戏审批信息</a>',
    DOMESTIC + "202609/t20260930_1.html": build_list(("暗夜勇士", "移动", "杭州玛伊克"),
                                                     ("霸主征途", "移动、客户端", "鸿运互联")),
    DOMESTIC + "202608/t20260831_2.html": build_list(("旧游戏", "移动", "某公司"), base=2100),
    IMPORTED: '<a href="./202609/t20260925_3.html">2026年9月份进口网络游戏审批信息</a>',
    IMPORTED + "202609/t20260925_3.html": build_list(("海外大作", "客户端", "上海某公司"),
                                                     base=2300),
}  # fmt: skip


# TC-NGC-001
def test_tc_ngc_001_rows() -> None:
    out = build_client(LISTS).query("game_license", {"start_date": "20260901"}, [])
    assert list(out.columns) == COLUMNS
    assert sorted(out["name"]) == ["暗夜勇士", "海外大作", "霸主征途"]
    row = out[out["name"] == "霸主征途"].iloc[0]
    assert row["category"] == "移动、客户端" and row["operator"] == "鸿运互联"
    assert row["publisher"] == "某出版社" and row["approval_no"] == "国新出审\u30142026\u30152202号"
    assert row["approved_on"] == "20260929" and row["published"] == "20260930"
    assert row["origin"] == "domestic"
    assert out[out["name"] == "海外大作"].iloc[0]["origin"] == "imported"


# TC-NGC-002
def test_tc_ngc_002_filters_and_errors() -> None:
    client = build_client(LISTS)
    out = client.query("game_license", {"start_date": "20260901", "channels": "gcwlyxspxx"}, [])
    assert "旧游戏" not in set(out["name"]) and set(out["origin"]) == {"domestic"}
    with pytest.raises(DataSourceError, match="channels"):
        client.query("game_license", {"channels": "bogus"}, [])
    bad = {**LISTS, DOMESTIC + "202609/t20260930_1.html": "<table><tr><td>x</td></tr></table>"}
    with pytest.raises(DataSourceError, match="approval table"):
        build_client(bad).query("game_license", {"start_date": "20260901"}, [])
