# RAG System with Guardrails

## Overview

A Retrieval-Augmented Generation (RAG) system that answers questions by pulling relevant context from a knowledge base before generating a response. This project layers safety guardrails on top — validating inputs, checking outputs for hallucination, filtering toxic or off-topic content, and ensuring the LLM stays grounded in the retrieved documents.

## What It Does

- **Document Ingestion** — Upload PDFs, markdown, HTML, or plain text into a vector store
- **Chunking & Embedding** — Split documents into semantic chunks and generate vector embeddings
- **Semantic Search** — Retrieve the most relevant chunks for a given user query
- **Augmented Generation** — Pass retrieved context to the LLM to produce grounded answers
- **Citation Tracking** — Every answer includes references to the source documents and chunks used
- **Input Guardrails** — Block prompt injection attempts, detect PII in queries, reject off-topic requests
- **Output Guardrails** — Check for hallucination (claims not supported by retrieved context), toxicity, and PII leakage
- **Confidence Scoring** — Rate how confident the system is that the answer is grounded in the sources
- **Query Routing** — Classify incoming queries as semantic (vector search) or structured (SQL/filter) and route to the appropriate retrieval backend
- **Cross-Encoder Re-ranking** — After initial retrieval, re-score candidate chunks with a cross-encoder model to improve precision before passing to the LLM
- **RAG Evaluation** — Automated quality metrics via Ragas: faithfulness, answer relevancy, context precision, context recall — exposed via async run-based APIs (`POST /evaluations`, `GET /evaluations/{run_id}`, `GET /evaluations/{run_id}/results`) so long-running evaluations never block the request thread
- **Document Management** — List, inspect, and delete documents from the knowledge base (`GET /api/documents`, `DELETE /api/documents/{id}`) with full lifecycle tracking
- **Indirect Prompt Injection Defence** — Scan document content at ingestion time for embedded instructions that could hijack the LLM when retrieved as context (e.g. chunks containing "Ignore all previous instructions")
- **Conversation History** — Maintain per-session message history so follow-up questions are interpreted in context; `session_id` passed per request, last N turns included in the generation prompt
- **LLM Operational Controls** — Retry-with-exponential-backoff on transient Anthropic API errors, per-request timeout, rate-limit header parsing, and token-usage logging for cost visibility
- **Observability & Auditing** — Structured JSON logs for every guardrail decision, query, and LLM call; OpenTelemetry traces for end-to-end latency; token usage per request; compliance audit trail (who queried what, when, and what was returned)

## Why It Is Worth Developing

| Reason | Detail |
|--------|--------|
| **Most in-demand AI pattern** | RAG is the #1 architecture companies adopt before fine-tuning |
| **Safety is a differentiator** | Most RAG demos skip guardrails — adding them shows production-readiness |
| **Hallucination is the top concern** | Enterprises will not deploy LLMs without grounding and validation |
| **Covers multiple roles** | Touches AI architecture, safety engineering, data engineering, and prompt engineering |
| **Real-world applicability** | Customer support, internal knowledge bases, legal research, medical Q&A all use RAG |

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Embedding Model | OpenAI `text-embedding-3-small` or Sentence Transformers | Convert text to vectors |
| Re-ranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (sentence-transformers) | Re-score retrieved chunks for precision |
| Vector Database | ChromaDB, Pinecone, or pgvector (PostgreSQL) | Store and query embeddings |
| LLM | Claude (Anthropic) or GPT-4 | Generate answers from context |
| Framework | LangChain or LlamaIndex (or custom) | Orchestrate retrieval and generation |
| Query Router | LLM classifier (few-shot) | Route queries to vector vs SQL retrieval |
| Guardrails | Custom middleware + `presidio-analyzer` (PII) + NLI cross-encoder (grounding) | Input/output validation |
| RAG Evaluation | Ragas (async, run-based) | Faithfulness, answer relevancy, context precision/recall |
| Observability | structlog + OpenTelemetry + Prometheus | Latency, token usage, guardrail decisions, audit trail |
| LLM Resilience | `tenacity` retry library | Exponential backoff, timeout, rate-limit handling |
| Backend | FastAPI (Python) | API server |
| Frontend | Streamlit or React | Chat interface with citations |
| Document Processing | Unstructured, PyMuPDF, BeautifulSoup | Parse various document formats |
| Database | PostgreSQL | Store documents, metadata, audit logs |
| Containerisation | Docker + Docker Compose | Reproducible environment |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 DOCUMENT INGESTION                           │ │
│  │                                                              │ │
│  │  PDF ─┐                                                      │ │
│  │  MD  ─┤──▶ Parser ──▶ Chunker ──▶ Embedder ──┐              │ │
│  │  HTML ─┘                                      │              │ │
│  │                                               ▼              │ │
│  │                                     ┌──────────────┐         │ │
│  │                                     │   Vector DB  │         │ │
│  │                                     │  (ChromaDB / │         │ │
│  │                                     │   pgvector)  │         │ │
│  │                                     └──────┬───────┘         │ │
│  │                                            │                 │ │
│  │  Structured data ──▶ PostgreSQL ───────────┤                 │ │
│  │  (tables, metadata)                        │                 │ │
│  └────────────────────────────────────────────┼─────────────────┘ │
│                                               │                   │
│  ┌────────────────────────────────────────────┼─────────────────┐ │
│  │                 QUERY PIPELINE              │                 │ │
│  │                                             │                 │ │
│  │  User Query                                 │                 │ │
│  │      │                                      │                 │ │
│  │      ▼                                      │                 │ │
│  │  ┌──────────────────────┐                   │                 │ │
│  │  │   INPUT GUARDRAILS   │                   │                 │ │
│  │  │                      │                   │                 │ │
│  │  │  • Prompt injection  │                   │                 │ │
│  │  │    detection         │                   │                 │ │
│  │  │  • PII scanner       │                   │                 │ │
│  │  │  • Topic classifier  │                   │                 │ │
│  │  │  • Query rewriter    │                   │                 │ │
│  │  └──────────┬───────────┘                   │                 │ │
│  │             │                               │                 │ │
│  │             ▼                               │                 │ │
│  │  ┌──────────────────────┐                   │                 │ │
│  │  │    QUERY ROUTER      │                   │                 │ │
│  │  │                      │                   │                 │ │
│  │  │  LLM classifies:     │                   │                 │ │
│  │  │  • "semantic" ──────────▶ Vector search ◀┘                 │ │
│  │  │  • "structured" ───────▶ SQL query (PostgreSQL)            │ │
│  │  │  • "hybrid" ───────────▶ Both, merge results               │ │
│  │  └──────────┬───────────┘                                     │ │
│  │             │                                                 │ │
│  │             ▼                                                 │ │
│  │  ┌──────────────────────┐                                     │ │
│  │  │  CROSS-ENCODER       │                                     │ │
│  │  │  RE-RANKER            │                                     │ │
│  │  │                      │                                     │ │
│  │  │  Initial top-20 ──▶  │                                     │ │
│  │  │  Re-score with       │                                     │ │
│  │  │  cross-encoder ──▶   │                                     │ │
│  │  │  Select top-5        │                                     │ │
│  │  └──────────┬───────────┘                                     │ │
│  │             │                                                 │ │
│  │             ▼                                                 │ │
│  │  ┌──────────────────────┐                                     │ │
│  │  │   LLM GENERATION    │                                     │ │
│  │  │                      │                                     │ │
│  │  │  System prompt +     │                                     │ │
│  │  │  Retrieved context + │                                     │ │
│  │  │  User query          │                                     │ │
│  │  │       │              │                                     │ │
│  │  │       ▼              │                                     │ │
│  │  │  Claude / GPT-4      │                                     │ │
│  │  └──────────┬───────────┘                                     │ │
│  │             │                                                 │ │
│  │             ▼                                                 │ │
│  │  ┌──────────────────────┐                                     │ │
│  │  │  OUTPUT GUARDRAILS   │                                     │ │
│  │  │                      │                                     │ │
│  │  │  • Hallucination     │                                     │ │
│  │  │    check (grounded?) │                                     │ │
│  │  │  • Toxicity filter   │                                     │ │
│  │  │  • PII redaction     │                                     │ │
│  │  │  • Confidence score  │                                     │ │
│  │  │  • Citation verify   │                                     │ │
│  │  └──────────┬───────────┘                                     │ │
│  │             │                                                 │ │
│  │             ▼                                                 │ │
│  │  ┌──────────────────────┐                                     │ │
│  │  │     RESPONSE         │                                     │ │
│  │  │  Answer + Citations  │                                     │ │
│  │  │  + Confidence Score  │                                     │ │
│  │  └──────────────────────┘                                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                 RAG EVALUATION (Ragas)                         │ │
│  │                                                               │ │
│  │  POST /api/evaluations                  — enqueue run, returns {"run_id": "uuid"}  │ │
│  │  GET  /api/evaluations/{run_id}         — status: queued/running/complete/error   │ │
│  │  GET  /api/evaluations/{run_id}/results — scores + per-question breakdown         │ │
│  │                                                               │ │
│  │  Async: runs via FastAPI BackgroundTasks.                     │ │
│  │  20-question eval takes 3–5 min — never blocks HTTP thread.  │ │
│  │                                                               │ │
│  │  Metrics:                                                     │ │
│  │  • Faithfulness — are claims supported by retrieved context?  │ │
│  │  • Answer Relevancy — does the answer address the question?   │ │
│  │  • Context Precision — are the retrieved chunks relevant?     │ │
│  │  • Context Recall — did we retrieve all needed information?   │ │
│  │                                                               │ │
│  │  Output: JSON scores + per-question breakdown by run id       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Guardrail Detail

```
                    DOCUMENT INGESTION (guardrail at write time)
                    ┌─────────────────────────────┐
                    │                             │
  Uploaded file ───▶│  Indirect Injection Scan    │
                    │  Detect embedded LLM        │
                    │  instructions in content    │
                    │  (e.g. "Ignore all rules")  │
                    │  Flag or quarantine chunk   │
                    │                             │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │  Parse → Chunk → Embed       │
                    │  → pgvector store            │
                    └──────────────────────────────┘

                    INPUT GUARDRAILS (query time)
                    ┌─────────────────────────────┐
                    │                             │
  User Query ──────▶│  1. Prompt Injection Check  │
                    │     Regex + semantic embed  │
                    │     similarity to attack    │
                    │     cluster (no LLM call)   │
                    │     ↓ pass                  │
                    │  2. PII Detection           │
                    │     presidio-analyzer       │
                    │     (40+ entity types)      │
                    │     ↓ pass                  │
                    │  3. Topic Classification    │
                    │     Embedding similarity    │
                    │     to on-topic centroid    │
                    │     ↓ on-topic              │
                    │  4. Query Normalisation     │
                    │                             │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │  RETRIEVAL + LLM             │
                    │  (with session history)      │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │    OUTPUT GUARDRAILS         │
                    │                             │
                    │  1. Grounding Check         │
                    │     Tier 1: token overlap   │
                    │     Tier 2: NLI entailment  │
                    │     (cross-encoder/nli-     │
                    │      deberta-v3-small)      │
                    │     ↓ pass                  │
                    │  2. Toxicity Filter         │
                    │     ↓ pass                  │
                    │  3. PII Redaction           │
                    │     presidio-anonymizer     │
                    │     ↓ clean                 │
                    │  4. Confidence Score        │
                    │     f(retrieval_scores,     │
                    │       NLI entailment score) │
                    │     (0.0 → 1.0)             │
                    │                             │
                    └──────────┬──────────────────┘
                               │
                               ▼
                    Validated Response + Citations
```

## Query Router Detail

```
                    QUERY ROUTER (LLM few-shot classifier)

  "What documents mention GDPR?"
      → semantic (concept search → vector DB)

  "How many documents were uploaded in March?"
      → structured (count query → SQL)

  "What does our GDPR policy say about data retention timelines?"
      → hybrid (vector for policy content + SQL for metadata filter)

  The router is a lightweight LLM call with 3-5 few-shot examples
  per category. Adds ~200ms latency but dramatically improves
  retrieval relevance for mixed workloads.
```

## Re-ranking Detail

```
  WITHOUT RE-RANKING:              WITH CROSS-ENCODER RE-RANKING:

  Query → Embed → Cosine sim      Query → Embed → Cosine sim
  → Top-5 chunks → LLM            → Top-20 candidates
                                   → Cross-encoder scores each
                                     (query, chunk) pair
                                   → Top-5 by cross-encoder → LLM

  Bi-encoder (embedding) is        Cross-encoder is slower but
  fast but shallow — compares       deeper — reads query and chunk
  vectors, not meaning.             together, understands nuance.

  Model: cross-encoder/ms-marco-MiniLM-L-6-v2
  Latency: ~50ms for 20 candidates
  Impact: typically +10-15% retrieval precision
```

## API Surface

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Deep health check (DB connectivity) |
| POST | `/api/documents/upload` | Upload and ingest a document |
| GET | `/api/documents` | List all documents with metadata |
| DELETE | `/api/documents/{id}` | Remove document and its embeddings |
| POST | `/api/query` | Ask a question, get grounded answer |
| POST | `/api/evaluations` | Enqueue async Ragas evaluation run |
| GET | `/api/evaluations/{run_id}` | Poll evaluation run status |
| GET | `/api/evaluations/{run_id}/results` | Fetch evaluation scores |

All endpoints except `/api/health` require `X-API-Key` header. Upload validates file size (≤50MB), MIME type, and sanitises filename.

---

## Production Readiness Requirements

### LLM Operational Controls
- **Retry with exponential backoff** — `tenacity` wraps every Anthropic API call; retries on `RateLimitError`, `APIConnectionError`, `InternalServerError` with jitter, max 3 attempts
- **Per-request timeout** — 30s hard timeout on LLM calls; returns structured error if exceeded
- **Token usage logging** — `input_tokens` and `output_tokens` logged per request for cost visibility
- **Cost budget alert** — configurable `MAX_TOKENS_PER_DAY`; warning logged when 80% consumed

### Vector DB Operational Controls
- **Query timeout** — pgvector search wrapped with `asyncio.wait_for(timeout=5.0)`; returns empty results with a logged warning rather than hanging
- **Ingestion back-pressure** — concurrent ingestion requests capped via `asyncio.Semaphore(max_concurrent_ingestions)` to prevent vector DB queue growth during traffic spikes
- **Connection pool** — SQLAlchemy `pool_size` and `max_overflow` configured; pool exhaustion returns 503 rather than blocking indefinitely

### Observability & Auditing
- **Structured JSON logging** — every guardrail decision, query, LLM call, and ingestion event logged with `timestamp`, `session_id`, `event_type`, `duration_ms`, `tokens_used`
- **OpenTelemetry traces** — spans for ingestion pipeline, retrieval, re-ranking, guardrail checks, and LLM generation; exportable to Jaeger or OTLP collector
- **Compliance audit trail** — PostgreSQL `audit_log` table records: who queried (API key hash), what (query text hash), when, confidence score, blocked status; retained per configurable policy
- **Health metrics endpoint** — `GET /api/metrics` exposes Prometheus-format counters: `rag_requests_total`, `rag_blocked_total`, `rag_latency_seconds`, `rag_tokens_used_total`

### Guardrail Bypass Defences
- **Indirect prompt injection at ingestion** — document chunks scanned for embedded LLM instructions before storage; flagged chunks quarantined and operator-notified
- **Pipeline-level defence** — system prompt explicitly instructs the LLM to ignore any retrieved content that contradicts its operating instructions
- **Adversarial test coverage** — evaluation dataset includes Unicode homoglyph attacks, encoding-based bypasses, and multi-turn injection attempts

---

## Development Methodology

All implementation follows a disciplined engineering process — not just "write code and test it later."

### Test-Driven Development
Every feature begins with a failing test. No implementation code exists without a test justifying it. Coverage targets: **85% overall**, **95% on all guardrail modules**. Tests are the specification.

### E2E Testing as Part of Development
End-to-end tests are written alongside feature work at each phase boundary — not retrofitted. They run against a live Docker Compose stack with real PostgreSQL + pgvector and seeded fixture documents. Every guardrail has an E2E scenario. E2E is the final stage in CI.

### Pair Programming
All implementation is done in pairs. Both developers must independently agree the code is correct and complete before it is committed. Either developer can block a commit. Disagreements escalate to the Architect.

### Adversarial QA Engineer
A dedicated team member whose sole role is to **break** the system — attempting prompt injection bypasses, PII leakage, topic classifier evasion, grounding check circumvention, upload boundary violations, and auth bypass. Every guardrail task is gated on adversarial QA sign-off. Failed attack attempts become regression tests.

### Software Architect
Present throughout all phases — not only at design time. Enforces architectural decisions, reviews all new files at creation, and signs off on each phase boundary before the next begins. Tiebreaker when the pair disagrees.

### Security Engineer
Reviews code (not runtime) for OWASP Top 10 issues, audits file upload handling, input validation, auth implementation, and secret management. Runs `bandit` static analysis. Signs off on all security-sensitive tasks.

### Performance Benchmarker
Validates latency and throughput on async paths — LLM retry under rate limits, vector DB query timeouts under concurrent load, re-ranker latency (target: <120ms p95). Required sign-off on all async and LLM-interaction tasks.

### Definition of Done
A task is complete only when: tests pass at coverage target, both pair developers agree, Architect approves structure, relevant specialists (QA / Security / Perf) have signed off, automated code review findings are addressed, and an E2E test covers the new behaviour.

---

## Key Learning Outcomes

- Vector embedding and similarity search
- Document parsing and chunking strategies
- Prompt engineering for grounded generation
- Two-tier hallucination detection (token overlap + NLI entailment)
- Multi-layer input/output validation with real classifiers
- Indirect prompt injection defence at ingestion and generation
- Query routing — classifying and directing queries to the right retrieval backend
- Cross-encoder re-ranking — improving precision beyond bi-encoder similarity
- RAG evaluation with Ragas — async run-based, curated golden datasets
- LLM operational controls — retry, timeout, cost budgeting
- Production observability — structured logging, OpenTelemetry, audit trails
- Building genuinely production-safe AI applications
