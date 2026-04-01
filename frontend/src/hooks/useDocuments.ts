import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDocuments, uploadAndWait, deleteDocument } from '../api/documents'

const DOCUMENTS_KEY = ['documents'] as const

export function useDocuments() {
  return useQuery({
    queryKey: DOCUMENTS_KEY,
    queryFn: () => listDocuments().then((r) => r.documents),
    staleTime: 30_000,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) =>
      uploadAndWait(file, () => {
        // Refresh list while processing so status badge updates live
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY })
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY })
    },
  })
}
