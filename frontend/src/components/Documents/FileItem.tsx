
import type { Document } from '../../types/api'

interface FileItemProps {
  document: Document
  onDelete: (id: number) => void
  isDeleting: boolean
}

const STATUS_LABELS: Record<Document['status'], string> = {
  processing: 'Processing',
  ready: 'Ready',
  error: 'Error',
  quarantined: 'Quarantined',
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FileItem({ document, onDelete, isDeleting }: FileItemProps) {
  return (
    <div className={`file-item file-item--${document.status}`}>
      <div className="file-item__icon" aria-hidden="true">
        {document.status === 'ready' ? '✅' : document.status === 'error' ? '❌' : document.status === 'quarantined' ? '🚫' : '⏳'}
      </div>
      <div className="file-item__info">
        <span className="file-item__name">{document.filename}</span>
        <span className="file-item__meta">
          {formatBytes(document.file_size)} · {document.chunk_count} chunks
          {document.injection_risk && (
            <span className="file-item__risk-badge" title="Injection risk detected">⚠ injection risk</span>
          )}
        </span>
      </div>
      <span className={`file-item__status file-item__status--${document.status}`}>
        {STATUS_LABELS[document.status]}
      </span>
      <button
        className="file-item__delete"
        onClick={() => onDelete(document.id)}
        disabled={isDeleting}
        aria-label={`Delete ${document.filename}`}
      >
        🗑
      </button>
    </div>
  )
}
