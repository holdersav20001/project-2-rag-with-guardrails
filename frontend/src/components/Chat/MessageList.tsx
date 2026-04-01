import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../../hooks/useChat'
import type { Source } from '../../types/api'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'

interface MessageListProps {
  messages: ChatMessage[]
  isLoading: boolean
  onShowSources: (sources: Source[]) => void
}

export default function MessageList({ messages, isLoading, onShowSources }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="message-list message-list--empty">
        <div className="message-list__empty-state">
          <p className="message-list__empty-title">Ask anything about your documents</p>
          <p className="message-list__empty-hint">
            Upload documents in the Documents tab, then ask questions here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="message-list" role="log" aria-live="polite" aria-label="Conversation">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onShowSources={onShowSources} />
      ))}
      {isLoading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  )
}
