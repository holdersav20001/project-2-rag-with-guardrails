# Project 2 — RAG with Guardrails

A production-grade Retrieval-Augmented Generation (RAG) system for GDPR and compliance document Q&A, with a multi-layer guardrail pipeline that fires on both sides of the LLM. Built as a portfolio project to demonstrate that adding AI to a regulated domain is not just a matter of calling an LLM — it requires defence-in-depth.

---

## What it does

Users upload compliance documents (PDF, TXT, MD). They can then ask questions about them in natural language. Every query passes through three input guardrails before retrieval, and two output guardrails before the answer is returned. Off-topic questions, prompt injection attempts, and PII-containing queries are blocked before the LLM is ever called.

---

## Architecture Overview

```mermaid
graph TB
    subgraph Frontend["Frontend (React/Vite · port 3000)"]
        UI["Document Manager + Chat UI"]
    end

    subgraph API["FastAPI (port 8000)"]
        AUTH["API Key Auth"]
        DOCS["GET /api/documents"]
        QUERY["POST /api/query"]
        EVAL["POST /api/evaluations"]
    end

    subgraph Guardrails_In["Input Guardrails"]
        INJ["Injection Detector<br/>(regex)"]
        TOPIC["Topic Classifier<br/>(embedding)"]
        PII_IN["PII Detector<br/>(Presidio)"]
    end

    subgraph Retrieval["Retrieval"]
        ROUTER["Query Router<br/>(semantic/structured/hybrid)"]
        EMBED["Embed Query<br/>(sentence-transformers)"]
        VEC["pgvector Search<br/>(top 10)"]
        RERANK["Cross-Encoder<br/>(top 5)"]
        SQL["SQL Handler<br/>(NL → SQL)"]
    end

    subgraph LLM["LLM Generation"]
        HIST["Load Session History"]
        GEN["OpenRouter API<br/>(with retry)"]
    end

    subgraph Guardrails_Out["Output Guardrails"]
        GROUND["Grounding Check<br/>(token overlap + NLI)"]
        PII_OUT["PII Redaction<br/>(Presidio)"]
        CONF["Confidence Score"]
    end

    subgraph Storage["PostgreSQL + pgvector"]
        CHUNKS["(document_chunks)"]
        SESSION["(session_history)"]
        AUDIT["(audit_log)"]
    end

    UI -->|REST| AUTH
    AUTH --> DOCS
    AUTH --> QUERY
    AUTH --> EVAL
    QUERY --> INJ
    INJ -->|blocked| UI
    INJ -->|pass| TOPIC
    TOPIC -->|blocked| UI
    TOPIC -->|pass| PII_IN
    PII_IN -->|blocked| UI
    PII_IN -->|pass| ROUTER
    ROUTER -->|semantic| EMBED
    ROUTER -->|structured| SQL
    EMBED --> VEC
    VEC --> RERANK
    RERANK --> HIST
    SQL --> HIST
    HIST --> GEN
    GEN --> GROUND
    GROUND --> PII_OUT
    PII_OUT --> CONF
    CONF --> UI
    CHUNKS <-->|search| VEC
    SESSION <-->|history| HIST
    INJ -->|log| AUDIT
    TOPIC -->|log| AUDIT
    PII_IN -->|log| AUDIT
    DOCS -->|ingest| CHUNKS
```

---

## Ingestion Pipeline

When a document is uploaded it is processed once and never re-processed:

```mermaid
flowchart LR
    UP[Upload\nPDF / TXT / MD]
    PARSE[Parse\nPyMuPDF · UTF-8]
    CHUNK[Chunk\nLlamaIndex SentenceSplitter\n512 tokens · 50 overlap]
    DEDUP{Content hash\nalready exists?}
    SCAN[Scan chunk for\nindirect injection]
    EMBED_C[Embed chunk\nsentence-transformers\nall-MiniLM-L6-v2]
    STORE[(PostgreSQL\ndocument_chunks)]

    UP --> PARSE --> CHUNK --> DEDUP
    DEDUP -->|yes| SKIP[Return already_exists]
    DEDUP -->|no| SCAN
    SCAN -->|clean| EMBED_C --> STORE
    SCAN -->|injection detected| DROP[Drop chunk]
```

**Why pre-compute embeddings?** Embeddings are ~5ms per chunk with the model warm. A 50-page PDF produces ~200 chunks. Computing them at query time (on every request) would add a second of latency per document — instead it's a one-time cost at upload.

---

## Query Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant G as Input Guardrails
    participant R as Retrieval
    participant DB as PostgreSQL
    participant LLM as OpenRouter
    participant O as Output Guardrails

    U->>API: POST /api/query {query, session_id}
    API->>G: Injection check
    alt injection detected
        G-->>U: {blocked: true, guardrail: "injection_detector"}
    end
    API->>G: Topic check (embedding similarity)
    alt off-topic
        G-->>U: {blocked: true, guardrail: "topic_classifier"}
    end
    API->>G: PII check (Presidio NER)
    alt PII found
        G-->>U: {blocked: true, guardrail: "pii_detector"}
    end
    API->>R: Route query (semantic / structured / hybrid)
    alt structured (metadata question)
        R->>DB: Generated SQL query
        DB-->>R: Result rows
    else semantic / hybrid
        R->>DB: pgvector cosine search (top 10)
        DB-->>R: Candidate chunks
        R->>R: Cross-encoder re-rank (top 5)
    end
    API->>DB: Load session history (last 10 turns)
    DB-->>API: Prior messages
    API->>LLM: {system, history, context chunks, query}
    LLM-->>API: Generated answer
    API->>O: Token overlap grounding check
    alt overlap < 0.7
        O->>O: NLI DeBERTa entailment check
    end
    API->>O: Presidio PII redaction on answer
    API->>O: Compute confidence score
    API->>DB: Save session turn
    API-->>U: {answer, sources, confidence, grounded, session_id}
```

---

## Input Guardrails — Why Three Different Techniques

Each guardrail solves a fundamentally different problem:

| Guardrail | Problem | Right tool | Wrong tool |
|---|---|---|---|
| Injection | Does text contain a specific attack *pattern*? | Regex on normalised input | Embeddings — semantic similarity misses structural obfuscation |
| Topic | Is the *meaning* in the right domain? | Embedding cosine vs centroid | Regex — "data" appears in football transfer news |
| PII | Are there real *named entities* in the text? | NER model (Presidio) | Either — needs span-level entity recognition |

### Injection Detector

```mermaid
flowchart TD
    RAW[Raw query text]
    NORM["Normalise:\n• Unicode homoglyphs → ASCII\n• Zero-width chars stripped\n• Fragmentation spaces handled"]
    PATTERNS{Match regex\npatterns?}
    PASS[Pass to topic check]
    BLOCK[Block — injection_detector]

    RAW --> NORM --> PATTERNS
    PATTERNS -->|no match| PASS
    PATTERNS -->|match| BLOCK
```

Fragmentation attacks (`I g n o r e  a l l`) are caught by patterns with `\s*` between characters. Unicode homoglyphs (Cyrillic о vs Latin o) are normalised before matching.

### Topic Classifier

```mermaid
flowchart TD
    QUERY[Query]
    EMBED_Q[Embed query\nall-MiniLM-L6-v2]
    CENTROID[Compare to centroid\nof 32 on-topic GDPR examples]
    META{Matches metadata\npattern?}
    THRESH{cosine similarity\n≥ threshold?}
    PASS[Pass to PII check]
    BLOCK[Block — topic_classifier]

    QUERY --> META
    META -->|yes: 'how many docs...'| PASS
    META -->|no| EMBED_Q --> CENTROID --> THRESH
    THRESH -->|yes| PASS
    THRESH -->|no| BLOCK
```

The centroid is the average vector of 32 example sentences covering all aspects of GDPR: data subject rights, controller obligations, SAR deadlines, breach notification, etc. Any query that lands in that embedding neighbourhood passes.

### PII Detector

Uses Microsoft Presidio (MIT licence) with 40+ entity types: names, emails, phone numbers, SSNs, IBANs, passport numbers, IP addresses. The same engine is reused at the output stage to redact PII that the LLM might echo from source documents.

---

## Output Guardrails — Two-Tier Grounding

```mermaid
flowchart TD
    ANSWER[LLM answer]
    SOURCES[Retrieved source chunks]
    T1{Token overlap\n≥ 0.7?}
    T2{NLI entailment\ncheck — DeBERTa}
    REDACT[Presidio PII redaction]
    SCORE[Compute confidence score]
    RETURN[Return to user]

    ANSWER --> T1
    SOURCES --> T1
    T1 -->|yes — fast pass| REDACT
    T1 -->|no — escalate| T2
    T2 -->|entailed| REDACT
    T2 -->|contradiction| RETURN_UG[Return grounded=false]
    REDACT --> SCORE --> RETURN
```

**Why two tiers?** Token overlap is near-instant but misses logical contradictions:

```
source: "data must not be retained beyond its purpose"
answer: "data can be kept indefinitely"

token overlap: "data", "be", "kept" all appear → would pass (wrong)
NLI (DeBERTa): reads both texts, detects contradiction → correct
```

Running NLI on every response would add ~200ms. Running it only when token overlap fails keeps the average latency low while catching hallucinations the fast check misses.

**Confidence score** is a weighted combination of values already in the pipeline:

```
confidence = 0.6 × sigmoid(mean retrieval score)
           + 0.4 × token overlap ratio
```

No extra computation. The retrieval scores come from pgvector; the overlap ratio from the grounding check that already ran.

---

## Query Routing — Semantic vs Structured

A few-shot LLM classifier decides how to handle each query before retrieval:

```mermaid
flowchart LR
    Q[Query]
    ROUTER{LLM few-shot\nclassifier}
    SEM[Semantic\nvector search + re-rank]
    STR[Structured\nnatural language → SQL → DB]
    HYB[Hybrid\nboth paths merged]

    Q --> ROUTER
    ROUTER -->|e.g. 'What are SAR deadlines?'| SEM
    ROUTER -->|e.g. 'How many documents uploaded?'| STR
    ROUTER -->|e.g. 'List GDPR docs uploaded this month'| HYB
```

Structured queries bypass vector search entirely — a SQL handler translates the question to a safe `SELECT` (validated to only touch the `documents` table) and the LLM wraps the result in a natural sentence.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, TanStack Query |
| API | FastAPI, Pydantic v2, slowapi (rate limiting) |
| Database | PostgreSQL 17 + pgvector extension |
| ORM | SQLAlchemy 2 (async) + Alembic migrations |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers |
| Re-ranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Grounding NLI | `cross-encoder/nli-deberta-v3-small` |
| PII Detection | Microsoft Presidio + spaCy |
| LLM | OpenRouter (model-agnostic — swap via config) |
| Evaluation | Ragas (async background task) |
| Parsing | PyMuPDF (PDF), LlamaIndex SentenceSplitter |
| Observability | structlog, OpenTelemetry, Prometheus |
| Containerisation | Docker Compose (db + api + frontend) |

---

## Running Locally

**Prerequisites:** Docker Desktop, an OpenRouter API key.

```bash
# 1. Clone and configure
git clone https://github.com/YOUR_USERNAME/project-2-rag-with-guardrails.git
cd project-2-rag-with-guardrails
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY and API_KEY

# 2. Start the stack (builds images, runs migrations, starts all services)
docker compose up -d

# 3. Open the UI
open http://localhost:3000

# 4. Run integration tests (requires stack running)
pytest tests/integration/ -v --no-cov

# 5. Run e2e tests
pytest tests/e2e/ -v --no-cov
```

**Unit tests** (no Docker required):
```bash
pip install -e ".[dev]"
pytest tests/unit/ -v --no-cov
```

---

## API

All routes except `GET /api/health` require `X-API-Key` header.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check — public |
| `POST` | `/api/query` | Ask a question |
| `GET` | `/api/documents` | List uploaded documents |
| `POST` | `/api/documents/upload` | Upload a document |
| `GET` | `/api/documents/{id}` | Get document status |
| `DELETE` | `/api/documents/{id}` | Delete document and chunks |
| `POST` | `/api/evaluations` | Start a Ragas evaluation run |
| `GET` | `/api/evaluations/{run_id}` | Poll evaluation status |
| `GET` | `/api/evaluations/{run_id}/results` | Get evaluation scores |

### Example query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How long must we retain personal data under GDPR?",
    "session_id": "my-session-001"
  }'
```

```json
{
  "blocked": false,
  "answer": "Under GDPR Article 5(1)(e), personal data must not be kept for longer than is necessary for the purposes for which it is processed...",
  "sources": ["chunk text 1", "chunk text 2", "chunk text 3"],
  "confidence": 0.84,
  "grounded": true,
  "session_id": "my-session-001"
}
```

---

## Project Structure

```
src/rag_guardrails/
├── api/
│   ├── routes/          # FastAPI route handlers
│   │   ├── query.py     # Query pipeline + routing
│   │   ├── documents.py # Document lifecycle
│   │   └── evaluations.py # Async Ragas evaluation
│   └── dependencies.py  # API key auth
├── guardrails/
│   ├── input_guards.py  # Injection, topic, PII (input)
│   └── output_guards.py # Grounding, PII redaction (output)
├── retrieval/
│   ├── query_router.py  # Semantic / structured / hybrid classifier
│   └── structured_handler.py # NL → SQL for metadata queries
├── ingestion/           # Document parsing, chunking, embedding
├── models/              # SQLAlchemy ORM models
├── core/                # Config, database, logging
└── evaluation/          # Ragas runner

tests/
├── unit/                # Fast, no external deps
├── integration/         # Against live Docker stack (port 8000)
└── e2e/                 # Full adversarial scenarios
```

---

## Design Decisions

**Why not one big guardrail?** A single LLM-based "is this safe?" check is tempting but wrong. It would be slow (every query makes an extra LLM call), expensive, non-deterministic, and can itself be prompt-injected. The three-technique approach uses the cheapest correct tool for each problem.

**Why pgvector over a dedicated vector DB?** The knowledge base fits in a single Postgres instance already used for everything else. Eliminating a second stateful service reduces operational complexity with no retrieval quality penalty at this scale.

**Why OpenRouter?** A single API key that routes to any major LLM. Changing models (Claude → GPT-4o-mini → Gemini) is a one-line config change. For a compliance use case where the "best" model may change based on cost/quality trade-offs, this is practical.

**Why two-tier grounding?** Token overlap is O(n) and catches most clean cases. NLI (DeBERTa) is accurate but ~200ms. Running NLI only when overlap fails keeps p50 latency low while catching logical contradictions the fast check misses.
