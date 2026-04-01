
import type { Document } from '../../types/api'
import FileItem from './FileItem'
import LoadingSkeleton from '../shared/LoadingSkeleton'

interface FileListProps {
  documents: Document[] | undefined
  isLoading: boolean
  deletingId: number | null
  onDelete: (id: number) => void
}

export default function FileList({ documents, isLoading, deletingId, onDelete }: FileListProps) {
  if (isLoading) {
    return (
      <div className="file-list">
        <LoadingSkeleton lines={3} />
      </div>
    )
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="file-list file-list--empty">
        <p className="file-list__empty">No documents uploaded yet.</p>
      </div>
    )
  }

  return (
    <div className="file-list" role="list" aria-label="Uploaded documents">
      {documents.map((doc) => (
        <div key={doc.id} role="listitem">
          <FileItem
            document={doc}
            onDelete={onDelete}
            isDeleting={deletingId === doc.id}
          />
        </div>
      ))}
    </div>
  )
}
