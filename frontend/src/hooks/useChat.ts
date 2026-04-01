import { useState, useCallback, useRef } from 'react'
import { postQuery } from '../api/query'
import type { QueryResponse, Source } from '../types/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  blocked?: boolean
  guardrail?: string
  reason?: string
  sources?: Source[]
  confidence?: number
  grounded?: boolean
}

interface UseChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  sessionId: string | undefined
  sendMessage: (query: string) => Promise<void>
  clearMessages: () => void
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sessionIdRef = useRef<string | undefined>(undefined)

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return

    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: query.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const response: QueryResponse = await postQuery({
        query: query.trim(),
        session_id: sessionIdRef.current,
        top_k: 5,
      })

      if (response.session_id) {
        sessionIdRef.current = response.session_id
      }

      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.blocked ? (response.reason ?? 'This query was blocked.') : (response.answer ?? ''),
        timestamp: new Date(),
        blocked: response.blocked,
        guardrail: response.guardrail,
        reason: response.reason,
        sources: response.sources,
        confidence: response.confidence,
        grounded: response.grounded,
      }

      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  const clearMessages = useCallback(() => {
    setMessages([])
    sessionIdRef.current = undefined
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    sessionId: sessionIdRef.current,
    sendMessage,
    clearMessages,
  }
}
