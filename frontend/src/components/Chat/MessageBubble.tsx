import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '../../hooks/useChat'
import BlockedMessage from './BlockedMessage'
import ConfidenceBadge from './ConfidenceBadge'

interface MessageBubbleProps {
  message: ChatMessage
  onShowSources?: (sources: NonNullable<ChatMessage['sources']>) => void
}

export default function MessageBubble({ message, onShowSources }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  if (message.blocked) {
    return (
      <div className="message message--assistant">
        <BlockedMessage guardrail={message.guardrail} reason={message.reason} />
      </div>
    )
  }

  return (
    <div className={`message message--${isUser ? 'user' : 'assistant'}`}>
      <div className={`message__bubble message__bubble--${isUser ? 'user' : 'assistant'}`}>
        <div className="message__text message__markdown">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {!isUser && (
          <div className="message__footer">
            {message.grounded !== undefined && (
              <span
                className={`grounded-badge grounded-badge--${message.grounded ? 'true' : 'false'}`}
                title={message.grounded
                  ? 'NLI check passed — answer is supported by the retrieved documents'
                  : 'NLI check failed — answer may not be fully supported by sources'}
              >
                {message.grounded ? '✓ sourced' : '⚠ ungrounded'}
              </span>
            )}
            {message.confidence !== undefined && (
              <ConfidenceBadge score={message.confidence} />
            )}
            {message.sources && message.sources.length > 0 && onShowSources && (
              <button
                className="message__sources-btn"
                onClick={() => onShowSources(message.sources!)}
                aria-label={`View ${message.sources.length} source${message.sources.length !== 1 ? 's' : ''}`}
              >
                {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
              </button>
            )}
          </div>
        )}
      </div>
      <time className="message__time" dateTime={message.timestamp.toISOString()}>
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </time>
    </div>
  )
}
