
import type { Source } from '../../types/api'
import SourceCard from './SourceCard'

interface CitationPanelProps {
  sources: Source[]
  onClose: () => void
}

export default function CitationPanel({ sources, onClose }: CitationPanelProps) {
  return (
    <aside className="citation-panel" aria-label="Source citations">
      <div className="citation-panel__header">
        <h2 className="citation-panel__title">Sources ({sources.length})</h2>
        <button
          className="citation-panel__close"
          onClick={onClose}
          aria-label="Close citation panel"
        >
          ✕
        </button>
      </div>
      <div className="citation-panel__list">
        {sources.map((source, i) => (
          <SourceCard key={`${source.doc_id ?? i}-${source.chunk ?? i}`} source={source} index={i} />
        ))}
      </div>
    </aside>
  )
}
