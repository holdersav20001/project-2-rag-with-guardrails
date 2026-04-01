import { useCallback, useState } from 'react'

interface DropZoneProps {
  onFiles: (files: File[]) => void
  disabled: boolean
}

const ACCEPTED = ['.pdf', '.txt', '.md', '.docx']
const ACCEPTED_MIME = ['application/pdf', 'text/plain', 'text/markdown', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

export default function DropZone({ onFiles, disabled }: DropZoneProps) {
  const [dragging, setDragging] = useState(false)

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList) return
    const valid = Array.from(fileList).filter((f) =>
      ACCEPTED_MIME.includes(f.type) ||
      ACCEPTED.some((ext) => f.name.toLowerCase().endsWith(ext))
    )
    if (valid.length > 0) onFiles(valid)
  }, [onFiles])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (!disabled) handleFiles(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) setDragging(true)
  }

  const handleDragLeave = () => setDragging(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files)
    e.target.value = ''
  }

  return (
    <label
      className={`dropzone ${dragging ? 'dropzone--active' : ''} ${disabled ? 'dropzone--disabled' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      aria-label="Upload documents"
    >
      <input
        type="file"
        className="dropzone__input"
        multiple
        accept={ACCEPTED.join(',')}
        onChange={handleChange}
        disabled={disabled}
        aria-hidden="true"
        tabIndex={-1}
      />
      <div className="dropzone__icon" aria-hidden="true">📄</div>
      <p className="dropzone__text">
        {dragging ? 'Drop files here' : 'Drag & drop files or click to browse'}
      </p>
      <p className="dropzone__hint">PDF, TXT, MD, DOCX · max 10 MB each</p>
    </label>
  )
}
