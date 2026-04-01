"""
Structured query handler — translates natural language metadata questions
to SQL against the documents table, executes safely, returns formatted results.

Allowed schema (read-only, documents table only):
  documents(id, filename, file_size, chunk_count, status, created_at, mime_type)
"""
from __future__ import annotations

import re

from rag_guardrails.core.logging import get_logger

logger = get_logger(__name__)

_SCHEMA_DESCRIPTION = """
Table: documents
Columns:
  id          INTEGER  — unique document ID
  filename    TEXT     — uploaded filename (e.g. 'gdpr_policy.pdf')
  file_size   INTEGER  — file size in bytes
  chunk_count INTEGER  — number of text chunks extracted
  status      TEXT     — 'ready', 'processing', 'error', or 'quarantined'
  created_at  TIMESTAMPTZ — when the document was uploaded
  mime_type   TEXT     — MIME type (e.g. 'application/pdf', 'text/plain')
"""

_SQL_PROMPT = """You are a SQL generator for a document knowledge base.
Write a single read-only PostgreSQL SELECT query to answer the question.

{schema}

Rules:
- Only use the documents table. No JOINs to other tables.
- Only SELECT statements are allowed. No INSERT, UPDATE, DELETE, DROP, etc.
- Use standard PostgreSQL syntax.
- For date filtering, use created_at with TIMESTAMPTZ comparisons.
- Return only the SQL query, nothing else. No markdown, no explanation.

Question: {question}
SQL:"""


def _is_safe_sql(sql: str) -> bool:
    """Reject anything that isn't a plain SELECT on documents."""
    upper = sql.upper().strip()
    if not upper.startswith("SELECT"):
        return False
    # Block any data-mutating or structural keywords
    dangerous = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE"
        r"|EXEC|EXECUTE|COPY|CALL|DO|SET\s+SESSION|pg_)\b",
        re.IGNORECASE,
    )
    if dangerous.search(sql):
        return False
    # Only allow the documents table
    if re.search(r"\b(?!documents\b)\w+\s*\.", sql, re.IGNORECASE):
        return False
    return True


def _format_results(rows: list[dict]) -> str:
    """Format query results as readable plain text."""
    if not rows:
        return "No documents found matching that criteria."

    if len(rows) == 1 and len(rows[0]) == 1:
        # Single value (e.g., COUNT) — return directly
        val = list(rows[0].values())[0]
        return str(val)

    lines = []
    for row in rows[:50]:  # cap at 50 rows in context
        line = "  ".join(f"{k}: {v}" for k, v in row.items())
        lines.append(f"- {line}")
    result = "\n".join(lines)
    if len(rows) > 50:
        result += f"\n... and {len(rows) - 50} more"
    return result


async def run_structured_query(question: str) -> tuple[str, str]:
    """
    Translate question to SQL, execute, return (answer_text, sql_used).
    answer_text is a human-readable string suitable for including in LLM context.
    """
    from rag_guardrails.retrieval.llm_client import call_llm, make_client
    from rag_guardrails.core.config import get_settings
    from rag_guardrails.core.database import AsyncSessionLocal
    from sqlalchemy import text

    settings = get_settings()
    client = make_client(settings.openrouter_api_key, settings.openrouter_base_url)

    prompt = _SQL_PROMPT.format(schema=_SCHEMA_DESCRIPTION, question=question)
    try:
        raw_sql = await call_llm(
            client,
            model=settings.openrouter_model,
            messages=[{"role": "user", "content": prompt}],
            system="You are a SQL generator. Reply with only the SQL query.",
            max_tokens=200,
        )
    except Exception as exc:
        logger.error("structured_sql_generation_failed", error=str(exc))
        return "Unable to generate SQL query for this question.", ""

    # Strip markdown fences if model added them
    sql = re.sub(r"```(?:sql)?|```", "", raw_sql).strip()

    if not _is_safe_sql(sql):
        logger.warning("structured_sql_unsafe", sql=sql[:200])
        return "The generated query was rejected for safety reasons.", sql

    logger.info("structured_query_executing", sql=sql[:200])

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(text(sql))
            rows = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    except Exception as exc:
        logger.error("structured_sql_execution_failed", error=str(exc), sql=sql[:200])
        return f"Query execution failed: {exc}", sql

    answer = _format_results(rows)
    return answer, sql
