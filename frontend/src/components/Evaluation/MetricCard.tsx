import { getConfidenceLevel, formatScore } from '../../types/ui'

interface MetricCardProps {
  label: string
  score: number | undefined
  description: string
  meaning: string
}

export default function MetricCard({ label, score, description, meaning }: MetricCardProps) {
  const level = score !== undefined ? getConfidenceLevel(score) : undefined

  return (
    <div className={`metric-card ${level ? `metric-card--${level}` : 'metric-card--pending'}`}>
      <p className="metric-card__label">{label}</p>
      <p className="metric-card__score">
        {score !== undefined ? formatScore(score) : '—'}
      </p>
      <p className="metric-card__description">{description}</p>
      <p className="metric-card__meaning">{meaning}</p>
    </div>
  )
}
