
import { getConfidenceLevel, formatScore } from '../../types/ui'

interface ConfidenceBadgeProps {
  score: number
}

export default function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const level = getConfidenceLevel(score)
  return (
    <span
      className={`confidence-badge confidence-badge--${level}`}
      title={`Confidence: ${formatScore(score)}`}
      aria-label={`Confidence ${level}: ${formatScore(score)}`}
    >
      {formatScore(score)}
    </span>
  )
}
