"""LLM access behind one interface, so tests run on FakeLLMClient at no API cost."""

import logging
import time
from collections.abc import Iterator
from functools import lru_cache
from typing import Literal, Protocol, TypedDict, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.core.errors import LLMUnavailable

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class LLMClient(Protocol):
    model: str

    def structured(self, prompt: str, schema: type[T], system: str | None = None) -> T: ...

    def stream(self, messages: list[Message], system: str | None = None) -> Iterator[str]: ...


class ClaudeClient:
    def __init__(self, api_key: str, model: str):
        # The SDK already retries 408/409/429/5xx and connection errors twice with backoff.
        self._client = anthropic.Anthropic(api_key=api_key or None, max_retries=2)
        self.model = model

    def structured(self, prompt: str, schema: type[T], system: str | None = None) -> T:
        kwargs = {"system": system} if system else {}
        # Structured outputs constrain the JSON; one repair retry covers anything that still fails validation.
        for attempt in range(2):
            started = time.perf_counter()
            try:
                response = self._client.messages.parse(
                    model=self.model,
                    max_tokens=16000,
                    messages=[{"role": "user", "content": prompt}],
                    output_format=schema,
                    **kwargs,
                )
            except ValidationError:
                if attempt == 0:
                    continue
                raise LLMUnavailable("The model returned data in an unexpected shape.", retryable=False)
            except (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError) as exc:
                raise LLMUnavailable(f"Claude is unavailable right now ({type(exc).__name__}).")
            except anthropic.APIStatusError as exc:
                raise LLMUnavailable(f"Claude rejected the request ({exc.status_code}).", retryable=False)

            self._log_usage(response, started)
            if response.stop_reason == "refusal":
                raise LLMUnavailable("Claude declined to process this document.", retryable=False)
            if response.stop_reason == "max_tokens" or response.parsed_output is None:
                raise LLMUnavailable("The model's answer was cut off.", retryable=False)
            return response.parsed_output
        raise AssertionError("unreachable")

    def stream(self, messages: list[Message], system: str | None = None) -> Iterator[str]:
        kwargs = {"system": system} if system else {}
        try:
            with self._client.messages.stream(
                model=self.model, max_tokens=4000, messages=messages, **kwargs
            ) as stream:
                yield from stream.text_stream
        except anthropic.APIError as exc:
            raise LLMUnavailable(f"Claude is unavailable right now ({type(exc).__name__}).")

    def _log_usage(self, response, started: float) -> None:
        logger.info(
            "llm call",
            extra={
                "model": self.model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_ms": round((time.perf_counter() - started) * 1000),
            },
        )


class FakeLLMClient:
    """Returns canned responses keyed by schema; used in unit tests."""

    model = "fake"

    def __init__(self, responses: dict[type[BaseModel], BaseModel] | None = None, stream_text: str = ""):
        self.responses = responses or {}
        self.stream_text = stream_text
        self.prompts: list[str] = []

    def structured(self, prompt: str, schema: type[T], system: str | None = None) -> T:
        self.prompts.append(prompt)
        return self.responses[schema]  # type: ignore[return-value]

    def stream(self, messages: list[Message], system: str | None = None) -> Iterator[str]:
        yield from self.stream_text.split(" ")


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    return ClaudeClient(settings.anthropic_api_key, settings.llm_model)
