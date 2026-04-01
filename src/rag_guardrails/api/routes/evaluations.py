"""Async evaluation endpoints — POST returns run_id, poll for status/results."""
from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from rag_guardrails.api.dependencies import require_api_key
from rag_guardrails.core.database import get_db
from rag_guardrails.core.logging import get_logger
from rag_guardrails.models.evaluation_run import EvaluationRun

logger = get_logger(__name__)
router = APIRouter()


class EvalRequest(BaseModel):
    questions: list[str]
    ground_truths: list[str]
    model: str | None = None


@router.post("/evaluations", status_code=202)
async def start_evaluation(
    request: EvalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    if len(request.questions) != len(request.ground_truths):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "questions and ground_truths must have equal length",
        )

    run_id = str(uuid4())
    run = EvaluationRun(
        run_id=run_id,
        status="pending",
        config_json=json.dumps(request.model_dump()),
    )
    db.add(run)
    await db.commit()

    background_tasks.add_task(_run_evaluation, run_id, request)

    logger.info("evaluation_started", run_id=run_id, question_count=len(request.questions))
    return {"run_id": run_id, "status": "pending"}


@router.get("/evaluations/{run_id}")
async def get_evaluation_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    from sqlalchemy import select
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.run_id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Evaluation run '{run_id}' not found")
    return {"run_id": run_id, "status": run.status, "created_at": run.created_at.isoformat()}


@router.get("/evaluations/{run_id}/results")
async def get_evaluation_results(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    from sqlalchemy import select
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.run_id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Evaluation run '{run_id}' not found")
    if run.status != "complete":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Evaluation not complete yet. Current status: {run.status}",
        )
    return {"run_id": run_id, "scores": json.loads(run.scores_json), "status": "complete"}


async def _run_evaluation(run_id: str, request: EvalRequest) -> None:
    """Background task — runs Ragas evaluation and updates the DB record."""
    from rag_guardrails.evaluation.ragas_runner import run_ragas_evaluation
    from rag_guardrails.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await run_ragas_evaluation(run_id, request.questions, request.ground_truths, db)
