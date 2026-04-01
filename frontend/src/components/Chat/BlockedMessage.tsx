

interface BlockedMessageProps {
  guardrail?: string
  reason?: string
}

const GUARDRAIL_LABELS: Record<string, string> = {
  injection: 'Prompt Injection',
  topic: 'Off-Topic Query',
  pii: 'PII Detected',
}

export default function BlockedMessage({ guardrail, reason }: BlockedMessageProps) {
  const label = guardrail ? (GUARDRAIL_LABELS[guardrail] ?? guardrail) : 'Guardrail'

  return (
    <div className="blocked-message" role="alert">
      <div className="blocked-message__icon" aria-hidden="true">🛡️</div>
      <div className="blocked-message__body">
        <p className="blocked-message__title">Blocked by {label}</p>
        {reason && <p className="blocked-message__reason">{reason}</p>}
      </div>
    </div>
  )
}
