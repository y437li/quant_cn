"""Build the configured risk model from RiskModelSettings (plan 05 phase 5)."""

from __future__ import annotations

from quant_cn.core.risk_model_settings import RiskModelSettings
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.risk.analyst_descriptors import AnalystDescriptors
from quant_cn.risk.bayesian_shrinker import BayesianShrinker
from quant_cn.risk.descriptor_builder import DescriptorBuilder
from quant_cn.risk.eigenfactor_adjuster import EigenfactorAdjuster
from quant_cn.risk.exposure_standardizer import ExposureStandardizer
from quant_cn.risk.factor_covariance_estimator import FactorCovarianceEstimator
from quant_cn.risk.factor_return_estimator import FactorReturnEstimator
from quant_cn.risk.fundamental_descriptors import FundamentalDescriptors
from quant_cn.risk.price_descriptors import PriceDescriptors
from quant_cn.risk.risk_model import RiskModel
from quant_cn.risk.specific_risk_estimator import SpecificRiskEstimator
from quant_cn.risk.structural_specific_risk import StructuralSpecificRisk
from quant_cn.risk.volatility_regime_adjuster import VolatilityRegimeAdjuster
from quant_cn.statistic.neutralizer import Neutralizer
from quant_cn.statistic.standardizer import Standardizer


class RiskModelFactory:
    """
    Purpose:
        Wire a RiskModel and all its estimators from one RiskModelSettings (config/
        risk_model.yaml), so variants (six styles vs ten, other half-lives) are config only.

    Contract:
        Input:
            query: LakeQuery  -- passed to the model for stored-frame reads
        Output:
            instance; `build(settings) -> RiskModel`
        Raises:
            (none at construction)

    Used by:
        cli.GaugeCommands  -- injected type or call
        cli.ServiceBuilder  -- risk model step
        research_space/notebooks/20261111_risk_model_validation.ipynb  -- variants
        cli.AppServiceBuilder  -- wires it

    Test cases:
        TC-RMF-001  build returns a RiskModel named after the settings with the configured styles
    """

    def __init__(self, query: LakeQuery) -> None:
        self._query = query

    def build(self, settings: RiskModelSettings) -> RiskModel:
        """
        Purpose:
            The model for these settings.

        Contract:
            Input:
                settings: RiskModelSettings
            Output:
                RiskModel
            Raises:
                (none)
        """
        standardizer = Standardizer()
        regime = VolatilityRegimeAdjuster(settings.vra_half_life)
        descriptors = DescriptorBuilder(
            PriceDescriptors(),
            FundamentalDescriptors(),
            standardizer,
            settings.exclude_suffixes,
            AnalystDescriptors(),
        )
        exposures = ExposureStandardizer(settings, standardizer, Neutralizer())
        returns = FactorReturnEstimator(
            settings.style_names, settings.weight_cap_quantile, settings.min_regression_names
        )
        covariance = FactorCovarianceEstimator(
            settings, EigenfactorAdjuster(settings.eigen_sims, settings.eigen_scale), regime
        )
        specific = SpecificRiskEstimator(
            settings,
            StructuralSpecificRisk(),
            BayesianShrinker(settings.shrink_q, settings.shrink_groups),
            regime,
        )
        return RiskModel(
            settings, descriptors, exposures, returns, covariance, specific, self._query
        )
