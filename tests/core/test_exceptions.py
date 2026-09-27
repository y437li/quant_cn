from __future__ import annotations

import pytest

from quant_cn.core.exceptions import (
    ConfigError,
    DataSourceError,
    LakeError,
    PermissionDeniedError,
    QuantCnError,
    SchemaError,
)


# TC-QCE-001
@pytest.mark.parametrize(
    "exc", [ConfigError, SchemaError, DataSourceError, PermissionDeniedError, LakeError]
)
def test_tc_qce_001_hierarchy(exc: type[Exception]) -> None:
    assert issubclass(exc, QuantCnError)
    assert issubclass(PermissionDeniedError, DataSourceError)
