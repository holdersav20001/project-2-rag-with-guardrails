"""
Query router — classifies incoming queries as semantic, structured, or hybrid.

semantic   → vector search (concept/content questions about document text)
structured → SQL query (metadata questions: counts, dates, filenames)
hybrid     → both, results merged

Classification uses a lightweight LLM call with few-shot examples.
Cached per query string to avoid duplicate LLM calls.
"""
from __future__ import annotations

import re
from typing import Literal

from rag_guardrails.core.logging import get_logger

logger = get_logger(__name__)

QueryType = Literal["semantic", "structured", "hybrid"]

_FEW_SHOT = """Classify the following query as one of: semantic, structured, or hybrid.

semantic  = asks about the CONTENT or MEANING of documents (concepts, rules, explanations)
structured = asks about METADATA (counts, dates, filenames, file sizes, statuses)
hybrid    = needs both content and metadata to answer fully

Examples:
Q: What does our data retention policy say?
A: semantic

Q: How many documents have been uploaded?
A: structured

Q: When was the GDPR policy document uploaded?
A: structured

Q: What documents mention data breach notification, and when were they added?
A: hybrid

Q: List all PDF files in the knowledge base.
A: structured

Q: How many documents were uploaded in March?
A: structured

Q: What is the right to erasure under GDPR?
A: semantic

Q: What does the most recently uploaded document say about cookies?
A: hybrid

Q: How long must we keep personal data?
A: semantic

Q: What is the total size of all uploaded documents?
A: structured

Q: What is the time limit for responding to a subject access request?
A: semantic

Q: What are the legal requirements around data breach notification deadlines?
A: semantic

Q: How long do organisations have to comply with erasure requests?
A: semantic

Q: What does the SAR guidance say about the response timeline?
A: semantic

Now classify:
Q: {query}
A:"""


async def classify_query(query: str) -> QueryType:
    """Classify query using LLM few-shot. Returns 'semantic', 'structured', or 'hybrid'."""
    from rag_guardrails.retrieval.llm_client import call_llm, make_client
    from rag_guardrails.core.config import get_settings

    settings = get_settings()
    client = make_client(settings.openrouter_api_key, settings.openrouter_base_url)

    prompt = _FEW_SHOT.format(query=query)
    try:
        response = await call_llm(
            client,
            model=settings.openrouter_model,
            messages=[{"role": "user", "content": prompt}],
            system="You are a query classifier. Reply with exactly one word: semantic, structured, or hybrid.",
            max_tokens=10,
        )
        raw = response.strip().lower()
        # Extract the first matching keyword in case the model adds punctuation
        for qt in ("structured", "hybrid", "semantic"):
            if qt in raw:
                logger.info("query_routed", query_type=qt, query=query[:80])
                return qt  # type: ignore[return-value]
    except Exception as exc:
        logger.warning("query_router_failed", error=str(exc), fallback="semantic")

    return "semantic"
