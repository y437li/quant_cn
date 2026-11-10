"""Extension point for LLM vendors used by extraction (D-098)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LlmReply:
    """
    Purpose:
        One LLM answer as parsed JSON, with the model and token usage, and whether it came from
        the response cache (a cached reply costs nothing and makes rebuilds deterministic).

    Contract:
        Input:
            content:           dict[str, Any]  -- the reply parsed as a JSON object
            model:             str
            prompt_tokens:     int >= 0
            completion_tokens: int >= 0
            cached:            bool
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.BaseLlmClient           -- return type of fetch_json
        data_loading.DeepSeekClient  -- builds it

    Test cases:
        TC-DSC-001  (via DeepSeekClient) content parsed, usage recorded
    """

    content: dict[str, Any]
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached: bool = False
    raw: str = field(default="", repr=False)


class BaseLlmClient(ABC):
    """
    Purpose:
        Abstract chat-completion client that returns a JSON object: one system prompt, one user
        message, an optional model override. Vendors subclass it; extractors depend on this.

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance with `fetch_json`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        data_loading.DeepSeekClient          -- subclass
        industry_graph.ApplicationExtractor  -- injected client
        industry_graph.ValuationExtractor    -- injected client
        industry_graph.QuarterlyNoteExtractor  -- injected client
        industry_graph.BrokerViewSynthesizer  -- injected client
        industry_graph.BusinessModeExtractor  -- injected client
        industry_graph.PricingAdjudicator  -- injected client
        industry_graph.MoatExtractor  -- injected client

    Test cases:
        TC-BAC-001  cannot be instantiated; subclass must implement fetch_json
    """

    @abstractmethod
    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        """
        Purpose:
            Ask the model and return its answer parsed as a JSON object.

        Contract:
            Input:
                system: str        -- instructions, including the JSON shape expected
                user:   str        -- the material to read
                model:  str | None -- override of the configured model
                stop:   Sequence[str] -- optional stop sequences
            Output:
                LlmReply
            Raises:
                DataSourceError  -- vendor or network failure after retries, or a reply that is
                                    not a JSON object
                ConfigError      -- API key missing
        """
