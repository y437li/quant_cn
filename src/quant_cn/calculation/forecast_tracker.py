"""Earnings previews (业绩预告) scored against the first reported actual (plan 18 ph1, D-124)."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.guidance_settings import GuidanceSettings

logger = logging.getLogger(__name__)

PROFIT_FIELD = "n_income_attr_p"
WAN = 1e4  # forecast_vip amounts are in 万元; statements and express_vip in CNY
FORECAST_COLUMNS = [
    "ts_code", "ann_date", "end_date", "type", "p_change_min", "p_change_max",
    "net_profit_min", "net_profit_max", "last_parent_net", "update_flag",
]  # fmt: skip
ACTUAL_COLUMNS = ["ts_code", "end_date", "field", "value", "known_on"]
EXPRESS_COLUMNS = ["ts_code", "ann_date", "end_date", "n_income", "update_flag"]
OUTCOME_COLUMNS = [
    "ts_code", "end_date", "ann_date", "version", "n_versions", "is_last", "days_after_end",
    "ex_ante", "type", "low", "high", "mid", "revision", "actual", "actual_known_on", "outcome",
    "position", "surprise", "express_profit", "express_known_on",
]  # fmt: skip
TRACK_COLUMNS = [
    "ts_code", "n", "hit_rate", "above_rate", "below_rate", "mean_surprise",
    "median_abs_surprise", "first_hit_rate", "last_period", "sufficient", "n_ex_ante",
    "ex_ante_hit_rate", "ex_ante_mean_surprise", "ex_ante_sufficient",
]  # fmt: skip
SCORED = ("in", "above", "below")


class ForecastTracker:
    """
    Purpose:
        Score every earnings preview (业绩预告, all revisions) against the first reported net
        profit attributable to the parent, and summarise each company's record as hit rate and
        bias (plan 18 ph1, D-124). Pure: the inputs come in as frames read by the lake
        (LakeReader.read_panel for forecast_vip / express_vip, StatementVersionReader.
        read_first_versions for the actual), so the tracker never sees a restated actual.

    Contract:
        Input:
            codec:    DateCodec
            settings: GuidanceSettings  -- history_start, window_years, min_outcomes
        Output:
            instance; `build(forecasts, actuals, express, as_of) -> DataFrame[OUTCOME_COLUMNS]`
            and `build_track_record(outcomes, as_of) -> DataFrame[TRACK_COLUMNS]`
        Raises:
            ValueError  -- malformed as_of or inputs without their columns

    Used by:
        (none yet)  -- pipeline.GuidanceStep (plan 18 ph6)

    Test cases:
        TC-FT-001  range from net_profit_min/max (万元 -> CNY, ordered low <= high); in / above /
                   below against the actual; position and surprise
        TC-FT-002  range filled from p_change and a positive last_parent_net when net_profit is
                   missing; no bound at all -> outcome no_range
        TC-FT-003  one-sided range: only a floor -> in or below; only a ceiling -> in or above;
                   position and surprise NaN
        TC-FT-004  revisions: versions numbered by ann_date, same-day duplicates keep the highest
                   update_flag, is_last, revision up / down / none vs the previous mid
        TC-FT-005  PIT: on an as_of before the actual's known_on the outcome is pending; previews
                   announced after as_of are not seen; a preview announced after the actual is
                   after_actual
        TC-FT-006  express: the first flash report known on as_of fills express_profit and
                   express_known_on; periods before history_start are dropped
        TC-FT-007  track record: last versions of scored periods within window_years of as_of;
                   rates, mean and median abs surprise, first_hit_rate from version 1,
                   sufficient iff n >= min_outcomes
        TC-FT-008  no previews -> empty frames with the columns; malformed as_of or missing
                   columns raise ValueError
        TC-FT-009  days_after_end = ann_date - end_date in days; ex_ante iff published on or
                   before the period end
        TC-FT-010  ex-ante record: per period the last version published on or before the period
                   end; n_ex_ante, hit rate, mean surprise, ex_ante_sufficient; n_ex_ante 0 and
                   NaN rates when no version came before the period end
    """

    def __init__(self, codec: DateCodec, settings: GuidanceSettings) -> None:
        self._codec = codec
        self._settings = settings

    @staticmethod
    def list_fields() -> list[str]:
        """
        Purpose:
            The fundamentals_long field the actual comes from.

        Contract:
            Input:
                (none)
            Output:
                list[str]  -- [PROFIT_FIELD]
            Raises:
                (none)
        """
        return [PROFIT_FIELD]

    def build(
        self, forecasts: pd.DataFrame, actuals: pd.DataFrame, express: pd.DataFrame, as_of: str
    ) -> pd.DataFrame:
        """
        Purpose:
            One row per preview version known on as_of, with its range and outcome.

        Contract:
            Input:
                forecasts: DataFrame  -- FORECAST_COLUMNS (forecast_vip, amounts in 万元)
                actuals:   DataFrame  -- ACTUAL_COLUMNS (first versions; field PROFIT_FIELD, CNY)
                express:   DataFrame  -- EXPRESS_COLUMNS (express_vip, CNY)
                as_of:     str        -- YYYYMMDD; rows announced after it are not used
            Output:
                DataFrame  -- OUTCOME_COLUMNS, key (ts_code, end_date, ann_date) unique, sorted:
                    low, high, mid  CNY; low <= high when both; mid only when both
                    revision        up / down / none vs the previous version's mid; NA for v1
                    days_after_end  calendar days from end_date to ann_date (<= 0 = before)
                    ex_ante         published on or before the period end (forward guidance)
                    outcome         in | above | below | pending (actual not known on as_of) |
                                    no_range | after_actual (preview announced after the actual)
                    position        (actual - low) / (high - low), two-sided ranges only
                    surprise        (actual - mid) / |mid|, two-sided ranges with mid != 0
                Visible from actual_known_on; factor use goes through PitAligner (next session).
            Raises:
                ValueError  -- malformed as_of or missing columns
        """
        self._codec.validate(as_of)
        self._check(forecasts, FORECAST_COLUMNS, "forecasts")
        self._check(actuals, ACTUAL_COLUMNS, "actuals")
        self._check(express, EXPRESS_COLUMNS, "express")
        versions = self._list_versions(forecasts, as_of)
        if versions.empty:
            return pd.DataFrame(columns=OUTCOME_COLUMNS)
        out = versions.merge(
            self._build_first_actuals(actuals, as_of), on=["ts_code", "end_date"], how="left"
        )
        out = out.merge(
            self._build_first_express(express, as_of), on=["ts_code", "end_date"], how="left"
        )
        out["outcome"] = self._compute_outcomes(out)
        two_sided = out["low"].notna() & out["high"].notna()
        width = (out["high"] - out["low"]).where(two_sided & (out["high"] > out["low"]))
        out["position"] = (out["actual"] - out["low"]) / width
        scored = out["outcome"].isin(SCORED)
        mid = out["mid"].where(scored & (out["mid"] != 0))
        out["surprise"] = (out["actual"] - mid) / mid.abs()
        out["position"] = out["position"].where(scored)
        logger.info("forecast outcomes %s: %d versions", as_of, len(out))
        return self._to_strings(out[OUTCOME_COLUMNS]).reset_index(drop=True)

    def build_track_record(self, outcomes: pd.DataFrame, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            Per company: how often the last preview of a period held, and the average miss.

        Contract:
            Input:
                outcomes: DataFrame  -- OUTCOME_COLUMNS from build(..., as_of)
                as_of:    str        -- YYYYMMDD; window = period ends after as_of minus
                                        window_years
            Output:
                DataFrame  -- TRACK_COLUMNS, one row per company with >= 1 scored period:
                    n                    scored periods (last version outcome in / above / below)
                    hit_rate, above_rate, below_rate  shares of n
                    mean_surprise        mean surprise (bias; > 0 = guides low), NaN if none
                    median_abs_surprise  median |surprise|
                    first_hit_rate       in-range share of version 1 of the same periods
                    last_period          latest scored end_date
                    sufficient           n >= min_outcomes
                    n_ex_ante            scored periods with a version published on or before
                                         the period end (the last such version is scored)
                    ex_ante_hit_rate, ex_ante_mean_surprise  of those; NaN when n_ex_ante = 0
                    ex_ante_sufficient   n_ex_ante >= min_outcomes
            Raises:
                ValueError  -- malformed as_of or missing columns
        """
        self._check(outcomes, OUTCOME_COLUMNS, "outcomes")
        start = self._get_window_start(as_of)
        last = outcomes[outcomes["is_last"].astype(bool) & outcomes["outcome"].isin(SCORED)]
        last = last[last["end_date"] > start]
        if last.empty:
            return pd.DataFrame(columns=TRACK_COLUMNS)
        out = self._compute_rates(outcomes, last)
        out["sufficient"] = out["n"] >= self._settings.min_outcomes
        out = out.join(self._compute_ex_ante(outcomes, start))
        out["n_ex_ante"] = out["n_ex_ante"].fillna(0).astype(int)
        out["ex_ante_sufficient"] = out["n_ex_ante"] >= self._settings.min_outcomes
        out = out.reset_index().rename(columns={"index": "ts_code"})
        out["ts_code"] = out["ts_code"].astype("string")
        out["last_period"] = out["last_period"].astype("string")
        return out[TRACK_COLUMNS].sort_values("ts_code").reset_index(drop=True)

    @staticmethod
    def _compute_rates(outcomes: pd.DataFrame, last: pd.DataFrame) -> pd.DataFrame:
        """Per company over the scored last versions: rates, bias, first-version hit rate."""
        first = outcomes[outcomes["version"] == 1].merge(
            last[["ts_code", "end_date"]], on=["ts_code", "end_date"]
        )
        grouped = last.groupby("ts_code")
        return pd.DataFrame(
            {
                "n": grouped.size(),
                "hit_rate": grouped["outcome"].apply(lambda s: (s == "in").mean()),
                "above_rate": grouped["outcome"].apply(lambda s: (s == "above").mean()),
                "below_rate": grouped["outcome"].apply(lambda s: (s == "below").mean()),
                "mean_surprise": grouped["surprise"].mean(),
                "median_abs_surprise": grouped["surprise"].apply(lambda s: s.abs().median()),
                "first_hit_rate": (first["outcome"] == "in").groupby(first["ts_code"]).mean(),
                "last_period": grouped["end_date"].max(),
            }
        )

    @staticmethod
    def _compute_ex_ante(outcomes: pd.DataFrame, start: str) -> pd.DataFrame:
        """Per company: the last pre-period-end version of each scored period, summarised."""
        pre = outcomes[outcomes["ex_ante"].astype(bool) & outcomes["outcome"].isin(SCORED)]
        pre = pre[pre["end_date"] > start].sort_values("version")
        pre = pre.drop_duplicates(["ts_code", "end_date"], keep="last")
        grouped = pre.groupby("ts_code")
        return pd.DataFrame(
            {
                "n_ex_ante": grouped.size(),
                "ex_ante_hit_rate": grouped["outcome"].apply(lambda s: (s == "in").mean()),
                "ex_ante_mean_surprise": grouped["surprise"].mean(),
            },
            index=pd.Index(sorted(pre["ts_code"].unique())),
        )

    @staticmethod
    def _check(frame: pd.DataFrame, columns: list[str], name: str) -> None:
        missing = sorted(set(columns) - set(frame.columns))
        if missing:
            raise ValueError(f"{name} missing columns: {missing}")

    def _list_versions(self, forecasts: pd.DataFrame, as_of: str) -> pd.DataFrame:
        f = forecasts[(forecasts["ann_date"] <= as_of)]
        f = f[f["end_date"] >= self._settings.history_start]
        f = f.sort_values(
            ["ts_code", "end_date", "ann_date", "update_flag"], ascending=[True, True, True, False]
        )
        f = f.drop_duplicates(["ts_code", "end_date", "ann_date"], keep="first").copy()
        if f.empty:
            return f
        f["days_after_end"] = [
            (self._codec.to_date(a) - self._codec.to_date(e)).days
            for a, e in zip(f["ann_date"], f["end_date"], strict=True)
        ]
        f["ex_ante"] = f["days_after_end"] <= 0
        low, high = self._get_bounds(f)
        both = low.notna() & high.notna()  # losses can come with the bounds swapped
        f["low"] = low.where(~both, np.fmin(low, high))
        f["high"] = high.where(~both, np.fmax(low, high))
        f["mid"] = (f["low"] + f["high"]) / 2
        keys = f.groupby(["ts_code", "end_date"], sort=False)
        f["version"] = keys.cumcount() + 1
        f["n_versions"] = keys["ann_date"].transform("size")
        f["is_last"] = f["version"] == f["n_versions"]
        prev = keys["mid"].shift()
        f["revision"] = np.select(
            [f["mid"] > prev, f["mid"] < prev, f["mid"] == prev], ["up", "down", "none"], default=""
        )
        f["revision"] = f["revision"].replace("", pd.NA)
        return f

    @staticmethod
    def _get_bounds(f: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        base = f["last_parent_net"].where(f["last_parent_net"] > 0)
        low = f["net_profit_min"].fillna(base * (1 + f["p_change_min"] / 100))
        high = f["net_profit_max"].fillna(base * (1 + f["p_change_max"] / 100))
        return low.astype(float) * WAN, high.astype(float) * WAN

    @staticmethod
    def _build_first_actuals(actuals: pd.DataFrame, as_of: str) -> pd.DataFrame:
        a = actuals[(actuals["field"] == PROFIT_FIELD) & (actuals["known_on"] <= as_of)]
        a = a.sort_values(["ts_code", "end_date", "known_on"]).drop_duplicates(
            ["ts_code", "end_date"]
        )
        return a.rename(columns={"value": "actual", "known_on": "actual_known_on"})[
            ["ts_code", "end_date", "actual", "actual_known_on"]
        ]

    @staticmethod
    def _build_first_express(express: pd.DataFrame, as_of: str) -> pd.DataFrame:
        e = express[express["ann_date"] <= as_of]
        e = e.sort_values(
            ["ts_code", "end_date", "ann_date", "update_flag"], ascending=[True, True, True, False]
        )
        e = e.drop_duplicates(["ts_code", "end_date"])
        return e.rename(columns={"n_income": "express_profit", "ann_date": "express_known_on"})[
            ["ts_code", "end_date", "express_profit", "express_known_on"]
        ]

    @staticmethod
    def _compute_outcomes(out: pd.DataFrame) -> np.ndarray:
        act, low, high = out["actual"], out["low"], out["high"]
        known = out["actual_known_on"].notna()
        conditions = [
            ~known,
            out["ann_date"] > out["actual_known_on"],
            low.isna() & high.isna(),
            low.notna() & (act < low),
            high.notna() & (act > high),
        ]
        choices = ["pending", "after_actual", "no_range", "below", "above"]
        # string-dtype comparisons give <NA>, not False, where a side is missing
        masks = [pd.Series(c).fillna(False).to_numpy(dtype=bool) for c in conditions]
        return np.select(masks, choices, default="in")

    @staticmethod
    def _to_strings(out: pd.DataFrame) -> pd.DataFrame:
        out = out.copy()
        text = ["ts_code", "end_date", "ann_date", "type", "revision", "actual_known_on", "outcome",
                "express_known_on"]  # fmt: skip
        for col in text:
            out[col] = out[col].astype("string")
        return out

    def _get_window_start(self, as_of: str) -> str:
        day = self._codec.to_date(as_of)
        years = self._settings.window_years
        try:
            start = day.replace(year=day.year - years)
        except ValueError:  # 29 February
            start = day.replace(year=day.year - years, day=28)
        return self._codec.to_str(start)
