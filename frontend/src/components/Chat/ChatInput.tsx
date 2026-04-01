import { useState, useCallback, useRef } from 'react'

interface ChatInputProps {
  onSend: (query: string) => void
  disabled: boolean
}

const MAX_CHARS = 2000

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, onSend])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value.slice(0, MAX_CHARS))
    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
  }

  const remaining = MAX_CHARS - value.length
  const nearLimit = remaining < 200

  return (
    <div className="chat-input">
      <div className="chat-input__wrapper">
        <textarea
          ref={textareaRef}
          className="chat-input__textarea"
          placeholder="Ask a question… (Enter to send, Shift+Enter for new line)"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          aria-label="Message input"
          aria-describedby={nearLimit ? 'chat-input-limit' : undefined}
        />
        <button
          className="chat-input__send"
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
        >
          ↑
        </button>
      </div>
      {nearLimit && (
        <p id="chat-input-limit" className="chat-input__limit" aria-live="polite">
          {remaining} characters remaining
        </p>
      )}
    </div>
  )
}
