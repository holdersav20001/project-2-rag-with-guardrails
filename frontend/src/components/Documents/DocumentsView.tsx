import { useState } from 'react'
import { useDocuments, useUploadDocument, useDeleteDocument } from '../../hooks/useDocuments'
import DropZone from './DropZone'
import FileList from './FileList'

export default function DocumentsView() {
  const { data: documents, isLoading, error } = useDocuments()
  const uploadMutation = useUploadDocument()
  const deleteMutation = useDeleteDocument()
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [uploadErrors, setUploadErrors] = useState<string[]>([])

  const handleFiles = async (files: File[]) => {
    setUploadErrors([])
    for (const file of files) {
      try {
        await uploadMutation.mutateAsync(file)
      } catch (err) {
        setUploadErrors((prev) => [
          ...prev,
          `${file.name}: ${err instanceof Error ? err.message : 'Upload failed'}`,
        ])
      }
    }
  }

  const handleDelete = async (id: number) => {
    setDeletingId(id)
    try {
      await deleteMutation.mutateAsync(id)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="documents-view">
      <div className="documents-view__header">
        <h1 className="documents-view__title">Documents</h1>
        {documents && (
          <span className="documents-view__count">{documents.length} file{documents.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      <DropZone onFiles={handleFiles} disabled={uploadMutation.isPending} />

      {uploadMutation.isPending && (
        <p className="documents-view__uploading" aria-live="polite">Uploading…</p>
      )}

      {uploadErrors.length > 0 && (
        <ul className="documents-view__errors" role="alert">
          {uploadErrors.map((e, i) => (
            <li key={i} className="documents-view__error">{e}</li>
          ))}
        </ul>
      )}

      {error && (
        <p className="documents-view__error" role="alert">
          Failed to load documents: {error instanceof Error ? error.message : 'Unknown error'}
        </p>
      )}

      <FileList
        documents={documents}
        isLoading={isLoading}
        deletingId={deletingId}
        onDelete={handleDelete}
      />
    </div>
  )
}
