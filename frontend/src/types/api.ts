/** API response shapes — kept in sync with FastAPI Pydantic models. */

export interface Source {
  text: string
  score: number
  doc_id?: number
  chunk?: number
  filename?: string
}

export interface QueryRequest {
  query: string
  session_id?: string
  top_k?: number
}

export interface QueryResponse {
  blocked: boolean
  guardrail?: string
  reason?: string
  answer?: string
  sources: Source[]
  confidence?: number
  grounded?: boolean
  session_id?: string
}

export interface Document {
  id: number
  filename: string
  file_size: number
  chunk_count: number
  injection_risk: boolean
  status: 'processing' | 'ready' | 'error' | 'quarantined'
  created_at: string
}

export interface DocumentListResponse {
  documents: Document[]
}

export interface UploadResponse {
  document_id: number
  filename: string
  status: string
  message?: string
  injection_risk?: boolean
}

export interface EvalRequest {
  questions: string[]
  ground_truths: string[]
  model?: string
}

export interface EvalRunStatus {
  run_id: string
  status: 'pending' | 'running' | 'complete' | 'error'
  created_at: string
}

export interface EvalScores {
  faithfulness: number
  answer_relevancy: number
  context_precision: number
  context_recall: number
}

export interface EvalResults {
  run_id: string
  status: 'complete'
  scores: EvalScores
}
