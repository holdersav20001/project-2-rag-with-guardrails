

export default function TypingIndicator() {
  return (
    <div className="message message--assistant" aria-live="polite" aria-label="Assistant is typing">
      <div className="message__bubble message__bubble--assistant">
        <div className="typing-indicator">
          <span className="typing-indicator__dot" />
          <span className="typing-indicator__dot" />
          <span className="typing-indicator__dot" />
        </div>
      </div>
    </div>
  )
}
