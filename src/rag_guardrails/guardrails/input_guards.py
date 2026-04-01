"""
Input guardrails — run before any retrieval or LLM call.
Pipeline: injection check → topic check → PII check.
All decisions are logged to the audit_log table.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
from presidio_analyzer import AnalyzerEngine

from rag_guardrails.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared result type
# ---------------------------------------------------------------------------

@dataclass
class GuardrailResult:
    blocked: bool
    reason: str
    guardrail: str
    details: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# INJ — Prompt injection detection
# ---------------------------------------------------------------------------

# Normalise then match — covers Unicode homoglyphs (Cyrillic etc.)
_INJECTION_PATTERNS: list[re.Pattern] = [
    # Standard patterns (run on whitespace-normalised text)
    re.compile(r"ignor[e\W]+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"disregard\s+(your\s+)?(former|previous|all)\s+(directives|instructions|rules)", re.I),
    re.compile(r"you\s+are\s+now\s+(dan|jailbreak|unrestricted|unfiltered)", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)\s+an?\s+ai\s+with\s+no\s+restrictions", re.I),
    re.compile(r"(reveal|output|print|show|display)\s+(the\s+)?(system\s+prompt|prompt|instructions)", re.I),
    re.compile(r"SW5nb3JlIGFsbA", re.I),  # base64 "Ignore all"
    re.compile(r"act\s+without\s+restriction", re.I),
    re.compile(r"no\s+content\s+restrictions", re.I),
    re.compile(r"hypothetically.{0,40}no\s+restrictions", re.I),
    # Multilingual overrides
    re.compile(r"ignorez\s+toutes\s+les\s+instructions", re.I),   # French
    re.compile(r"ignora\s+todas\s+las\s+instrucciones", re.I),     # Spanish
    # Fragmentation attacks: "I g n o r e  a l l  p r e v i o u s  i n s t r u c t i o n s"
    # Uses \s* between chars so it catches both spaced and zero-width variants
    # without collapsing real word boundaries in _normalise().
    re.compile(
        r"i\s*g\s*n\s*o\s*r\s*e\s+a\s*l\s*l\s+p\s*r\s*e\s*v\s*i\s*o\s*u\s*s\s+i\s*n\s*s\s*t\s*r\s*u\s*c\s*t\s*i\s*o\s*n\s*s",
        re.I,
    ),
    re.compile(
        r"d\s*i\s*s\s*r\s*e\s*g\s*a\s*r\s*d\s+.{0,30}\s*i\s*n\s*s\s*t\s*r\s*u\s*c\s*t\s*i\s*o\s*n\s*s",
        re.I,
    ),
]


def _normalise(text: str) -> str:
    """Collapse Unicode to ASCII equivalents and strip zero-width chars."""
    # Remove zero-width chars
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    # Normalise to NFKD to strip homoglyphs (Cyrillic lookalikes → ASCII)
    text = unicodedata.normalize("NFKD", text)
    # Collapse excess whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # NOTE: do NOT collapse all \w-spaces — that turns "Ignore all" → "Ignoreall"
    # and defeats the patterns above. Fragmentation is handled by \s* in the patterns.
    return text


def check_injection(query: str) -> GuardrailResult:
    """Check for prompt injection attempts. Returns GuardrailResult."""
    normalised = _normalise(query)

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(normalised):
            logger.info(
                "guardrail_decision",
                guardrail="injection_detector",
                action="blocked",
                reason=f"pattern_match: {pattern.pattern[:40]}",
                query_hash=hashlib.sha256(query.encode()).hexdigest()[:8],
            )
            return GuardrailResult(
                blocked=True,
                reason=f"Prompt injection detected: {pattern.pattern[:40]}",
                guardrail="injection_detector",
                details={"pattern": pattern.pattern},
            )

    return GuardrailResult(blocked=False, reason="", guardrail="injection_detector")


# ---------------------------------------------------------------------------
# TOP — Topic classifier (embedding cosine similarity)
# ---------------------------------------------------------------------------

# On-topic example queries used to compute the centroid embedding.
# These represent the domain: enterprise document Q&A (policy, compliance, GDPR).
_ON_TOPIC_EXAMPLES = [
    # Policy / compliance framing
    "What does our data retention policy say?",
    "How long must we keep personal data under GDPR?",
    "What are our compliance obligations?",
    "Explain our data breach notification procedure.",
    "What is the GDPR data subject access request process?",
    "What security training is required for employees?",
    "What does the policy say about third-party data processors?",
    "Describe our data protection principles.",
    "What personal data do we collect and why?",
    "How should we handle a subject access request?",
    "What is our lawful basis for processing personal data?",
    "What are the rules around data minimisation?",
    "Quelle est notre politique de rétention des données?",  # French on-topic
    "What is GDPR?",
    "What is the maximum retention period for customer records?",
    # Knowledge base / document metadata queries
    "How many documents have been uploaded?",
    "What files are in the knowledge base?",
    "List all the documents available in the system.",
    "When was this document uploaded?",
    "What is the total size of all uploaded documents?",
    # Organisation rights and obligations (practical Q&A angle)
    "Can an organisation charge a fee for a subject access request?",
    "Can an organisation refuse a subject access request?",
    "When can a controller extend the time limit for responding to a SAR?",
    "What exemptions allow withholding information from a data subject?",
    "How long does an organisation have to respond to a subject access request?",
    "What happens if an organisation misses the SAR deadline?",
    "Can a company refuse to act on a request that is manifestly unfounded?",
    "What are the grounds for refusing to comply with an erasure request?",
    "Are there any fees allowed under GDPR for access requests?",
    "What is the right to erasure and when does it apply?",
    "What counts as a valid identity verification for a subject access request?",
    "Does GDPR apply to paper records as well as digital data?",
]

_topic_centroid: np.ndarray | None = None

# Structural/metadata patterns that are always on-topic for a RAG knowledge base.
# These bypass embedding-based topic classification.
_METADATA_PATTERNS = re.compile(
    r"\b(how many|count|total|list|show me|what documents|which files?|"
    r"when was|uploaded|available documents?|all documents?|all files?)\b",
    re.IGNORECASE,
)


def _get_topic_centroid() -> np.ndarray:
    global _topic_centroid
    if _topic_centroid is None:
        from rag_guardrails.retrieval.embeddings import get_embed_model
        model = get_embed_model()
        embeddings = np.array([
            model.get_text_embedding(ex) for ex in _ON_TOPIC_EXAMPLES
        ])
        centroid = embeddings.mean(axis=0)
        norm = np.linalg.norm(centroid)
        _topic_centroid = centroid / norm if norm > 0 else centroid
    return _topic_centroid


def check_topic(query: str, threshold: float | None = None) -> GuardrailResult:
    """Check if query is on-topic via cosine similarity to centroid."""
    from rag_guardrails.core.config import get_settings
    from rag_guardrails.retrieval.embeddings import get_embed_model

    if threshold is None:
        threshold = get_settings().topic_similarity_threshold

    if len(query.strip()) < 3:
        return GuardrailResult(
            blocked=True,
            reason="Query too short to classify",
            guardrail="topic_classifier",
            details={"similarity": 0.0},
        )

    # Structural/metadata queries are always on-topic for a knowledge base
    if _METADATA_PATTERNS.search(query):
        return GuardrailResult(blocked=False, reason="", guardrail="topic_classifier", details={"similarity": 1.0})

    model = get_embed_model()
    q_emb = np.array(model.get_text_embedding(query))
    norm = np.linalg.norm(q_emb)
    if norm > 0:
        q_emb = q_emb / norm

    centroid = _get_topic_centroid()
    similarity = float(np.dot(q_emb, centroid))

    logger.info(
        "guardrail_decision",
        guardrail="topic_classifier",
        action="blocked" if similarity < threshold else "allowed",
        reason=f"similarity={similarity:.3f}, threshold={threshold}",
        query_hash=hashlib.sha256(query.encode()).hexdigest()[:8],
    )

    if similarity < threshold:
        return GuardrailResult(
            blocked=True,
            reason=f"Query appears off-topic (similarity={similarity:.3f}, threshold={threshold})",
            guardrail="topic_classifier",
            details={"similarity": similarity, "threshold": threshold},
        )

    return GuardrailResult(
        blocked=False,
        reason="",
        guardrail="topic_classifier",
        details={"similarity": similarity},
    )


# ---------------------------------------------------------------------------
# PII — Detection via presidio-analyzer
# ---------------------------------------------------------------------------

_PII_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "US_SSN",
    "IBAN_CODE",
    "IP_ADDRESS",
    "US_PASSPORT",
    "US_BANK_NUMBER",
]

_analyzer: AnalyzerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
    return _analyzer


def check_pii(query: str) -> GuardrailResult:
    """Detect PII in a query using presidio-analyzer."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(
        text=query,
        entities=_PII_ENTITIES,
        language="en",
        score_threshold=0.6,
    )

    # Filter PERSON at higher threshold to avoid org-name false positives
    filtered = [
        r for r in results
        if not (r.entity_type == "PERSON" and r.score < 0.75)
    ]

    if filtered:
        entity_types = list({r.entity_type for r in filtered})
        logger.info(
            "guardrail_decision",
            guardrail="pii_detector",
            action="blocked",
            reason=f"PII detected: {entity_types}",
            query_hash=hashlib.sha256(query.encode()).hexdigest()[:8],
        )
        return GuardrailResult(
            blocked=True,
            reason=f"PII detected in query: {entity_types}",
            guardrail="pii_detector",
            details={"entities": entity_types},
        )

    return GuardrailResult(blocked=False, reason="", guardrail="pii_detector")


# ---------------------------------------------------------------------------
# Pipeline — run all input guards in sequence
# ---------------------------------------------------------------------------

def run_input_guards(query: str) -> GuardrailResult:
    """Run injection → topic → PII checks. Returns first block or final allow."""
    for check in (check_injection, check_topic, check_pii):
        result = check(query)
        if result.blocked:
            return result
    return GuardrailResult(blocked=False, reason="", guardrail="all_passed")
