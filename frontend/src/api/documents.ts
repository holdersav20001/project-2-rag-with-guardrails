import { api } from './client'
import type { Document, DocumentListResponse, UploadResponse } from '../types/api'

export async function listDocuments(): Promise<DocumentListResponse> {
  return api.get<DocumentListResponse>('/documents')
}

export async function getDocument(id: number): Promise<Document> {
  return api.get<Document>(`/documents/${id}`)
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return api.upload<UploadResponse>('/documents/upload', form)
}

/** Upload then poll until status is no longer 'processing'. Returns final document state. */
export async function uploadAndWait(
  file: File,
  onProgress?: (status: Document['status']) => void,
): Promise<Document> {
  const upload = await uploadDocument(file)

  // Already exists — fetch current state
  if (upload.status === 'already_exists') {
    return getDocument(upload.document_id)
  }

  // Poll until ready / error / quarantined
  const MAX_POLLS = 60
  const INTERVAL_MS = 2000
  for (let i = 0; i < MAX_POLLS; i++) {
    await new Promise((r) => setTimeout(r, INTERVAL_MS))
    const doc = await getDocument(upload.document_id)
    onProgress?.(doc.status)
    if (doc.status !== 'processing') return doc
  }
  // Timed out — return whatever state we have
  return getDocument(upload.document_id)
}

export async function deleteDocument(id: number): Promise<void> {
  return api.delete<void>(`/documents/${id}`)
}
