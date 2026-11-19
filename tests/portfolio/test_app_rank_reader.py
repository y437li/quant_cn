"""Contract tests for portfolio.AppRankReader (plan 19 ph2, plan 31)."""

from __future__ import annotations

from pathlib import Path

from quant_cn.core.app_publisher_settings import AppPublisher, AppPublisherSettings
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.portfolio.app_rank_reader import AppRankReader
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS
from tests.support import MiniLake, SampleFactorLake

REPO = Path(__file__).resolve().parents[2]
NAMES = {"002558.SZ": "巨人网络", "002602.SZ": "世纪华通"}
PUBLISHERS = AppPublisherSettings(publishers=[
    AppPublisher(artist_id="10", artist="巨人", company="巨人网络", code="002558.SZ"),
    AppPublisher(artist_id="20", artist="Century", company="世纪华通", code="002602.SZ"),
    AppPublisher(artist_id="30", artist="Tencent", company="腾讯", code="00700.HK"),
    AppPublisher(artist_id="40", artist="9z", company="冰川网络", code="300533.SZ"),
])  # fmt: skip
ROWS = [  # (date, country, chart, rank, app_id, name, artist_id)
    ("20261116", "cn", "grossing", 1, "a", "王者荣耀", "30"),
    ("20261116", "cn", "grossing", 40, "g1", "超自然行动组", "10"),
    ("20261117", "cn", "grossing", 1, "a", "王者荣耀", "30"),
    ("20261117", "cn", "grossing", 2, "x", "无主游戏", "99"),
    ("20261117", "cn", "grossing", 33, "g1", "超自然行动组", "10"),
    ("20261117", "cn", "grossing", 60, "g2", "原始征途", "10"),
    ("20261117", "cn", "free", 5, "g1", "超自然行动组", "10"),
    ("20261117", "cn", "grossing", 6, "w1", "无尽冬日", "20"),
    ("20261117", "us", "grossing", 3, "w2", "Whiteout Survival", "20"),
    ("20261117", "jp", "grossing", 9, "w2", "ホワイトアウト", "20"),
    ("20261117", "br", "grossing", 50, "x1", "X-Clash", "40"),  # A share outside NAMES
    ("20261117", "us", "free", 4, "f1", "Free Only", "99"),
]
RELEASED = {"x": "20261001", "w2": "20260901", "f1": "20261101"}  # others 20200101


def build_reader(lake: MiniLake, config: Config) -> AppRankReader:
    rows = [{"capture_date": d, "country": c, "chart": ch, "rank": float(r), "app_id": a, "name": n,
             "artist_id": art, "release_date": RELEASED.get(a, "20200101")}
            for d, c, ch, r, a, n, art in ROWS]  # fmt: skip
    SampleFactorLake.write(lake, config, "app_store_charts", rows)
    settings = SectorMonitorSettings.load(REPO).model_copy(update={"app_top": 2})
    return AppRankReader(settings, PUBLISHERS, lake.query, DateCodec())


# TC-ARR-001
def test_tc_arr_001_rank_lines(lake: MiniLake, config: Config) -> None:
    settings = SectorMonitorSettings.load(REPO)
    assert AppRankReader(settings, PUBLISHERS, lake.query, DateCodec()).read_rank_lines(NAMES).empty
    out = build_reader(lake, config).read_rank_lines(NAMES)
    assert list(out.columns) == LINE_COLUMNS
    assert out.values.tolist() == [
        ["世纪华通", "20261117", 6.0],
        ["巨人网络", "20261116", 40.0],
        ["巨人网络", "20261117", 33.0],  # best of 33 and 60; overseas and free left out
    ]


# TC-ARR-002
def test_tc_arr_002_rankings(lake: MiniLake, config: Config) -> None:
    doc = build_reader(lake, config).read_rankings(NAMES)
    assert (doc["as_of"], doc["prev"], doc["country"]) == ("20261117", "20261116", "cn")
    assert [a["name"] for a in doc["apps"]] == [
        "无尽冬日",
        "超自然行动组",
        "原始征途",
        "Whiteout Survival",
        "X-Clash",  # A share outside NAMES; 王者荣耀 (HK) is not listed
    ]
    ghost = doc["apps"][1]
    assert (ghost["rank"], ghost["prev"], ghost["free"], ghost["company"]) == (
        33,
        40,
        5,
        "巨人网络",
    )
    whiteout = doc["apps"][3]
    assert whiteout["rank"] is None and whiteout["overseas_best"] == 3
    assert (whiteout["overseas_market"], whiteout["overseas_markets"]) == ("us", 2)
    assert [(t["rank"], t["company"], t["prev"]) for t in doc["top"]] == [
        (1, "腾讯", 1),
        (2, None, None),
    ]


# TC-ARR-003
def test_tc_arr_003_new_games(lake: MiniLake, config: Config) -> None:
    new = build_reader(lake, config).read_rankings(NAMES)["new"]
    # 无主游戏 (cn grossing #2, unmapped) and Whiteout Survival (overseas grossing); the us
    # free-only game and every pre-window release are left out
    assert [(g["name"], g["company"], g["release_date"]) for g in new] == [
        ("无主游戏", None, "20261001"),
        ("Whiteout Survival", "世纪华通", "20260901"),
    ]
