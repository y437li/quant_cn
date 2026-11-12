"""Settings of the Barra-style risk model (plan 05, D-045, D-061, D-127): config/risk_model.yaml."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StyleSpec(BaseModel):
    """
    Purpose:
        One style factor: its descriptors with CNE5 weights and the factors it is orthogonalised
        against (RISK_FACTOR_LIST §1).

    Contract:
        Input:
            name:        str               -- RISK_EXPOSURE.factor, e.g. "size"
            descriptors: dict[str, float]  -- descriptor name -> weight > 0 (renormalised over the
                                              descriptors a stock has)
            orthogonalize_to: list[str]    -- earlier style names regressed out (cap weighted)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- empty descriptors, non-positive weight, extra keys

    Used by:
        core.RiskModelSettings  -- field `styles`
        risk.ExposureStandardizer  -- injected type or call

    Test cases:
        TC-RMS-001  config/risk_model.yaml loads; style weights per CNE5; missing file = defaults
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    descriptors: dict[str, float] = Field(min_length=1)
    orthogonalize_to: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_weights(self) -> StyleSpec:
        """
        Purpose:
            Refuse non-positive descriptor weights.

        Contract:
            Input:
                (the model)
            Output:
                StyleSpec  -- self
            Raises:
                ValueError  -- a weight <= 0
        """
        if any(w <= 0 for w in self.descriptors.values()):
            raise ValueError(f"style {self.name}: descriptor weights must be > 0")
        return self


class ExternalSeriesSpec(BaseModel):
    """
    Purpose:
        One external daily series behind a partial-beta descriptor (D-128, D-134): where it is
        in the lake and how its dates map to China sessions.

    Contract:
        Input:
            descriptor: str  -- descriptor name it feeds, e.g. "us_beta"
            dataset:    str  -- dated lake dataset, e.g. "index_global", "fx_daily"
            code:       str  -- ts_code in that dataset, e.g. "SPX", "USDCNH.FXCM"
            column:     str  -- value column
            kind:       "pct" | "price"  -- percent change already, or a price to difference
            date_shift_days: int >= 0  -- calendar days added to the vendor date before the
                                          overnight alignment (FXCM dates bars by their open: 1)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- bad kind, negative shift, extra keys

    Used by:
        core.RiskModelSettings  -- field `external_series`
        risk.RiskInputLoader  -- injected type or call

    Test cases:
        TC-RMS-003  external series and theme baskets load from YAML; bad values refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    descriptor: str
    dataset: str
    code: str
    column: str = "pct_chg"
    kind: Literal["pct", "price"] = "pct"
    date_shift_days: int = Field(default=0, ge=0)


class ThemeBasketSpec(BaseModel):
    """
    Purpose:
        A theme basket behind a partial-beta descriptor (D-130): the circ_mv-weighted return
        of a concept's current members (excluding the stock itself), from the concept's list
        date on.

    Contract:
        Input:
            descriptor: str  -- descriptor name, e.g. "aidc_beta"
            concept:    str  -- ths_member ts_code, e.g. "885887.TI"
            start:      str  -- YYYYMMDD first session with a basket (concept list date)
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- malformed date, extra keys

    Used by:
        core.RiskModelSettings  -- field `theme_baskets`
        risk.RiskInputLoader  -- injected type or call

    Test cases:
        TC-RMS-003  external series and theme baskets load from YAML; bad values refused
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    descriptor: str
    concept: str
    start: str = Field(pattern=r"^\d{8}$")


class RiskModelSettings(BaseModel):
    """
    Purpose:
        Every tunable of the risk model in one typed object, CNE5 defaults (RISK_MODEL_DESIGN §1):
        estimation universe, style set, regression weights, covariance and specific-risk
        half-lives and lags, eigenfactor and volatility-regime adjustments.

    Contract:
        Input:
            name:            str    -- model id written into RISK_VALIDATION notes
            start:           str    -- YYYYMMDD first exposure date (needs 2018-09 daily_basic)
            exclude_suffixes: list[str]  -- ts_code suffixes outside the model (".BJ")
            external_series: list[ExternalSeriesSpec]  -- partial-beta series (D-128, D-134)
            theme_baskets:   list[ThemeBasketSpec]     -- theme partial betas (D-130)
            monitor_styles:  list[StyleSpec]  -- exposures and returns reported, kept out of the
                                                 regression and covariance (D-130)
            styles:          list[StyleSpec]  -- order matters for orthogonalisation
            winsor_sd:       float > 0  -- descriptor / factor clip in sd units (CNE5: 3)
            min_coverage:    float in (0, 1]  -- a style is regressed on a date only when this
                                                 share of the estimation universe has a raw value
            weight_cap_quantile: float in (0, 1]  -- sqrt-cap regression weights capped here
            min_regression_names: int  -- sessions with fewer usable stocks are not regressed
            vol_half_life, corr_half_life: int  -- factor covariance EWMA half-lives (90 / 480)
            cov_window:      int    -- factor-return sessions used per covariance date
            cov_nw_lags:     int >= 0  -- Newey-West lags on factor returns (2)
            horizon_days:    int >= 1  -- forecast horizon (21); NW scales to it
            min_factor_obs:  int    -- sessions before a factor's covariance is reported
            eigen_sims:      int >= 0  -- Monte-Carlo simulations (0 disables the adjustment)
            eigen_scale:     float  -- a in gamma = a (v - 1) + 1 (USE4: 1.2)
            eigen_refit_days: int >= 1  -- recompute the bias profile every N dates
            seed:            int    -- RNG seed of the simulations (reproducible rebuilds)
            vra_half_life:   int    -- volatility-regime EWMA half-life (42); 0 disables
            specific_half_life, specific_window, specific_nw_lags: int  -- 90 / 252 / 5
            specific_min_obs, specific_full_obs: int  -- blend structural below full_obs
            shrink_q:        float >= 0  -- Bayesian shrinkage intensity (0.1)
            shrink_groups:   int >= 1  -- size groups of the shrinkage prior (10)
            validation_portfolios: int  -- random long-only portfolios in the bias test (100)
            validation_names: int  -- stocks per random portfolio
            validation_sessions: int  -- forecast sessions in the bias tests (252)
            benchmarks: list[str]  -- index codes tested as portfolios (index_weight)
        Output:
            frozen pydantic model; `style_names`
        Raises:
            pydantic.ValidationError  -- out-of-range values, malformed date, extra keys,
                                         orthogonalisation against an unknown or later style

    Used by:
        core.Config                     -- field `risk_model`
        risk.ExposureStandardizer       -- styles, clip, coverage
        risk.FactorCovarianceEstimator  -- half-lives, window, lags
        risk.SpecificRiskEstimator      -- specific settings
        risk.RiskModelFactory           -- builds the model
        risk.RiskModel  -- injected type or call
        pipeline.RiskModelStep  -- injected type or call
        pipeline.RiskValidationWriter  -- injected type or call

    Test cases:
        TC-RMS-001  config/risk_model.yaml loads; style weights per CNE5; missing file = defaults
        TC-RMS-002  orthogonalising against an unknown style is refused; bad date refused;
                    a monitor style may not repeat a model style
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = "cne5_v1"
    start: str = Field(default="20190102", pattern=r"^\d{8}$")
    exclude_suffixes: list[str] = Field(default_factory=lambda: [".BJ"])
    external_series: list[ExternalSeriesSpec] = Field(default_factory=list)
    theme_baskets: list[ThemeBasketSpec] = Field(default_factory=list)
    monitor_styles: list[StyleSpec] = Field(default_factory=list)
    styles: list[StyleSpec] = Field(default_factory=list)
    winsor_sd: float = Field(default=3.0, gt=0)
    min_coverage: float = Field(default=0.5, gt=0, le=1)
    weight_cap_quantile: float = Field(default=0.95, gt=0, le=1)
    min_regression_names: int = Field(default=100, ge=10)
    vol_half_life: int = Field(default=90, ge=1)
    corr_half_life: int = Field(default=480, ge=1)
    cov_window: int = Field(default=1260, ge=21)
    cov_nw_lags: int = Field(default=2, ge=0)
    horizon_days: int = Field(default=21, ge=1)
    min_factor_obs: int = Field(default=63, ge=2)
    eigen_sims: int = Field(default=1000, ge=0)
    eigen_scale: float = Field(default=1.2, gt=0)
    eigen_refit_days: int = Field(default=21, ge=1)
    seed: int = 20260928
    vra_half_life: int = Field(default=42, ge=0)
    specific_half_life: int = Field(default=90, ge=1)
    specific_window: int = Field(default=252, ge=21)
    specific_nw_lags: int = Field(default=5, ge=0)
    specific_min_obs: int = Field(default=42, ge=2)
    specific_full_obs: int = Field(default=126, ge=2)
    shrink_q: float = Field(default=0.1, ge=0)
    shrink_groups: int = Field(default=10, ge=1)
    validation_portfolios: int = Field(default=100, ge=1)
    validation_names: int = Field(default=50, ge=1)
    validation_sessions: int = Field(default=252, ge=21)
    benchmarks: list[str] = Field(default_factory=lambda: ["000300.SH", "000905.SH", "000852.SH"])

    @model_validator(mode="after")
    def validate_styles(self) -> RiskModelSettings:
        """
        Purpose:
            Orthogonalisation may only target styles listed earlier; full_obs > min_obs.

        Contract:
            Input:
                (the model)
            Output:
                RiskModelSettings  -- self
            Raises:
                ValueError  -- unknown or later target; duplicate style; full_obs <= min_obs
        """
        seen: list[str] = []
        for style in self.styles:
            if style.name in seen:
                raise ValueError(f"duplicate style {style.name}")
            missing = [t for t in style.orthogonalize_to if t not in seen]
            if missing:
                raise ValueError(f"style {style.name} orthogonalised to unknown/later {missing}")
            seen.append(style.name)
        for style in self.monitor_styles:
            if style.name in seen:
                raise ValueError(f"monitor style {style.name} duplicates a style")
            if any(t not in seen for t in style.orthogonalize_to):
                raise ValueError(f"monitor style {style.name} orthogonalised to an unknown style")
            seen.append(style.name)
        if self.specific_full_obs <= self.specific_min_obs:
            raise ValueError("specific_full_obs must exceed specific_min_obs")
        return self

    @property
    def style_names(self) -> list[str]:
        """
        Purpose:
            Style factor names in configured order.

        Contract:
            Input:
                (none)
            Output:
                list[str]
            Raises:
                (none)
        """
        return [s.name for s in self.styles]
