"""App Store chart ranks per company and game (plan 19 ph2, plan 31)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pandas as pd

from quant_cn.core.app_publisher_settings import AppPublisherSettings
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS

VIEW = "curated.app_store_charts"
GROSSING = "grossing"
FREE = "free"
_SQL = f"""
    SELECT capture_date, country, chart, CAST(rank AS INTEGER) AS rank, app_id, name, artist_id,
        release_date
    FROM {VIEW} WHERE rank IS NOT NULL"""


class AppRankReader:
    """
    Purpose:
        Read the App Store game charts (curated.app_store_charts, plan 19) per company through
        the publisher map (AppPublisherSettings):
        - `read_rank_lines(names)`: each company's best rank on the home market's grossing
          chart (settings.app_country) per capture date, as LINE_COLUMNS (label = company
          name, period = capture_date, value = rank; lower is better);
        - `read_rankings(names)`: the leaderboard block of the latest capture: `apps`, one row
          per game of the companies in `names` and of every A-share company in the map (home
          grossing rank and the previous capture's, home free rank, best overseas grossing
          rank and its market, overseas markets in the grossing top 100), sorted by home
          grossing rank then best overseas rank; and `top`, the home grossing top `app_top`
          with each game's company (None when the account is not in the map) and previous
          rank; and `new`, the games released within settings.new_game_days of the latest
          capture that are on the home grossing or free top 100 or an overseas grossing top
          100, any publisher (plan 33, D-170), with release_date, sorted like `apps`.
        Companies are matched by ts_code (names: code -> name). No view gives empty results.

    Contract:
        Input:
            settings: SectorMonitorSettings (app_country, app_top, new_game_days); publishers:
            AppPublisherSettings; query: LakeQuery; codec: DateCodec
        Output:
            instance; read_rank_lines -> DataFrame (LINE_COLUMNS); read_rankings -> dict
            {"as_of", "prev", "country", "apps": [...], "top": [...], "new": [...]}
        Raises:
            LakeError  -- a lake query fails

    Used by:
        portfolio.SectorMonitorBuilder  -- the app_rank chart, table column and leaderboard
        cli.AppServiceBuilder  -- `build_sector_monitor`

    Test cases:
        TC-ARR-001  best home grossing rank per company and date; unmapped accounts and other
                    companies are left out; no view gives an empty frame
        TC-ARR-002  leaderboard: home grossing, previous, free and overseas best per game,
                    sorted; A-share companies of the map outside `names` included, HK ones not;
                    the top list carries company names, None for unmapped accounts
        TC-ARR-003  new games: released within new_game_days, on a qualifying chart, any
                    publisher; older releases and overseas free-only entries left out
    """

    def __init__(
        self,
        settings: SectorMonitorSettings,
        publishers: AppPublisherSettings,
        query: LakeQuery,
        codec: DateCodec,
    ) -> None:
        self._s = settings
        self._by_artist = publishers.get_by_artist()
        self._a_share = publishers.get_a_share()
        self._query = query
        self._codec = codec

    def read_rank_lines(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Best home grossing rank per company and capture date.

        Contract:
            Input:
                names: dict[str, str]  -- ts_code -> company name
            Output:
                DataFrame LINE_COLUMNS, sorted by label then period
            Raises:
                LakeError  -- the query fails
        """
        frame = self._read_frame()
        own = frame[(frame["country"] == self._s.app_country) & (frame["chart"] == GROSSING)
                    & frame["code"].isin(list(names))]  # fmt: skip
        if own.empty:
            return pd.DataFrame(columns=LINE_COLUMNS)
        best = own.groupby(["code", "capture_date"], as_index=False)["rank"].min()
        out = pd.DataFrame({"label": best["code"].map(names), "period": best["capture_date"],
                            "value": best["rank"].astype(float)})  # fmt: skip
        return out.sort_values(["label", "period"]).reset_index(drop=True)

    def read_rankings(self, names: dict[str, str]) -> dict[str, Any]:
        """
        Purpose:
            The leaderboard block of the latest capture.

        Contract:
            Input:
                names: dict[str, str]  -- ts_code -> company name
            Output:
                dict  -- {"as_of", "prev", "country", "apps", "top"}; apps cover `names` plus
                every A-share company of the map; as_of None and empty lists without chart data
            Raises:
                LakeError  -- the query fails
        """
        frame = self._read_frame()
        home = self._s.app_country
        if frame.empty:
            return {"as_of": None, "prev": None, "country": home, "apps": [], "top": [], "new": []}
        dates = sorted(frame["capture_date"].unique())
        as_of, prev = str(dates[-1]), (str(dates[-2]) if len(dates) > 1 else None)
        now = frame[frame["capture_date"] == as_of]
        before = frame[frame["capture_date"] == prev]
        prev_rank = self._get_ranks(before, home, GROSSING)
        own = now[now["code"].isin([*names, *self._a_share])]
        apps = [self._build_app(app_id, rows, prev_rank, home)
                for app_id, rows in own.groupby("app_id")]  # fmt: skip
        apps.sort(key=lambda a: (a["rank"] or 999, a["overseas_best"] or 999))
        top = now[(now["country"] == home) & (now["chart"] == GROSSING)
                  & (now["rank"] <= self._s.app_top)].sort_values("rank")  # fmt: skip
        top_rows = [{"rank": int(rank), "name": str(name), "company": self._get_text(company),
                     "code": self._get_text(code), "prev": prev_rank.get(str(app_id))}
                    for rank, name, company, code, app_id in zip(
                        top["rank"], top["name"], top["company"], top["code"], top["app_id"],
                        strict=True)]  # fmt: skip
        return {"as_of": as_of, "prev": prev, "country": home, "apps": apps, "top": top_rows,
                "new": self._build_new(now, prev_rank, home, as_of)}  # fmt: skip

    def _build_new(
        self, now: pd.DataFrame, prev_rank: dict[str, int], home: str, as_of: str
    ) -> list[dict[str, Any]]:
        since = self._codec.to_str(
            self._codec.to_date(as_of) - dt.timedelta(days=self._s.new_game_days)
        )
        fresh = now[now["release_date"].fillna("") >= since]
        listed = (fresh["country"] == home) | (fresh["chart"] == GROSSING)
        out = []
        for app_id, rows in fresh[listed].groupby("app_id"):
            row = self._build_app(app_id, rows, prev_rank, home)
            row["release_date"] = str(rows["release_date"].iloc[0])
            out.append(row)
        out.sort(key=lambda a: (a["rank"] or 999, a["free"] or 999, a["overseas_best"] or 999))
        return out

    def _read_frame(self) -> pd.DataFrame:
        cols = ["capture_date", "country", "chart", "rank", "app_id", "name", "code", "company",
                "release_date"]  # fmt: skip
        if not self._query.has_view(VIEW):
            return pd.DataFrame(columns=cols)
        frame = self._query.sql(_SQL)
        artists = frame["artist_id"].astype(str)
        frame["code"] = artists.map(lambda a: p.code if (p := self._by_artist.get(a)) else None)
        frame["company"] = artists.map(
            lambda a: p.company if (p := self._by_artist.get(a)) else None
        )
        return frame[cols]

    @staticmethod
    def _get_text(value: Any) -> str | None:
        return None if value is None or pd.isna(value) else str(value)

    @staticmethod
    def _get_ranks(rows: pd.DataFrame, country: str, chart: str) -> dict[str, int]:
        hit = rows[(rows["country"] == country) & (rows["chart"] == chart)]
        return {str(a): int(r) for a, r in zip(hit["app_id"], hit["rank"], strict=True)}

    def _build_app(
        self, app_id: Any, rows: pd.DataFrame, prev_rank: dict[str, int], home: str
    ) -> dict[str, Any]:
        key = str(app_id)
        rank = self._get_ranks(rows, home, GROSSING).get(key)
        free = self._get_ranks(rows, home, FREE).get(key)
        abroad = rows[(rows["country"] != home) & (rows["chart"] == GROSSING)].sort_values("rank")
        names = rows[rows["country"] == home]["name"]
        name = str(names.iloc[0]) if not names.empty else str(rows["name"].mode().iloc[0])
        return {
            "app_id": key, "name": name, "company": self._get_text(rows["company"].iloc[0]),
            "code": self._get_text(rows["code"].iloc[0]), "rank": rank,
            "prev": prev_rank.get(key), "free": free,
            "overseas_best": int(abroad["rank"].iloc[0]) if not abroad.empty else None,
            "overseas_market": str(abroad["country"].iloc[0]) if not abroad.empty else None,
            "overseas_markets": int(abroad["country"].nunique()),
        }  # fmt: skip
