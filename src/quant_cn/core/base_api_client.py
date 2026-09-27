"""Extension point for data vendors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

import pandas as pd


class BaseApiClient(ABC):
    """
    Purpose:
        Abstract vendor client: one logical query returns all pages as one DataFrame.

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance with `query`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        data_loading.TushareClient       -- production subclass
        core.BaseFetcher                 -- injected client type
        data_loading.FetcherFactory      -- injected client type

    Test cases:
        TC-BAC-001  cannot be instantiated; subclass must implement query
    """

    @abstractmethod
    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Run one query and return every row across pages.

        Contract:
            Input:
                api_name: str                -- vendor endpoint name
                params:   Mapping[str, str]  -- endpoint parameters (no paging keys)
                fields:   Sequence[str]      -- requested columns; empty = vendor default
            Output:
                DataFrame  -- vendor column names; zero rows allowed
            Raises:
                DataSourceError        -- vendor or network failure after retries
                PermissionDeniedError  -- account lacks access to the endpoint
        """
