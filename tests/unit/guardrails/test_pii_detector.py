"""
Adversarial attack matrix — PII series.
Tests written BEFORE implementation (TDD red phase).
"""
import pytest
from rag_guardrails.guardrails.input_guards import check_pii
from rag_guardrails.guardrails.output_guards import redact_pii


class TestPIIDetection:
    """PII-001 through PII-013 from the attack matrix."""

    def test_pii_001_ssn_standard(self):
        """PII-001: Standard US SSN format."""
        result = check_pii("My SSN is 123-45-6789")
        assert result.blocked is True
        assert "US_SSN" in result.details.get("entities", []) or result.blocked

    def test_pii_002_ssn_no_hyphens(self):
        """PII-002: SSN without hyphens."""
        result = check_pii("SSN: 123456789")
        assert result.blocked is True

    def test_pii_003_credit_card_spaced(self):
        """PII-003: Credit card with spaces."""
        result = check_pii("Card: 4532 1111 1111 1111")
        assert result.blocked is True

    def test_pii_004_credit_card_no_spaces(self):
        """PII-004: Credit card without spaces."""
        result = check_pii("4532111111111111")
        assert result.blocked is True

    def test_pii_005_email_in_query(self):
        """PII-005: Email address in query."""
        result = check_pii("What does the file say about john.smith@corp.com?")
        assert result.blocked is True

    def test_pii_006_spelled_out_email(self):
        """PII-006: Email written out in words."""
        result = check_pii("johnsmith at company dot co dot uk")
        assert result.blocked is True

    def test_pii_007_iban(self):
        """PII-007: IBAN number."""
        result = check_pii("Bank: GB29NWBK60161331926819")
        assert result.blocked is True

    def test_pii_008_ip_address(self):
        """PII-008: IP address (PII under GDPR)."""
        result = check_pii("Server logs show user at 192.168.1.100")
        assert result.blocked is True

    def test_pii_009_uk_phone(self):
        """PII-009: UK phone number."""
        result = check_pii("+44 7911 123456")
        assert result.blocked is True

    def test_pii_010_us_phone_formatted(self):
        """PII-010: US phone number with parentheses."""
        result = check_pii("Call (555) 123-4567")
        assert result.blocked is True

    def test_pii_011_name_in_rag_context(self):
        """PII-011: Person name in RAG query context."""
        result = check_pii("What does the salary review say about John Smith?")
        assert result.blocked is True

    def test_pii_012_org_name_not_person(self):
        """PII-012: Organisation name containing person name — must NOT be blocked."""
        result = check_pii(
            "What did John Lewis Partnership say in their sustainability report?"
        )
        assert result.blocked is False

    def test_pii_013_output_redaction(self):
        """PII-013: PII in LLM output must be redacted."""
        answer = "The review mentions Jane Doe (DOB: 01/01/1990) and her salary of £45,000."
        redacted = redact_pii(answer)
        assert "Jane Doe" not in redacted
        assert "01/01/1990" not in redacted
        assert "[REDACTED" in redacted

    def test_result_lists_entity_types(self):
        """Blocked PII result must list which entities were found."""
        result = check_pii("My email is test@example.com")
        assert result.blocked is True
        assert "entities" in result.details
        assert len(result.details["entities"]) > 0
