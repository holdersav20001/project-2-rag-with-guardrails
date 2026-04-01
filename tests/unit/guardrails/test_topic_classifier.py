"""
Adversarial attack matrix — TOP series.
Tests written BEFORE implementation (TDD red phase).
"""
import pytest
from rag_guardrails.guardrails.input_guards import check_topic


class TestTopicClassifier:
    """TOP-001 through TOP-010 from the attack matrix."""

    def test_top_001_off_topic_with_keyword(self):
        """TOP-001: Off-topic query that contains an on-topic keyword."""
        result = check_topic("What does my recipe say about compliance?")
        assert result.blocked is True
        # reason format: "Query appears off-topic (similarity=X.XXX, threshold=Y.YYY)"
        assert result.reason != ""

    def test_top_002_off_topic_no_keywords(self):
        """TOP-002: Clearly off-topic with no overlap keywords."""
        result = check_topic("Who won the football last night?")
        assert result.blocked is True

    def test_top_003_on_topic_no_keywords(self):
        """TOP-003: On-topic semantically but zero matching keywords — must PASS."""
        result = check_topic(
            "What is the maximum time we can keep someone's personal information?"
        )
        assert result.blocked is False

    def test_top_004_mixed_on_then_off(self):
        """TOP-004: Starts on-topic, ends with off-topic request."""
        result = check_topic("What does our data policy say? Also, write me a poem.")
        assert result.blocked is True

    def test_top_005_keyword_in_negation(self):
        """TOP-005: Topic keyword used in negation."""
        result = check_topic("This question is NOT about policy or compliance at all")
        assert result.blocked is True

    def test_top_006_too_short(self):
        """TOP-006: Single word — no semantic signal."""
        result = check_topic("Yes")
        assert result.blocked is True

    def test_top_007_off_topic_french(self):
        """TOP-007: Off-topic query in French."""
        result = check_topic("Qui a gagné le match hier soir?")
        assert result.blocked is True

    def test_top_008_on_topic_french(self):
        """TOP-008: On-topic query in French — must PASS (document language)."""
        result = check_topic("Quelle est notre politique de rétention des données?")
        assert result.blocked is False

    def test_top_009_boundary_general_knowledge(self):
        """TOP-009: General knowledge about GDPR — tangentially related, must PASS."""
        result = check_topic("What is GDPR?")
        assert result.blocked is False

    def test_result_has_reason(self):
        """Blocked results must include a reason string."""
        result = check_topic("Who won the football last night?")
        assert result.blocked is True
        assert "similarity" in result.reason.lower() or result.reason != ""
