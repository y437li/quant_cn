"""The Barra-style A-share risk model (CNE5 family): stages and stored-model reads (plan 05)."""

from __future__ import annotations

import itertools
import logging

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.core.frames import FACTOR_RETURN
from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.descriptor_builder import DescriptorBuilder
from quant_cn.risk.exposure_standardizer import INDUSTRY_PREFIX, ExposureStandardizer
from quant_cn.risk.factor_covariance_estimator import FactorCovarianceEstimator
from quant_cn.risk.factor_return_estimator import COUNTRY, FactorReturnEstimator
from quant_cn.risk.risk_input_loader import RiskInputs
from quant_cn.risk.risk_snapshot import RiskSnapshot
from quant_cn.risk.specific_risk_estimator import SpecificRiskEstimator

logger = logging.getLogger(__name__)

EXPOSURE_VIEW = "derived.risk_exposure"
COV_VIEW = "derived.risk_factor_cov"
SPECIFIC_VIEW = "derived.risk_specific_risk"


class RiskModel(BaseRiskModel):
    """
    Purpose:
        CNE5-style model for A-shares (country + Shenwan L1 + configured styles) as a sequence
        of pure stages the pipeline step runs year by year: exposures from RiskInputs
        (DescriptorBuilder -> ExposureStandardizer), factor returns and residuals (exposures at
        t-1, returns t-1 -> t, circ_mv at t-1; FactorReturnEstimator), the factor covariance
        over the whole factor-return history (FactorCovarianceEstimator) and specific risk
        (SpecificRiskEstimator). Reads the stored frames back from derived.risk_* views for
        portfolio questions.

    Contract:
        Input:
            settings: RiskModelSettings; descriptors: DescriptorBuilder
            standardizer: ExposureStandardizer; returns: FactorReturnEstimator
            covariance: FactorCovarianceEstimator; specific: SpecificRiskEstimator
            query: LakeQuery
        Output:
            instance; stage methods `compute_exposures`, `compute_factor_returns`,
            `build_regression_panel`, `compute_monitor_returns`, `compute_covariance`,
            `compute_specific_time_series`, `compute_specific_session`,
            `compute_specific_final`; `load_snapshot`
        Raises:
            (none at construction)

    Used by:
        risk.RiskModelFactory   -- builds it
        pipeline.RiskModelStep  -- runs the stages and writes the frames

    Test cases:
        TC-RM-001  stages on a synthetic market: exposures -> factor returns recover the planted
                   returns; covariance and specific risk frames validate
        TC-RM-002  factor returns pair exposures at t-1 with returns on t (no look-ahead)
        TC-RM-004  compute_monitor_returns is empty without monitor styles and reports one
                   series per monitor style otherwise
        TC-RM-003  load_snapshot rebuilds X (with country), F and specific vol from the views;
                   a session without frames raises LakeError
    """

    def __init__(
        self,
        settings: RiskModelSettings,
        descriptors: DescriptorBuilder,
        standardizer: ExposureStandardizer,
        returns: FactorReturnEstimator,
        covariance: FactorCovarianceEstimator,
        specific: SpecificRiskEstimator,
        query: LakeQuery,
    ) -> None:
        super().__init__(settings.name)
        self._s = settings
        self._descriptors = descriptors
        self._standardizer = standardizer
        self._returns = returns
        self._covariance = covariance
        self._specific = specific
        self._query = query

    def compute_exposures(self, inputs: RiskInputs) -> pd.DataFrame:
        """
        Purpose:
            RISK_EXPOSURE for the inputs' window.

        Contract:
            Input:
                inputs: RiskInputs
            Output:
                DataFrame  -- RISK_EXPOSURE
            Raises:
                KeyError  -- input panels lack columns
        """
        return self._standardizer.compute(self._descriptors.compute(inputs))

    def compute_factor_returns(
        self, exposures: pd.DataFrame, inputs: RiskInputs
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purpose:
            FACTOR_RETURN and SPECIFIC_RETURN for the sessions of [inputs.start, inputs.end].

        Contract:
            Input:
                exposures: DataFrame  -- RISK_EXPOSURE covering the session before start to end
                inputs:    RiskInputs -- prices (returns) and basic (circ_mv) panels
            Output:
                tuple[DataFrame, DataFrame]  -- FACTOR_RETURN, SPECIFIC_RETURN
            Raises:
                KeyError  -- missing columns
        """
        panel = self.build_regression_panel(exposures, inputs)
        return self._returns.compute(panel)

    def compute_monitor_returns(self, exposures: pd.DataFrame, inputs: RiskInputs) -> pd.DataFrame:
        """
        Purpose:
            Daily returns of the monitor styles (D-130), estimated beside the model.

        Contract:
            Input:
                exposures: DataFrame  -- RISK_EXPOSURE incl. monitor styles, from the session
                                         before start to end
                inputs:    RiskInputs
            Output:
                DataFrame  -- FACTOR_RETURN of the monitor styles (empty when none configured)
            Raises:
                KeyError  -- missing columns
        """
        names = [m.name for m in self._s.monitor_styles]
        if not names:
            return FACTOR_RETURN.normalize(pd.DataFrame(columns=FACTOR_RETURN.columns), strict=True)
        return self._returns.compute_monitor(self.build_regression_panel(exposures, inputs), names)

    def build_regression_panel(self, exposures: pd.DataFrame, inputs: RiskInputs) -> pd.DataFrame:
        """
        Purpose:
            One row per stock and return session t: ret (t-1 -> t), circ_mv (CNY at t-1),
            l1_code and style exposures at t-1.

        Contract:
            Input:
                exposures: DataFrame  -- RISK_EXPOSURE
                inputs:    RiskInputs
            Output:
                DataFrame  -- trade_date (= t, in [start, end]), ts_code, ret, circ_mv, l1_code,
                              style columns
            Raises:
                KeyError  -- missing columns
        """
        close = inputs.prices.pivot(index="trade_date", columns="ts_code", values="close_adj")
        close = close.sort_index()
        sessions = list(close.index)
        next_session = dict(itertools.pairwise(sessions))
        ret = (
            (close / close.shift(1) - 1.0)
            .reset_index()
            .melt(id_vars="trade_date", var_name="ts_code", value_name="ret")
        )
        ret = ret.dropna(subset=["ret"])
        x = self._build_wide_exposures(exposures)
        caps = inputs.basic[["trade_date", "ts_code", "circ_mv"]].assign(
            circ_mv=lambda f: f["circ_mv"] * 1e4
        )
        x = x.merge(caps, on=["trade_date", "ts_code"], how="left")
        x["trade_date"] = x["trade_date"].map(next_session)
        x = x.dropna(subset=["trade_date"])
        panel = x.merge(ret, on=["trade_date", "ts_code"], how="inner")
        inside = (panel["trade_date"] >= inputs.start) & (panel["trade_date"] <= inputs.end)
        return panel[inside].reset_index(drop=True)

    def compute_covariance(
        self, factor_returns: pd.DataFrame, start: str | None = None
    ) -> pd.DataFrame:
        """
        Purpose:
            FACTOR_COV from the factor-return history.

        Contract:
            Input:
                factor_returns: DataFrame  -- FACTOR_RETURN, full history
                start: str | None          -- first session to output
            Output:
                DataFrame  -- FACTOR_COV
            Raises:
                SchemaError  -- invalid input
        """
        return self._covariance.compute(factor_returns, start)

    def compute_specific_session(
        self, sigma_ts: pd.Series, obs: pd.Series, exposures: pd.DataFrame, cap: pd.Series
    ) -> pd.DataFrame:
        """
        Purpose:
            Pre-regime specific vol of one session's members.

        Contract:
            Input:
                sigma_ts, obs: Series  -- index ts_code (time-series vol, residual counts)
                exposures: DataFrame   -- RISK_EXPOSURE rows of the session
                cap: Series            -- index ts_code, circ_mv (CNY)
            Output:
                DataFrame  -- ts_code, sigma, sigma_raw, g, cap (one row per member)
            Raises:
                KeyError  -- missing columns
        """
        x = exposures.pivot(index="ts_code", columns="factor", values="exposure")
        x = x.loc[:, x.notna().any()]
        industries = [c for c in x.columns if c.startswith(INDUSTRY_PREFIX)]
        x[industries] = x[industries].fillna(0.0)
        names = x.index
        s_ts = sigma_ts.reindex(names).to_numpy(float)
        h = obs.reindex(names).to_numpy(float)
        c = cap.reindex(names).to_numpy(float)
        sigma, g = self._specific.compute_session(s_ts, h, x.to_numpy(float), c)
        return pd.DataFrame({"ts_code": names, "sigma": sigma, "sigma_raw": s_ts, "g": g, "cap": c})

    def compute_specific_time_series(
        self, resid: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purpose:
            Time-series specific vol and residual counts (SpecificRiskEstimator).

        Contract:
            Input:
                resid: DataFrame  -- sessions x stocks residuals, sorted
            Output:
                tuple[DataFrame, DataFrame]  -- sigma_ts, counts h
            Raises:
                (none)
        """
        return self._specific.compute_time_series(resid)

    def compute_specific_final(self, pre: pd.DataFrame, resid: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            SPECIFIC_RISK after the specific volatility regime adjustment.

        Contract:
            Input:
                pre:   DataFrame  -- compute_specific_session rows with trade_date, all sessions
                resid: DataFrame  -- sessions x stocks residuals
            Output:
                DataFrame  -- SPECIFIC_RISK
            Raises:
                SchemaError  -- invalid output
        """
        return self._specific.compute_final(pre, resid)

    def load_snapshot(self, trade_date: str) -> RiskSnapshot:
        """
        Purpose:
            The stored model of one session.

        Contract:
            Input:
                trade_date: str  -- YYYYMMDD
            Output:
                RiskSnapshot  -- exposures with a country column of 1 and every covariance
                                 factor (missing = 0); daily units
            Raises:
                LakeError  -- views missing or no rows for the session
        """
        for view in (EXPOSURE_VIEW, COV_VIEW, SPECIFIC_VIEW):
            if not self._query.has_view(view):
                raise LakeError(f"{view} missing: run the risk model step")
        where = "WHERE trade_date = ?"
        exp = self._query.sql(
            f"SELECT ts_code, factor, exposure FROM {EXPOSURE_VIEW} {where}", [trade_date]
        )
        cov = self._query.sql(
            f"SELECT factor_i, factor_j, cov FROM {COV_VIEW} {where}", [trade_date]
        )
        spec = self._query.sql(f"SELECT ts_code, sigma FROM {SPECIFIC_VIEW} {where}", [trade_date])
        if exp.empty or cov.empty or spec.empty:
            raise LakeError(f"no risk model frames for {trade_date}")
        labels = sorted(cov["factor_i"].unique())
        x = exp.pivot(index="ts_code", columns="factor", values="exposure").assign(**{COUNTRY: 1.0})
        x = x.reindex(columns=labels).fillna(0.0)
        matrix = pd.DataFrame(RiskSnapshot.build_matrix(cov, labels), index=labels, columns=labels)
        return RiskSnapshot(trade_date, x, matrix, spec.set_index("ts_code")["sigma"])

    @staticmethod
    def _build_wide_exposures(exposures: pd.DataFrame) -> pd.DataFrame:
        industry = exposures["factor"].str.startswith(INDUSTRY_PREFIX)
        styles = exposures[~industry].pivot(
            index=["trade_date", "ts_code"], columns="factor", values="exposure"
        )
        l1 = (
            exposures[industry]
            .assign(l1_code=lambda f: f["factor"].str[len(INDUSTRY_PREFIX) :])
            .set_index(["trade_date", "ts_code"])["l1_code"]
        )
        out = styles.join(l1, how="outer").reset_index()
        out.columns.name = None
        return out
