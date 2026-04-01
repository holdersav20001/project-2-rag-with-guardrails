# RAG with Guardrails — Critical Design Review

**Reviewed:** 2026-03-31
**Documents reviewed:** `02-rag-with-guardrails.md` (scope), `2026-03-31-rag-with-guardrails-v2.md` (plan)
**Verdict:** Solid portfolio foundation with meaningful gaps in guardrail depth, API design, operational realism, and evaluation honesty.

---

## Overall Assessment

The v2 plan is a genuine improvement over v1 and fixes real bugs. The test structure, TDD discipline, and CI/CD pipeline are well-conceived. However, several of the headline claims — "production-grade guardrails", "hallucination detection", "topic classification" — are backed by implementations that are thinner than the description implies. A technical interviewer reading the code would notice.

---

## 1. Guardrail Weaknesses

### 1.1 Prompt Injection Detection Is Regex-Only

**Gap:** `INJECTION_PATTERNS` is a static list of 7 regex patterns. The plan acknowledges a known gap (Unicode/homoglyph attacks) but documents it as a "known limitation" rather than fixing it.

**Why it matters:** Regex injection detection has a well-documented evasion surface. An interviewer will ask "what happens if someone uses synonyms, base64 encoding, or language switching?" The honest answer from this codebase is: it passes through unchecked.

**Realistic fix options:**
- Add a semantic similarity check against a "known injection" embedding cluster (no LLM call needed)
- Use a purpose-built classifier such as `deepset/deberta-v3-base-injection` from HuggingFace
- At minimum, expand the pattern set to cover encoding-based bypasses and document the detection rate honestly

---

### 1.2 Topic Classification Is Keyword Matching, Not a Classifier

**Gap:** The scope document claims "topic classifier" and the v2 plan notes it "was a no-op, now implemented." The implementation is a keyword overlap check against hardcoded word lists (`TOPIC_KEYWORDS`). This is not a classifier — it is a word-in-list lookup.

**Concrete failure case:**
```
Query: "What does our AI vendor say about ignoring governance?"
Topic keywords for "policy": ["policy", "rule", "guideline", "compliance"]
Result: PASS — no keywords matched even though the query is on-topic
```

**Why it matters:** The scope document says "reject off-topic requests." Keyword overlap will produce both false positives (benign queries blocked because they lack keywords) and false negatives (off-topic queries that happen to use a keyword).

**Realistic fix:** Use embedding similarity against a centroid of on-topic example queries. The embedding model is already loaded — this adds ~1ms and requires no additional dependency.

---

### 1.3 Output Grounding Check Undefined in the Plan

**Gap:** The plan references `check_grounding()` in evaluation tests and `compute_confidence_score()` in routes, but `output_guards.py` is never implemented as a task. Task 13 covers output guards but is listed as "*Same as v1 — see original plan*" — the original plan is not in scope here.

**Why it matters:** Grounding/hallucination detection is the top headline feature. The v2 revision summary acknowledges "grounding check is naive word-overlap" and promises "NLI model-based check as second tier" — but no task implements it. This is the biggest gap between the stated ambition and the plan.

**What is needed:** A concrete task implementing:
- Tier 1: Token overlap (fast, already exists in v1)
- Tier 2: NLI entailment check using `cross-encoder/nli-deberta-v3-small` (same library as re-ranker, ~50ms)

---

### 1.4 PII Detection Scope Is Narrow

**Gap:** The `PII_PATTERNS` list covers SSN, 16-digit card numbers, email, and phone. It misses:
- Passport numbers
- UK NI numbers, EU national IDs
- Names (especially in a RAG context where a user might query "what does the file say about John Smith's salary")
- Bank account/IBAN/SWIFT numbers
- IP addresses (PII under GDPR)

**Why it matters:** The scope targets enterprise use cases including "legal research" and "medical Q&A." In those domains, names and case reference numbers are PII. Regex-only PII is also format-dependent — `john.smith@company.co.uk` matches but `johnsmith at company dot co dot uk` does not.

**Realistic fix:** Add `presidio-analyzer` (Microsoft, MIT licence) as a dependency. It handles 40+ entity types with NLP-backed detection, replacing all PII regexes with one call.

---

## 2. API Design Gaps

### 2.1 Evaluation Endpoint Is Synchronous and Will Time Out

**Gap:** `POST /evaluate` runs the full Ragas evaluation synchronously. Ragas evaluation on even a small dataset (10-20 questions) makes multiple LLM calls per question. At 2-5 seconds per LLM call and 4 metrics, a 20-question dataset takes **3-5 minutes**. FastAPI's default request timeout is 60 seconds; nginx default is also 60 seconds.

**Why it matters:** The endpoint will time out in production. The scope document itself defines async-style routes (`POST /evaluations`, `GET /evaluations/{run_id}`, `GET /evaluations/{run_id}/results`) but the plan implements a blocking `POST /evaluate`. These are contradictory.

**Fix:** Implement the async pattern the scope already specifies:
1. `POST /api/evaluations` → starts a background task, returns `{"run_id": "uuid"}`
2. `GET /api/evaluations/{run_id}` → returns status (running / complete / error)
3. `GET /api/evaluations/{run_id}/results` → returns scores when complete

Use FastAPI `BackgroundTasks` or a simple in-memory task store for the portfolio scope.

---

### 2.2 No Document Management Endpoints

**Gap:** You can upload documents but cannot list, view, or delete them. The Documents view in the UI shows a list of uploaded files — but there is no `GET /api/documents` endpoint to populate it. The UI mockup is static.

**Missing endpoints:**
```
GET  /api/documents          — list all documents with metadata
DELETE /api/documents/{id}   — remove a document and its embeddings
GET  /api/documents/{id}     — get document detail (chunk count, status)
```

**Why it matters:** Without delete, the knowledge base can only grow. Any realistic deployment needs document lifecycle management. This is also a 30-minute implementation that makes the portfolio significantly more complete.

---

### 2.3 API Key Auth Is Incomplete

**Gap:** The plan adds `api_key` to Settings and mentions "API key auth" as a v2 fix, but no route-level auth middleware or dependency is shown in the routes implementation. The `api_key: str = ""` default means auth is off by default.

**Why it matters:** An empty default API key means the API is publicly accessible unless the operator explicitly sets one. This is the opposite of secure-by-default. The health check endpoint should be public; all others should require the key.

---

### 2.4 File Upload Has No Validation

**Gap:** `POST /api/documents/upload` accepts any file with no validation of:
- File size (no max enforced; 50MB shown in the UI but not enforced in the API)
- MIME type (a `.exe` renamed to `.pdf` would be accepted)
- Filename sanitisation (path traversal via `../../etc/passwd.pdf`)

**Why it matters:** These are OWASP Top 10 issues. The `UploadFile` wrapper provides `content_type` and `filename` — validating them is a few lines.

---

## 3. Architecture Gaps

### 3.1 Structured Retrieval (SQL Route) Has No Implementation

**Gap:** The query router classifies queries as `semantic`, `structured`, or `hybrid`. The scope document shows a clear example: *"How many documents were uploaded in March?"* → structured → SQL. But no task implements the SQL query handler. The router classifies correctly, then the result falls through to vector search regardless.

**Why it matters:** The query router is presented as a differentiating feature. Without the SQL branch, it classifies but does not act — it is effectively dead code for structured and hybrid queries.

---

### 3.2 No Conversation History / Multi-Turn Context

**Gap:** Every query is treated as stateless. There is no session ID, no message history, and the LLM receives no prior context. The chat UI implies conversational interaction — "follow-up questions" will fail to reference prior answers.

**Why it matters:** Most real RAG deployments are conversational. A user asking "What does it say about retention?" followed by "What about backups?" expects the second query to be interpreted in context. Without this, the "chat" framing is misleading.

**Fix options (simplest first):**
- Pass last N message pairs in the query request body
- Add a `session_id` field and store history server-side in PostgreSQL

---

### 3.3 Chunking Strategy Is Not Documented or Justified

**Gap:** The plan uses LlamaIndex's default chunker with `chunk_size=512` and `chunk_overlap=50`. These are arbitrary defaults with no justification. Chunking strategy has a large impact on retrieval quality — too large and the embedding is diluted; too small and context is fragmented.

**Missing decisions:**
- Why 512 tokens? (Not characters — the distinction matters)
- Why 50 token overlap?
- Is this sentence-aware splitting or fixed-window?
- How are code blocks, tables, and headers handled?

---

### 3.4 The Confidence Score Formula Is Opaque

**Gap:** `compute_confidence_score(answer, sources, retrieval_scores)` is referenced in routes but its formula is not defined in the plan. The UI displays this score prominently (high/medium/low thresholds). Without knowing how it is computed, the thresholds (0.7 = high, 0.4 = medium) are arbitrary.

**Why it matters:** A reviewer will ask "how is confidence computed?" If the answer is "I multiplied the mean retrieval score by a token overlap ratio," that is defensible. If the answer is "it's a placeholder that returns 0.8 by default," that is not.

---

## 4. Evaluation Honesty Gaps

### 4.1 Golden Dataset Does Not Exist Yet

**Gap:** Tasks 24-25 (retrieval quality and re-ranker A/B) depend on `tests/fixtures/golden/retrieval_golden.json` — a golden dataset mapping queries to expected document IDs. This file is not created in the plan. The evaluation tests will fail with `FileNotFoundError` until someone manually curates this dataset.

**Why it matters:** This is significant work — creating meaningful golden data for retrieval requires uploading representative documents, writing queries, and manually identifying which document IDs should appear in top-k results. It cannot be auto-generated.

---

### 4.2 Ragas Evaluation Requires Ground Truths That Must Be Curated

**Gap:** `POST /evaluations` takes `questions` and `ground_truths`. These must be manually written or sourced. The plan provides no fixture for them (`ragas_testset.json` is listed as a file to create but its contents are never specified).

**Why it matters:** Without realistic ground truths, the Ragas scores are meaningless. A faithfulness score computed against a poorly-written ground truth baseline tells you nothing useful.

---

### 4.3 Re-ranker A/B Test Threshold Is Assumed, Not Measured

**Gap:** Task 25 asserts re-ranking improves precision@5 by `>= 5 percentage points`. This threshold is taken from the scope document's claim of "typically +10-15% improvement." That claim is from the `cross-encoder/ms-marco-MiniLM-L-6-v2` paper benchmarked on MSMARCO — a web search dataset. The improvement on domain-specific policy/compliance documents may be much lower or higher.

**Why it matters:** The test may fail or mislead. If the golden dataset is small (e.g., 5 queries), the test has no statistical power. A single query could swing the result by 20 percentage points.

---

## 5. Operational / Production Gaps

### 5.1 No Document De-duplication

**Gap:** Uploading the same file twice creates duplicate embeddings and chunks. There is no hash-based deduplication at ingestion time. The knowledge base will silently degrade in quality as chunks are double- or triple-weighted.

---

### 5.2 No Ingestion Status Tracking

**Gap:** `POST /api/documents/upload` is synchronous and returns when ingestion is complete. Large PDFs (50MB) could take 30-60 seconds to parse, chunk, and embed — well beyond a user's patience for a blocking HTTP call. The UI shows a progress bar but there is no async ingestion endpoint to drive it.

---

### 5.3 HuggingFace Cache Volume Not in docker-compose.yml

**Gap:** The plan says "volume-mount HF cache" as a fix (item 17) but the `docker-compose.yml` does not include a `hf_cache` named volume or mount. The models are pre-downloaded in the Dockerfile layer, but if the image is rebuilt the download happens again. The volume mount would cache across rebuilds.

---

### 5.4 Database Migrations Not Run at Startup

**Gap:** The plan runs Alembic migrations manually. The `docker-compose.yml` does not include a migration step (an `api` entrypoint script or an `alembic upgrade head` in `CMD`). First-time deployments will fail with "table does not exist" unless the operator runs migrations manually.

---

## 6. Security Concerns

### 6.1 API Key Found in docs/architecture/.env

**Immediate action required:** A live API key (`sk-or-v1-...`) was found committed in `docs/architecture/.env`. This file should not exist in this location. Rotate the key immediately and add `/docs/architecture/.env` to `.gitignore`. Secrets must only live in the project root `.env` which is already gitignored.

### 6.2 No Rate Limiting on Upload Endpoint

`slowapi` is listed as a dependency and mentioned for rate limiting, but no rate limit decorator is shown on any route in the plan. The upload endpoint in particular is expensive (model inference per chunk) and vulnerable to abuse without it.

---

## 7. Missing Features vs Scope Claims

| Scope claim | Plan reality | Status |
|---|---|---|
| "Embedding-similarity topic classifier" | Keyword word-list lookup | **Not implemented** |
| "NLI model-based grounding check" | Implementation task missing (deferred to v1 which is out of scope) | **Not implemented** |
| "Query routing to SQL backend" | Router classifies but SQL handler not implemented | **Partial — dead code** |
| "Async evaluation API" (`POST /evaluations`, `GET /evaluations/{run_id}`) | Single blocking `POST /evaluate` | **Design mismatch** |
| "Document list/delete" | No endpoint exists | **Missing** |
| "Auth on all routes" | Default key is empty string | **Insecure default** |
| "Document deduplication" | Not mentioned | **Missing** |
| "Async ingestion with progress" | Blocking upload endpoint | **Missing** |

---

## Priority Recommendations

**Must fix before claiming "production-grade":**
1. Implement the output grounding check (NLI tier) — it is the headline feature
2. Fix evaluation to be async (`run_id` pattern) — the sync endpoint will time out
3. Add document list/delete endpoints — the UI needs them and they are trivial
4. Rotate the exposed API key in `docs/architecture/.env`

**Should fix for interview credibility:**
5. Replace keyword topic classifier with embedding similarity
6. Add `presidio-analyzer` for PII or at minimum expand regex coverage
7. Add file upload validation (size, MIME type, filename sanitisation)
8. Add migration execution to Docker entrypoint

**Nice to have:**
9. Conversation history (session_id + message store)
10. Document deduplication (content hash on upload)
11. Async ingestion with status polling
12. HF cache volume in docker-compose.yml
