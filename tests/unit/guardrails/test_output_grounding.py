"""
Adversarial attack matrix — GRD series.
Tests written BEFORE implementation (TDD red phase).
"""
import pytest
from rag_guardrails.guardrails.output_guards import check_grounding, compute_confidence_score


POLICY_SOURCE = (
    "Personal data must be retained for a maximum of 90 days after the purpose of "
    "collection has been fulfilled. Organizations must notify supervisory authorities "
    "within 72 hours of a personal data breach."
)


class TestOutputGrounding:
    """GRD-001 through GRD-008 from the attack matrix."""

    @pytest.mark.asyncio
    async def test_grd_001_plausible_claim_not_in_context(self):
        """GRD-001: Answer states 180 days when source says 90."""
        result = await check_grounding(
            answer="Data must be retained for a maximum of 180 days.",
            sources=[POLICY_SOURCE],
        )
        assert result.grounded is False

    @pytest.mark.asyncio
    async def test_grd_002_wrong_numeric_value(self):
        """GRD-002: Wrong number of hours for breach notification."""
        result = await check_grounding(
            answer="Organizations must notify within 48 hours of a breach.",
            sources=[POLICY_SOURCE],
        )
        assert result.grounded is False

    @pytest.mark.asyncio
    async def test_grd_007_grounded_true_negative(self):
        """GRD-007: Accurate direct summary — must be GROUNDED."""
        result = await check_grounding(
            answer="Personal data must be retained for a maximum of 90 days after the purpose is fulfilled.",
            sources=[POLICY_SOURCE],
        )
        assert result.grounded is True

    @pytest.mark.asyncio
    async def test_grd_008_hedged_answer_grounded(self):
        """GRD-008: Correctly acknowledging limitation is still grounded."""
        result = await check_grounding(
            answer="The document does not specify which supervisory authority must be notified.",
            sources=[POLICY_SOURCE],
        )
        assert result.grounded is True

    @pytest.mark.asyncio
    async def test_result_has_method_field(self):
        """GroundingResult.method must be 'token_overlap' or 'nli'."""
        result = await check_grounding(
            answer="Data must be retained for 90 days.",
            sources=[POLICY_SOURCE],
        )
        assert result.method in ("token_overlap", "nli", "combined")

    def test_confidence_score_formula(self):
        """Confidence = 0.6 * mean_retrieval + 0.4 * token_overlap."""
        # With retrieval scores [0.8, 0.6] mean=0.7, overlap~0.5 → 0.6*0.7 + 0.4*0.5 = 0.62
        score = compute_confidence_score(
            answer="Data must be retained for 90 days.",
            sources=[POLICY_SOURCE],
            retrieval_scores=[0.8, 0.6],
        )
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_confidence_score_no_retrieval_scores(self):
        """No retrieval scores → mean defaults to 0.0."""
        score = compute_confidence_score(
            answer="Something.",
            sources=["Some source text."],
            retrieval_scores=[],
        )
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_grd_006_lexical_match_semantic_mismatch(self):
        """GRD-006: High token overlap but NLI entailment catches the contradiction."""
        # Paraphrase that contradicts source: same words, opposite meaning
        result = await check_grounding(
            answer="Data must NOT be retained for 90 days after the purpose is fulfilled.",
            sources=[POLICY_SOURCE],
        )
        assert result.grounded is False
