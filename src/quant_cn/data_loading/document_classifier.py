"""Title rules → document type (config/documents.yaml, D-101)."""

from __future__ import annotations

import re

import pandas as pd

from quant_cn.core.document_source import DocumentSource


class DocumentClassifier:
    """
    Purpose:
        Give each listed document its type: the source's fixed `doc_type`, or the first title rule
        whose `include` matches and whose `exclude` does not (e.g. "2025年年度报告" → annual;
        "2025年年度报告摘要" → none; "2025年半年度报告" → semiannual because that rule comes first).

    Contract:
        Input:
            source: DocumentSource
        Output:
            instance; `compute_doc_types`
        Raises:
            (none)

    Used by:
        data_loading.DocumentDownloader  -- selects candidates

    Test cases:
        TC-DCL-001  rule order and exclude: semiannual before annual, summaries and English dropped
        TC-DCL-002  a fixed doc_type labels every row; an empty series stays empty
    """

    def __init__(self, source: DocumentSource) -> None:
        self._source = source
        self._rules = [
            (
                rule.doc_type,
                re.compile(rule.include),
                re.compile(rule.exclude) if rule.exclude else None,
            )
            for rule in source.rules
        ]

    def compute_doc_types(self, titles: pd.Series) -> pd.Series:
        """
        Purpose:
            Document type per title.

        Contract:
            Input:
                titles: pd.Series[str | None]
            Output:
                pd.Series[str | None]  -- same index; None = not wanted
            Raises:
                (none)
        """
        if self._source.doc_type is not None:
            return pd.Series(self._source.doc_type, index=titles.index, dtype=object)
        return pd.Series([self._find_doc_type(t) for t in titles], index=titles.index, dtype=object)

    def _find_doc_type(self, title: object) -> str | None:
        if not isinstance(title, str):
            return None
        for doc_type, include, exclude in self._rules:
            if include.search(title) and not (exclude and exclude.search(title)):
                return doc_type
        return None
