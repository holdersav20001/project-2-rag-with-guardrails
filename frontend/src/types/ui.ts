/* ==========================================================================
   UI Type Definitions -- RAG with Guardrails
   ==========================================================================
   Shared types that connect API response shapes to component props.
   ========================================================================== */

// ---------------------------------------------------------------------------
// API response types (mirrored from backend)
// ---------------------------------------------------------------------------

export interface Source {
  filename: string;
  chunk_index: number;
  text: string;
  score: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  confidence: number;  // 0.0 to 1.0
  blocked: boolean;
  block_reason: string;
}

// ---------------------------------------------------------------------------
// UI-specific types
// ---------------------------------------------------------------------------

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export type MessageRole = 'user' | 'ai';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  /** Present only on AI messages */
  sources?: Source[];
  /** Present only on AI messages */
  confidence?: number;
  /** Present only on blocked messages */
  blocked?: boolean;
  /** Present only on blocked messages */
  block_reason?: string;
}

export type UploadStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

export interface UploadFile {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;       // 0-100
  error?: string;
}

export type ViewTab = 'chat' | 'documents';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Map a 0.0-1.0 confidence score to a semantic level for styling.
 *
 * Thresholds:
 *   >= 0.7  -> high   (green)
 *   >= 0.4  -> medium (amber)
 *   <  0.4  -> low    (red)
 */
export function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.7) return 'high';
  if (score >= 0.4) return 'medium';
  return 'low';
}

/**
 * Format a 0.0-1.0 score as a percentage string, e.g. "87%".
 */
export function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/**
 * Get the file extension from a filename, lowercased.
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop()!.toLowerCase() : '';
}
