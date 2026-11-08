"""DeepSeek chat completions as a JSON-returning LLM client with a response cache (D-098)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from quant_cn.core.base_llm_client import BaseLlmClient, LlmReply
from quant_cn.core.clock import Clock
from quant_cn.core.config import LlmConfig
from quant_cn.core.exceptions import ConfigError
from quant_cn.data_loading.http_transport import HttpTransport
from quant_cn.data_loading.request_pacer import RequestPacer

logger = logging.getLogger(__name__)
BEIJING = ZoneInfo("Asia/Shanghai")
WEEKDAYS = 5


class DeepSeekClient(BaseLlmClient):
    """
    Purpose:
        Call the DeepSeek (OpenAI-compatible) chat-completions endpoint with JSON output and
        temperature 0 and model reasoning off unless LlmConfig.thinking, paced and retried by
        RequestPacer. Every reply is cached on disk under
        `cache_dir/<hash[:2]>/<hash>.json`, keyed by model + system + user + stop, so a re-run
        costs nothing and gives the same graph (D-098). The key comes from LlmConfig (env only).

    Contract:
        Input:
            llm_config: LlmConfig
            clock:      Clock
            cache_dir:  Path | None          -- None disables the cache
            transport:  HttpTransport | None -- default HttpTransport()
        Output:
            instance; `fetch_json`, `get_usage`, `record_usage`, `compute_cost`
        Raises:
            (none at construction; a missing key fails at the first uncached call)

    Used by:
        research_space prototypes (plan 12 phase 4a pilot); ExtractionStep (to come)

    Test cases:
        TC-DSC-001  posts model, messages, JSON response format and auth header; parses content
                    and usage
        TC-DSC-002  a second identical call is served from the cache without a request
        TC-DSC-005  record_usage appends one JSON line per call with label and cost
        TC-DSC-004  cost at configured prices (miss / hit / output); half off-peak, Beijing time
        TC-DSC-003  a reply that is not a JSON object is retried, then raises DataSourceError;
                    a missing key raises ConfigError
    """

    def __init__(
        self,
        llm_config: LlmConfig,
        clock: Clock,
        cache_dir: Path | None = None,
        transport: HttpTransport | None = None,
    ) -> None:
        self._config = llm_config
        self._cache_dir = cache_dir
        self._transport = transport or HttpTransport()
        self._pacer = RequestPacer(
            clock,
            "deepseek",
            llm_config.min_interval_s,
            llm_config.retries,
            llm_config.retry_sleep_s,
        )
        self._clock = clock
        self._usage: dict[str, float] = {
            "calls": 0, "cached": 0, "prompt_tokens": 0, "completion_tokens": 0,
            "cache_hit_tokens": 0, "cost_cny": 0.0,
        }  # fmt: skip

    def fetch_json(
        self, system: str, user: str, model: str | None = None, stop: Sequence[str] = ()
    ) -> LlmReply:
        """
        Purpose:
            One JSON answer, from the cache when the same request was made before.

        Contract:
            Input:
                system: str; user: str; model: str | None; stop: Sequence[str]
            Output:
                LlmReply  -- cached=True when served from disk
            Raises:
                ConfigError      -- DEEPSEEK_API_KEY not set (uncached call)
                DataSourceError  -- failure after retries, or the reply is not a JSON object
        """
        name = model or self._config.model
        payload = self._build_payload(name, system, user, stop)
        key = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        cached = self._read_cache(key)
        if cached is not None:
            self._usage["cached"] += 1
            return LlmReply(
                cached["content"], name, cached["prompt_tokens"], cached["completion_tokens"], True
            )
        if not self._config.api_key:
            raise ConfigError("DEEPSEEK_API_KEY is not set (put it in .env)")
        headers = {"Authorization": f"Bearer {self._config.api_key}"}
        content, usage = self._pacer.run(
            key[:12],
            lambda: self._parse(
                self._transport.fetch_json(
                    self._config.url, payload, self._config.timeout_s, headers
                )
            ),
        )
        reply = LlmReply(
            content, name, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        )
        self._add_usage(name, reply, int(usage.get("prompt_cache_hit_tokens", 0)))
        self._write_cache(key, reply)
        return reply

    def _build_payload(
        self, name: str, system: str, user: str, stop: Sequence[str]
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": name,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0,
            "max_tokens": self._config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        if not self._config.thinking:
            payload["thinking"] = {"type": "disabled"}
        if stop:
            payload["stop"] = list(stop)
        return payload

    def _add_usage(self, name: str, reply: LlmReply, hit: int) -> None:
        self._usage["calls"] += 1
        self._usage["prompt_tokens"] += reply.prompt_tokens
        self._usage["completion_tokens"] += reply.completion_tokens
        self._usage["cache_hit_tokens"] += hit
        self._usage["cost_cny"] += self.compute_cost(
            name, reply.prompt_tokens - hit, hit, reply.completion_tokens
        )

    def get_usage(self) -> dict[str, float]:
        """
        Purpose:
            Calls, local-cache hits, tokens and money spent since construction.

        Contract:
            Input:
                (none)
            Output:
                dict[str, float]  -- calls, cached (local cache), prompt_tokens, completion_tokens,
                                     cache_hit_tokens (vendor prompt cache), cost_cny
            Raises:
                (none)
        """
        return dict(self._usage)

    def record_usage(self, ledger: Path, label: str) -> dict[str, Any]:
        """
        Purpose:
            Append this client's usage so far as one JSON line to the cost ledger.

        Contract:
            Input:
                ledger: Path  -- e.g. lake meta/llm_usage.jsonl (created when missing)
                label:  str   -- what was run, e.g. "plan12-4a applications 10 companies"
            Output:
                dict  -- the line written: at, label, model, usage fields
            Raises:
                OSError  -- the ledger cannot be written
        """
        line = {"at": self._clock.get_now().isoformat(timespec="seconds"), "label": label,
                "model": self._config.model, **self._usage}  # fmt: skip
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        return line

    def compute_cost(
        self, model: str, miss_tokens: int, hit_tokens: int, output_tokens: int
    ) -> float:
        """
        Purpose:
            CNY cost of one call at the configured peak prices, halved off-peak (Beijing time).

        Contract:
            Input:
                model: str; miss_tokens, hit_tokens, output_tokens: int >= 0
            Output:
                float  -- CNY; 0.0 when the model has no configured price (warning logged)
            Raises:
                (none)
        """
        price = self._config.prices.get(model)
        if not price:
            logger.warning("no price configured for %s: cost not counted", model)
            return 0.0
        peak = (
            miss_tokens * price["input_miss"]
            + hit_tokens * price["input_hit"]
            + output_tokens * price["output"]
        ) / 1e6
        return peak if self._is_peak() else peak / 2

    def _is_peak(self) -> bool:
        now = self._clock.get_now().astimezone(BEIJING)
        if now.weekday() >= WEEKDAYS:
            return False
        return any(start <= now.hour < end for start, end in self._config.peak_hours)

    @staticmethod
    def _parse(response: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            choice = response["choices"][0]
            if choice.get("finish_reason") == "length":
                raise ValueError(
                    "reply truncated at max_tokens (raise llm.max_tokens or shorten input)"
                )
            text = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"unexpected reply shape: {str(response)[:200]}") from exc
        try:
            content = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"reply is not JSON: {text[:200]}") from exc
        if not isinstance(content, dict):
            raise ValueError("reply JSON is not an object")
        return content, dict(response.get("usage") or {})

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        if self._cache_dir is None:
            return None
        path = self._cache_dir / key[:2] / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _write_cache(self, key: str, reply: LlmReply) -> None:
        if self._cache_dir is None:
            return
        path = self._cache_dir / key[:2] / f"{key}.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(
                json.dumps(
                    {
                        "content": reply.content,
                        "model": reply.model,
                        "prompt_tokens": reply.prompt_tokens,
                        "completion_tokens": reply.completion_tokens,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            os.replace(tmp, path)
        except OSError as exc:  # a cache failure must not lose a paid answer's use in this run
            logger.warning("llm cache write failed: %s", exc)
