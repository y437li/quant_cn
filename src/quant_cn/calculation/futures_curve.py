"""Futures term structure per material from daily contract quotes (plan 16 phase 2, D-121)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

# fut_daily ts_code suffix -> fut_basic exchange
SUFFIX_EXCHANGE = {
    "SHF": "SHFE",
    "DCE": "DCE",
    "ZCE": "CZCE",
    "INE": "INE",
    "GFE": "GFEX",
    "CFX": "CFFEX",
}
CONTRACT_COLUMNS = ("ts_code", "fut_code", "exchange", "d_month")
QUOTE_COLUMNS = ("ts_code", "trade_date", "settle", "close", "oi", "vol")
TENOR_TOLERANCE = 1  # months: a 6m / 12m price needs a contract within one month of the tenor
FLAT_BAND = 0.01  # |slope| below 1% is a flat curve


@dataclass(frozen=True)
class CurveSummary:
    """
    Purpose:
        The shape of one contract family's curve on one date: front, most-held, 6- and 12-month and
        last prices, and the slope from the most-held month to 12 months after it (or to the last
        later month when the curve is shorter).

    Contract:
        Input:
            family: str; trade_date: str; n_contracts: int >= 0; front_month, dominant_month,
            last_month: str | None (YYYYMM); front_price, dominant_price, price_6m, price_12m,
            last_price: float | None; slope_12m: float | None; shape: str -- contango |
            backwardation | flat | none
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        calculation.FuturesCurve  -- returned by compute_summary

    Test cases:
        TC-FCV-002  (via FuturesCurve) fields of a backwardated curve
    """

    family: str
    trade_date: str
    n_contracts: int
    front_month: str | None = None
    front_price: float | None = None
    dominant_month: str | None = None
    dominant_price: float | None = None
    price_6m: float | None = None
    price_12m: float | None = None
    last_month: str | None = None
    last_price: float | None = None
    slope_12m: float | None = None
    shape: str = "none"


class FuturesCurve:
    """
    Purpose:
        Back-month futures curve per contract family (e.g. "AL.SHF") and per material node
        (config/material_prices.yaml maps MAT_* ids to families), for the commodity price the
        market implies against the curve (plan 16 phase 2). A curve on a date is every listed
        month of the family that has a quote that day and has not expired (delivery month >= the
        trade month), priced at settle (close when settle is missing), with months ahead counted
        from the trade month. PIT: only quotes of that trade date are used.

    Contract:
        Input:
            contracts: DataFrame  -- curated reference fut_basic: ts_code, fut_code, exchange,
                                     d_month (YYYYMM)
            materials: Mapping[str, Sequence[str]]  -- material id -> families
        Output:
            instance; `list_families`, `build_curve`, `compute_summary`,
            `list_material_summaries`, `build_dominant_series`
        Raises:
            ValueError  -- contracts frame missing CONTRACT_COLUMNS

    Used by:
        plan 16 phase 2 ImpliedExpectations (to come); research checks

    Test cases:
        TC-FCV-001  curve rows: listed months only, expired dropped, settle else close, months
                    ahead from the trade month; unknown family -> empty frame; contracts without
                    a YYYYMM delivery month (continuous, index) ignored
        TC-FCV-002  summary of a backwardated curve: front, dominant (max oi), 6m, 12m, last,
                    slope and shape
        TC-FCV-003  short curve: 12m None, slope to the last month, flat inside 1%; empty curve
                    -> n_contracts 0, shape none
        TC-FCV-004  list_families per material, [] for unknown; list_material_summaries
        TC-FCV-005  ValueError: contracts without d_month, family without suffix, quotes
                    without a required column
        TC-FCV-006  build_dominant_series: one row per date, the max-oi unexpired month
    """

    def __init__(self, contracts: pd.DataFrame, materials: Mapping[str, Sequence[str]]) -> None:
        missing = [c for c in CONTRACT_COLUMNS if c not in contracts.columns]
        if missing:
            raise ValueError(f"contracts frame missing columns {missing}")
        frame = contracts[list(CONTRACT_COLUMNS)].dropna().astype(str)
        # continuous / index contracts carry no delivery month: they are not points on a curve
        self._contracts = frame[frame["d_month"].str.fullmatch(r"\d{6}")]
        self._materials = {k: list(v) for k, v in materials.items()}

    def list_families(self, material: str) -> list[str]:
        """
        Purpose:
            Contract families mapped to a material node.

        Contract:
            Input:
                material: str  -- MAT_* id
            Output:
                list[str]  -- [] for an unmapped material
            Raises:
                (none)
        """
        return list(self._materials.get(material, []))

    def build_curve(self, quotes: pd.DataFrame, family: str, trade_date: str) -> pd.DataFrame:
        """
        Purpose:
            The family's curve on one date.

        Contract:
            Input:
                quotes: DataFrame  -- fut_daily rows (QUOTE_COLUMNS), any families and dates
                family: str  -- "<fut_code>.<suffix>", e.g. "AL.SHF"
                trade_date: str  -- YYYYMMDD
            Output:
                DataFrame  -- ts_code, d_month, months_ahead, price, oi, vol; sorted by d_month;
                              empty when nothing is quoted
            Raises:
                ValueError  -- family without a known suffix, quotes missing a column
        """
        code, _, suffix = family.partition(".")
        if suffix not in SUFFIX_EXCHANGE:
            raise ValueError(f"family {family!r} must look like <fut_code>.<suffix>")
        missing = [c for c in QUOTE_COLUMNS if c not in quotes.columns]
        if missing:
            raise ValueError(f"quotes frame missing columns {missing}")
        listed = self._contracts[
            (self._contracts["fut_code"] == code)
            & (self._contracts["exchange"] == SUFFIX_EXCHANGE[suffix])
        ]
        day = quotes[quotes["trade_date"].astype(str) == trade_date]
        curve = day.merge(listed[["ts_code", "d_month"]], on="ts_code")
        curve = curve.assign(price=curve["settle"].fillna(curve["close"]))
        trade_month = int(trade_date[:4]) * 12 + int(trade_date[4:6])
        ahead = [int(m[:4]) * 12 + int(m[4:6]) - trade_month for m in curve["d_month"]]
        curve = curve.assign(months_ahead=pd.Series(ahead, index=curve.index, dtype="int64"))
        curve = curve[(curve["months_ahead"] >= 0) & curve["price"].notna()]
        columns = ["ts_code", "d_month", "months_ahead", "price", "oi", "vol"]
        return curve.sort_values("d_month")[columns].reset_index(drop=True)

    def compute_summary(self, curve: pd.DataFrame, family: str, trade_date: str) -> CurveSummary:
        """
        Purpose:
            Front, dominant, 6m, 12m and last prices and the curve shape.

        Contract:
            Input:
                curve: DataFrame  -- from build_curve; family, trade_date: str
            Output:
                CurveSummary  -- slope = price ~12 months after the most-held month (else the
                                 last later month) / most-held price - 1; shape contango above
                                 FLAT_BAND, backwardation below -FLAT_BAND, else flat; none
                                 when empty
            Raises:
                (none)
        """
        if curve.empty:
            return CurveSummary(family, trade_date, 0)
        front, last = curve.iloc[0], curve.iloc[-1]
        dominant = curve.iloc[int(curve["oi"].to_numpy().argmax())]
        p6, p12 = self._find_tenor(curve, 6), self._find_tenor(curve, 12)
        # base = the most-held month: the front month is often in delivery, thin and mispriced
        later = curve[curve["months_ahead"] > int(dominant["months_ahead"])]
        target = int(dominant["months_ahead"]) + 12
        if later.empty:
            slope = None
        else:
            gap = (later["months_ahead"] - target).abs().to_numpy()
            pick = later.iloc[int(gap.argmin())] if gap.min() <= TENOR_TOLERANCE else later.iloc[-1]
            slope = float(pick["price"]) / float(dominant["price"]) - 1
        shape = (
            "flat"
            if slope is None or abs(slope) < FLAT_BAND
            else "contango"
            if slope > 0
            else "backwardation"
        )
        return CurveSummary(
            family, trade_date, len(curve), str(front["d_month"]), float(front["price"]),
            str(dominant["d_month"]), float(dominant["price"]), p6, p12,
            str(last["d_month"]), float(last["price"]), slope, shape,
        )  # fmt: skip

    def list_material_summaries(
        self, quotes: pd.DataFrame, material: str, trade_date: str
    ) -> list[CurveSummary]:
        """
        Purpose:
            One summary per family of a material.

        Contract:
            Input:
                quotes: DataFrame; material: str; trade_date: str
            Output:
                list[CurveSummary]  -- in the order of the material map; [] when unmapped
            Raises:
                ValueError  -- as build_curve
        """
        return [
            self.compute_summary(self.build_curve(quotes, f, trade_date), f, trade_date)
            for f in self.list_families(material)
        ]

    def build_dominant_series(self, quotes: pd.DataFrame, family: str) -> pd.DataFrame:
        """
        Purpose:
            Daily price of the most-held unexpired month: the continuous price a material's
            profit sensitivity is regressed on (plan 16 phase 2).

        Contract:
            Input:
                quotes: DataFrame  -- fut_daily rows (QUOTE_COLUMNS), many dates
                family: str  -- "<fut_code>.<suffix>"
            Output:
                DataFrame  -- trade_date, ts_code, price; one row per date with a quote, sorted
            Raises:
                ValueError  -- as build_curve
        """
        code, _, suffix = family.partition(".")
        own = self._contracts[
            (self._contracts["fut_code"] == code)
            & (self._contracts["exchange"] == SUFFIX_EXCHANGE.get(suffix, ""))
        ]["ts_code"]
        mine = quotes[quotes["ts_code"].isin(set(own))]  # one filter instead of one per day
        rows = []
        for day in sorted(mine["trade_date"].astype(str).unique()):
            curve = self.build_curve(mine, family, day)
            if not curve.empty:
                top = curve.iloc[int(curve["oi"].to_numpy().argmax())]
                rows.append(
                    {"trade_date": day, "ts_code": top["ts_code"], "price": float(top["price"])}
                )
        return pd.DataFrame(rows, columns=["trade_date", "ts_code", "price"])

    @staticmethod
    def _find_tenor(curve: pd.DataFrame, months: int) -> float | None:
        gap = (curve["months_ahead"] - months).abs().to_numpy()
        if gap.min() > TENOR_TOLERANCE:
            return None
        return float(curve["price"].iloc[int(gap.argmin())])
