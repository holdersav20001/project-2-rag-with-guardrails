import { useState } from 'react'
import type { Source } from '../../types/api'
import { useChat } from '../../hooks/useChat'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import CitationPanel from './CitationPanel'

export default function ChatView() {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat()
  const [activeSources, setActiveSources] = useState<Source[] | null>(null)

  return (
    <div className={`chat-view ${activeSources ? 'chat-view--with-panel' : ''}`}>
      <div className="chat-view__main">
        <div className="chat-view__toolbar">
          {messages.length > 0 && (
            <button
              className="chat-view__clear-btn"
              onClick={clearMessages}
              aria-label="Clear conversation"
            >
              Clear
            </button>
          )}
        </div>

        <MessageList
          messages={messages}
          isLoading={isLoading}
          onShowSources={(sources) => setActiveSources(sources)}
        />

        {error && (
          <div className="chat-view__error" role="alert">
            {error}
          </div>
        )}

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>

      {activeSources && (
        <CitationPanel
          sources={activeSources}
          onClose={() => setActiveSources(null)}
        />
      )}
    </div>
  )
}
