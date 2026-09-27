from __future__ import annotations

import pytest

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.base_fetch_log import BaseFetchLog
from quant_cn.core.base_fetcher import BaseFetcher
from quant_cn.core.base_run_log import BaseRunLog
from quant_cn.core.base_step import BaseStep
from quant_cn.core.base_store import BaseStore


# TC-BAC-001
@pytest.mark.parametrize(
    "base", [BaseApiClient, BaseStore, BaseFetchLog, BaseRunLog, BaseStep, BaseFetcher]
)
def test_tc_bac_001_abstract(base: type) -> None:
    with pytest.raises(TypeError):
        base()
