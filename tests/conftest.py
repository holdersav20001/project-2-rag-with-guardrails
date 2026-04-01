"""Root conftest — shared fixtures available to all test levels."""
import os
import pytest

# Set test environment before any app imports
os.environ.setdefault("API_KEY", "test-api-key-do-not-use-in-production")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-00000000000000000000000000000000")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://ragtest:ragtest@localhost:5433/rag_test")


@pytest.fixture(scope="session")
def test_api_key() -> str:
    return "test-api-key-do-not-use-in-production"


@pytest.fixture(scope="session")
def sample_policy_text() -> str:
    return (
        "Personal data must be retained for a maximum of 90 days after the purpose of "
        "collection has been fulfilled, in compliance with GDPR Article 5(1)(e). "
        "Organizations must notify the relevant supervisory authority within 72 hours "
        "of becoming aware of a personal data breach."
    )
