import { api } from './client'
import type { EvalRequest, EvalRunStatus, EvalResults } from '../types/api'

export async function startEvaluation(request: EvalRequest): Promise<{ run_id: string; status: string }> {
  return api.post('/evaluations', request)
}

export async function getEvaluationStatus(runId: string): Promise<EvalRunStatus> {
  return api.get<EvalRunStatus>(`/evaluations/${runId}`)
}

export async function getEvaluationResults(runId: string): Promise<EvalResults> {
  return api.get<EvalResults>(`/evaluations/${runId}/results`)
}
