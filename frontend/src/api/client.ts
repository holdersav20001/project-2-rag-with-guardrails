/**
 * Base API client — all requests go through here.
 * Base URL from VITE_API_URL env var, falls back to relative path (works behind proxy).
 */
const BASE_URL = (import.meta.env.VITE_API_URL ?? '') + '/api'

// API key is passed via header — loaded from env in production, dev uses proxy
const API_KEY = import.meta.env.VITE_API_KEY ?? ''

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    ...(options.headers as Record<string, string> ?? {}),
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(response.status, error.detail ?? 'Request failed')
  }

  // 204 No Content
  if (response.status === 204) return undefined as T

  return response.json()
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  /** Upload a file using multipart/form-data */
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, {
      method: 'POST',
      body: formData,
      headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
    }),
}
