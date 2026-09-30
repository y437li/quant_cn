"""The factor extension point (SRC_DESIGN §2.5): one value per stock and session, PIT-safe."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ClassVar, Literal

import pandas as pd

from quant_cn.core.frames import FACTOR_PANEL

Input = Literal["prices", "fundamentals", "daily_basic"]


@dataclass(frozen=True)
class FactorInputs:
    """
    Purpose:
        The panels a factor may read, loaded once by FactorFactory for all factors of a run.
        Everything is already point in time: fundamentals come only as FUNDAMENTALS_PIT
        (effective the session after announcement, TTM from PIT-visible versions, D-092), prices
        and daily_basic are dated by their session (known at its close).

    Contract:
        Input:
            prices:       DataFrame  -- PRICE_PANEL, dense (every session inside each stock's span)
            fundamentals: DataFrame  -- FUNDAMENTALS_PIT (possibly empty)
            daily_basic:  DataFrame  -- curated daily_basic columns (possibly empty)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        factor.BaseFactor                   -- compute input
        factor.FactorFactory                -- build_inputs output
        factor.library.EarningsYieldFactor  -- injected type or call
        factor.library.MomentumFactor       -- injected type or call
        factor.library.ProfitGrowthFactor   -- injected type or call
        factor.library.ReversalFactor       -- injected type or call
        factor.library.RoeFactor            -- injected type or call
        factor.library.TurnoverFactor       -- injected type or call

    Test cases:
        TC-FIN-001  compute_field pivots one fundamentals field onto (trade_date, ts_code)
    """

    prices: pd.DataFrame
    fundamentals: pd.DataFrame = field(default_factory=pd.DataFrame)
    daily_basic: pd.DataFrame = field(default_factory=pd.DataFrame)

    def compute_field(self, name: str) -> pd.DataFrame:
        """
        Purpose:
            One fundamentals field as (trade_date, ts_code, <name>).

        Contract:
            Input:
                name: str  -- FUNDAMENTALS_PIT field
            Output:
                DataFrame  -- columns trade_date, ts_code, name; rows where the field is visible
            Raises:
                (none)
        """
        if self.fundamentals.empty:
            return pd.DataFrame(columns=["trade_date", "ts_code", name])
        rows = self.fundamentals[self.fundamentals["field"] == name]
        return rows[["trade_date", "ts_code", "value"]].rename(columns={"value": name})


class BaseFactor(ABC):
    """
    Purpose:
        Abstract factor: declares which inputs, fundamentals fields and daily_basic columns it
        needs and how many sessions of price history before the first output date; `compute`
        turns FactorInputs into FACTOR_PANEL rows for [start, end]. Contract (FACTOR_TESTING_DESIGN
        §11): the value at t uses only data known by the close of t; fundamentals only through
        FUNDAMENTALS_PIT. Subclasses register themselves by class name for FactorFactory.

    Contract:
        Input:
            name: str  -- FACTOR_PANEL.factor for this instance (from config/factors.yaml)
        Output:
            instance; `compute`; class attributes `inputs`, `fields`, `basic_columns`, `lookback`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        factor.FactorFactory                -- builds registered subclasses
        factor.library.*                    -- subclasses
        factor.library.EarningsYieldFactor  -- subclass
        factor.library.MomentumFactor       -- subclass
        factor.library.ProfitGrowthFactor   -- subclass
        factor.library.ReversalFactor       -- subclass
        factor.library.RoeFactor            -- subclass
        factor.library.TurnoverFactor       -- subclass

    Test cases:
        TC-BFA-001  compute keeps [start, end], sets value = value_raw and the factor name,
                   drops NaN values and validates FACTOR_PANEL
        TC-BFA-002  subclasses are registered by class name; the base cannot be instantiated
    """

    registry: ClassVar[dict[str, type[BaseFactor]]] = {}
    inputs: ClassVar[tuple[Input, ...]] = ()
    fields: ClassVar[tuple[str, ...]] = ()
    basic_columns: ClassVar[tuple[str, ...]] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        BaseFactor.registry[cls.__name__] = cls

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def lookback(self) -> int:
        """
        Purpose:
            Sessions of history needed before the first output date (0 = none).

        Contract:
            Input:
                (none)
            Output:
                int
            Raises:
                (none)
        """
        return 0

    def compute(self, inputs: FactorInputs, start: str, end: str) -> pd.DataFrame:
        """
        Purpose:
            FACTOR_PANEL rows of this factor for [start, end].

        Contract:
            Input:
                inputs: FactorInputs; start, end: str  -- YYYYMMDD, inclusive
            Output:
                DataFrame  -- FACTOR_PANEL (factor = self.name, value = value_raw; preprocessing
                              fills value later), NaN values dropped, sorted by key
            Raises:
                SchemaError  -- the subclass returned an invalid frame
        """
        raw = self.compute_raw(inputs)
        raw = raw[(raw["trade_date"] >= start) & (raw["trade_date"] <= end)]
        raw = raw.dropna(subset=["value_raw"])
        out = raw.assign(factor=self.name, value=raw["value_raw"])
        out = (
            out[FACTOR_PANEL.columns].sort_values(["trade_date", "ts_code"]).reset_index(drop=True)
        )
        return FACTOR_PANEL.validate(FACTOR_PANEL.normalize(out, strict=True))

    @abstractmethod
    def compute_raw(self, inputs: FactorInputs) -> pd.DataFrame:
        """
        Purpose:
            The raw factor value per stock and session.

        Contract:
            Input:
                inputs: FactorInputs
            Output:
                DataFrame  -- columns trade_date, ts_code, value_raw (NaN allowed)
            Raises:
                (subclass-specific)
        """

    @staticmethod
    def _build_joined(frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
        out = frames[0]
        for frame in frames[1:]:
            out = out.merge(frame, on=["trade_date", "ts_code"], how="inner")
        return out
