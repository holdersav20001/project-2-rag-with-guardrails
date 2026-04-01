import { useState } from 'react'
import type { Source } from '../../types/api'
import { formatScore } from '../../types/ui'

interface SourceCardProps {
  source: Source
  index: number
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="source-card">
      <div className="source-card__header">
        <span className="source-card__index">{index + 1}</span>
        <div className="source-card__meta">
          <span className="source-card__filename">{source.filename ?? 'Unknown source'}</span>
          {source.chunk !== undefined && (
            <span className="source-card__chunk">chunk {source.chunk}</span>
          )}
        </div>
        <span className="source-card__score">{formatScore(source.score)}</span>
        <button
          className="source-card__toggle"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Collapse source text' : 'Expand source text'}
        >
          {expanded ? '▲' : '▼'}
        </button>
      </div>
      {expanded && (
        <p className="source-card__text">{source.text}</p>
      )}
    </div>
  )
}
