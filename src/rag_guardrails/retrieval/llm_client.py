"""OpenRouter LLM client — OpenAI-compatible SDK with tenacity retry."""
from __future__ import annotations

import asyncio
import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from rag_guardrails.core.logging import get_logger

logger = get_logger(__name__)

_RETRYABLE = (
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.InternalServerError,
)


def make_client(api_key: str, base_url: str) -> openai.AsyncOpenAI:
    """Create an AsyncOpenAI client pointed at OpenRouter."""
    return openai.AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "RAG Guardrails",
        },
    )


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    reraise=True,
)
async def call_llm(
    client: openai.AsyncOpenAI,
    *,
    model: str,
    messages: list[dict],
    system: str | None = None,
    max_tokens: int = 1024,
    timeout: float = 30.0,
) -> str:
    """Call the LLM via OpenRouter with retry on transient errors. Returns answer text."""
    all_messages: list[dict] = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

    response = await asyncio.wait_for(
        client.chat.completions.create(
            model=model,
            messages=all_messages,
            max_tokens=max_tokens,
        ),
        timeout=timeout,
    )
    usage = response.usage
    logger.info(
        "llm_call_complete",
        model=model,
        input_tokens=usage.prompt_tokens if usage else None,
        output_tokens=usage.completion_tokens if usage else None,
    )
    return response.choices[0].message.content or ""
