from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_cn.core.config import Config
from quant_cn.core.document_source import DocumentRule, DocumentSource

BASE = {
    "dataset": "d",
    "id_column": "id",
    "code_column": "code",
    "date_column": "day",
    "title_column": "title",
    "url_template": "http://x/{id}",
    "file_template": "{id}.pdf",
}


# TC-DSR-001
def test_tc_dsr_001_yaml_loads_and_bad_regex(config: Config) -> None:
    assert {"cninfo", "em_industry", "em_stock"} <= set(config.documents)
    cninfo = config.documents["cninfo"]
    assert cninfo.a_share_only and cninfo.rules[0].doc_type == "semiannual"
    assert config.documents["em_industry"].folder == "eastmoney"
    with pytest.raises(ValidationError, match="bad regex"):
        DocumentRule(doc_type="x", include="(")


# TC-DSR-002
def test_tc_dsr_002_type_xor_rules() -> None:
    DocumentSource(**BASE, doc_type="industry_report")
    DocumentSource(**BASE, rules=[DocumentRule(doc_type="a", include="年度报告")])
    with pytest.raises(ValidationError, match="exactly one"):
        DocumentSource(**BASE)
    with pytest.raises(ValidationError, match="exactly one"):
        DocumentSource(**BASE, doc_type="x", rules=[DocumentRule(doc_type="a", include="b")])


# TC-DSR-003
def test_tc_dsr_003_concurrency_settings(config: Config) -> None:
    plain = DocumentSource(**BASE, doc_type="x")
    assert (plain.workers, plain.min_interval_s) == (4, 0.25)
    assert config.documents["em_industry"].min_interval_s == 0.3
    with pytest.raises(ValidationError):
        DocumentSource(**BASE, doc_type="x", workers=0)
    with pytest.raises(ValidationError):
        DocumentSource(**BASE, doc_type="x", min_interval_s=-1)
