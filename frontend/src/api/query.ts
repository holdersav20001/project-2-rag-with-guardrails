import { api } from './client'
import type { QueryRequest, QueryResponse } from '../types/api'

export async function postQuery(request: QueryRequest): Promise<QueryResponse> {
  return api.post<QueryResponse>('/query', request)
}
