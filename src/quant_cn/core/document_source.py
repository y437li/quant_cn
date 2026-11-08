"""Which documents are downloaded and where they land, as data (config/documents.yaml, D-101)."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentRule(BaseModel):
    """
    Purpose:
        One title rule: a title matching `include` and not `exclude` (regular expressions) is a
        document of `doc_type`.

    Contract:
        Input:
            doc_type: str         -- folder name, e.g. "annual"
            include:  str         -- regex searched in the title
            exclude:  str | None  -- regex that vetoes a match
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- a regex does not compile

    Used by:
        core.DocumentSource              -- field `rules`

    Test cases:
        TC-DSR-001  config/documents.yaml loads; an invalid regex is rejected
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_type: str
    include: str
    exclude: str | None = None

    @model_validator(mode="after")
    def _check_patterns(self) -> DocumentRule:
        for pattern in (self.include, self.exclude):
            if pattern is not None:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise ValueError(f"{self.doc_type}: bad regex {pattern!r}: {exc}") from exc
        return self


class DocumentSource(BaseModel):
    """
    Purpose:
        One document source of config/documents.yaml: the curated metadata dataset listing
        the documents, its key columns, the PDF URL and file-name templates (`{column}`
        placeholders), the folder under `documents/`, and how a row gets its doc type
        (a fixed `doc_type` or title `rules`, first match wins).

    Contract:
        Input:
            dataset:       str          -- curated metadata dataset
            id_column:     str          -- unique document id within the source
            code_column:   str          -- company or industry code used in file names
            date_column:   str          -- publication date YYYYMMDD (folder year/month)
            title_column:  str
            url_template:  str          -- e.g. "https://pdf.dfcfw.com/pdf/H3_{info_code}_1.pdf"
            file_template: str          -- e.g. "{sec_code}_{ann_id}.pdf"
            folder:        str | None   -- folder under documents/; default the source name
            a_share_only:  bool         -- keep codes listed in stock_basic only
            doc_type:      str | None   -- fixed type; exclusive with rules
            rules:         list[DocumentRule]
            workers:       int 1..16    -- parallel downloads for this source
            min_interval_s: float >= 0  -- spacing of request starts; the site's limit, shared
                                           by all workers (run one download per site at a time)
            throttle_codes: list[int]   -- HTTP statuses meaning "slow down" (e.g. 429, 567)
            cooldown_s:     float >= 0  -- pause of all workers after a throttle status
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- both or neither of doc_type and rules

    Used by:
        core.Config                      -- field `documents`
        data_loading.DocumentClassifier  -- injected type or call
        data_loading.DocumentDownloader  -- injected type or call

    Test cases:
        TC-DSR-001  config/documents.yaml loads; an invalid regex is rejected
        TC-DSR-002  doc_type and rules are exclusive and one is required
        TC-DSR-003  workers and min_interval_s default to 4 and 0.25 and are validated
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset: str
    id_column: str
    code_column: str
    date_column: str
    title_column: str
    url_template: str
    file_template: str
    folder: str | None = None
    a_share_only: bool = False
    doc_type: str | None = None
    rules: list[DocumentRule] = []
    workers: int = Field(default=4, ge=1, le=16)
    min_interval_s: float = Field(default=0.25, ge=0)
    throttle_codes: list[int] = Field(default_factory=lambda: [429, 567])
    cooldown_s: float = Field(default=900.0, ge=0)

    @model_validator(mode="after")
    def _check_type_source(self) -> DocumentSource:
        if (self.doc_type is None) == (not self.rules):
            raise ValueError(f"{self.dataset}: give exactly one of doc_type and rules")
        return self
