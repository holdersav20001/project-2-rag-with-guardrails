"""
Output guardrails — run on LLM answer before returning to client.
Tier 1: token overlap grounding check (fast).
Tier 2: NLI entailment check (cross-encoder/nli-deberta-v3-small).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import numpy as np
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import AnalyzerEngine

from rag_guardrails.core.logging import get_logger
from rag_guardrails.guardrails.input_guards import _PII_ENTITIES, _get_analyzer

logger = get_logger(__name__)

_anonymizer: AnonymizerEngine | None = None
_nli_model = None


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def _get_nli_model():
    global _nli_model
    if _nli_model is None:
        from sentence_transformers import CrossEncoder
        from rag_guardrails.core.config import get_settings
        _nli_model = CrossEncoder(get_settings().nli_model)
    return _nli_model


# ---------------------------------------------------------------------------
# GRD — Grounding / hallucination check
# ---------------------------------------------------------------------------

@dataclass
class GroundingResult:
    grounded: bool
    confidence: float
    method: str  # "token_overlap" | "nli" | "combined"


def _token_overlap_score(answer: str, sources: list[str]) -> float:
    """Jaccard-style token overlap between answer and combined source text."""
    if not sources:
        return 0.0
    combined = " ".join(sources).lower()
    answer_tokens = set(answer.lower().split())
    source_tokens = set(combined.split())
    if not answer_tokens:
        return 0.0
    intersection = answer_tokens & source_tokens
    return len(intersection) / len(answer_tokens)


async def check_grounding(answer: str, sources: list[str]) -> GroundingResult:
    """
    Two-tier grounding check.
    Tier 1: If token overlap >= 0.7, accept immediately (fast path).
    Tier 2: NLI entailment using cross-encoder/nli-deberta-v3-small.
    For structured queries with no document sources, grounding is not applicable.
    """
    if not sources:
        logger.info("grounding_check", method="no_sources", grounded=True)
        return GroundingResult(grounded=True, confidence=1.0, method="no_sources")

    overlap = _token_overlap_score(answer, sources)

    if overlap >= 0.7:
        logger.info("grounding_check", method="token_overlap", score=overlap, grounded=True)
        return GroundingResult(grounded=True, confidence=round(overlap, 3), method="token_overlap")

    # Tier 2: NLI entailment — check each chunk individually, take the best score.
    # Checking the full combined context dilutes specific facts and causes inconsistency.
    model = _get_nli_model()
    pairs = [(src[:1024], answer) for src in sources if src.strip()]

    if not pairs:
        return GroundingResult(grounded=False, confidence=0.0, method="nli_per_chunk")

    # Labels: contradiction=0, neutral=1, entailment=2
    all_scores = await asyncio.to_thread(
        model.predict,
        pairs,
        apply_softmax=True,
    )
    entailment_score = float(max(s[2] for s in all_scores))
    grounded = entailment_score >= 0.35
    confidence = round((overlap + entailment_score) / 2, 3)

    logger.info(
        "grounding_check",
        method="nli_per_chunk",
        entailment_score=entailment_score,
        overlap=overlap,
        grounded=grounded,
    )

    return GroundingResult(grounded=grounded, confidence=confidence, method="nli_per_chunk")


def compute_confidence_score(
    answer: str,
    sources: list[str],
    retrieval_scores: list[float],
) -> float:
    """
    Composite confidence score in [0, 1].
    Formula: 0.6 * mean_retrieval_score (sigmoid-normalised) + 0.4 * token_overlap_ratio
    """
    import math
    def sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    normalised = [sigmoid(s) for s in retrieval_scores] if retrieval_scores else [0.0]
    mean_retrieval = sum(normalised) / len(normalised)
    overlap = _token_overlap_score(answer, sources)
    score = 0.6 * mean_retrieval + 0.4 * overlap
    return round(min(max(score, 0.0), 1.0), 3)


# ---------------------------------------------------------------------------
# PII redaction in output
# ---------------------------------------------------------------------------

def redact_pii(text: str) -> str:
    """Replace PII entities in LLM output with [REDACTED:<TYPE>] placeholders."""
    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()

    analysis_results = analyzer.analyze(
        text=text,
        entities=_PII_ENTITIES,
        language="en",
        score_threshold=0.6,
    )

    if not analysis_results:
        return text

    from presidio_anonymizer.entities import OperatorConfig
    operators = {
        entity: OperatorConfig("replace", {"new_value": f"[REDACTED:{entity}]"})
        for entity in _PII_ENTITIES
    }

    result = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis_results,
        operators=operators,
    )
    return result.text
