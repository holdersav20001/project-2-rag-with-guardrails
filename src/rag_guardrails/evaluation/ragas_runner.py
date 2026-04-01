"""Ragas evaluation runner — async background task."""
from __future__ import annotations

import json
from datetime import datetime, UTC

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from rag_guardrails.core.logging import get_logger
from rag_guardrails.models.evaluation_run import EvaluationRun

logger = get_logger(__name__)


async def run_ragas_evaluation(
    run_id: str,
    questions: list[str],
    ground_truths: list[str],
    db: AsyncSession,
) -> None:
    """Run Ragas evaluation and store results."""
    await _set_status(run_id, "running", db)

    try:
        from ragas import evaluate, EvaluationDataset
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from ragas.llms import LangchainLLMWrapper
        from langchain_openai import ChatOpenAI
        from rag_guardrails.core.config import get_settings as _gs
        _s = _gs()
        _llm = LangchainLLMWrapper(ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=_s.openrouter_api_key,
            openai_api_base=_s.openrouter_base_url,
        ))
        for _m in (faithfulness, answer_relevancy, context_precision, context_recall):
            _m.llm = _llm

        # Generate answers and retrieve contexts for each question
        answers, contexts = await _generate_answers_and_contexts(questions)

        try:
            from ragas import SingleTurnSample
            samples = [
                SingleTurnSample(
                    user_input=q,
                    response=a,
                    retrieved_contexts=ctx,
                    reference=gt,
                )
                for q, a, ctx, gt in zip(questions, answers, contexts, ground_truths)
            ]
        except ImportError:
            from ragas.testset.graph import KnowledgeGraph
            samples = [
                {
                    "user_input": q,
                    "response": a,
                    "retrieved_contexts": ctx,
                    "reference": gt,
                }
                for q, a, ctx, gt in zip(questions, answers, contexts, ground_truths)
            ]

        dataset = EvaluationDataset(samples=samples)
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )

        def _to_float(val) -> float:
            """Handle scalar, list, and NaN results."""
            import math
            if isinstance(val, (list, tuple)):
                valid = [float(v) for v in val if v is not None and not math.isnan(float(v))]
                return round(sum(valid) / len(valid), 4) if valid else 0.0
            try:
                f = float(val)
                return round(f, 4) if not math.isnan(f) else 0.0
            except (TypeError, ValueError):
                return 0.0

        scores = {
            "faithfulness": _to_float(result["faithfulness"]),
            "answer_relevancy": _to_float(result["answer_relevancy"]),
            "context_precision": _to_float(result["context_precision"]),
            "context_recall": _to_float(result["context_recall"]),
        }

        await db.execute(
            update(EvaluationRun)
            .where(EvaluationRun.run_id == run_id)
            .values(
                status="complete",
                scores_json=json.dumps(scores),
                completed_at=datetime.now(UTC),
            )
        )
        await db.commit()
        logger.info("evaluation_complete", run_id=run_id, scores=scores)

    except Exception as exc:
        logger.error("evaluation_failed", run_id=run_id, error=str(exc))
        await db.execute(
            update(EvaluationRun)
            .where(EvaluationRun.run_id == run_id)
            .values(status="error", error_message=str(exc))
        )
        await db.commit()
        raise


async def _generate_answers_and_contexts(
    questions: list[str],
) -> tuple[list[str], list[list[str]]]:
    """Generate answers and retrieve contexts for each question using the live pipeline."""
    from rag_guardrails.retrieval.pipeline import retrieve_and_rerank
    from rag_guardrails.retrieval.llm_client import call_llm, make_client
    from rag_guardrails.core.config import get_settings

    settings = get_settings()
    client = make_client(settings.openrouter_api_key, settings.openrouter_base_url)
    answers, contexts = [], []

    for q in questions:
        chunks = await retrieve_and_rerank(q, top_k=5)
        ctx = [c["text"] for c in chunks]
        context_str = "\n\n".join(ctx) if ctx else "No context available."

        answer = await call_llm(
            client,
            model=settings.openrouter_model,
            messages=[{"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {q}"}],
            system="Answer strictly based on the provided context.",
        )
        answers.append(answer)
        contexts.append(ctx)

    return answers, contexts


async def _set_status(run_id: str, status: str, db: AsyncSession) -> None:
    await db.execute(
        update(EvaluationRun).where(EvaluationRun.run_id == run_id).values(status=status)
    )
    await db.commit()
