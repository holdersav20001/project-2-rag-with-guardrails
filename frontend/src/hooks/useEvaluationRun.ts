import { useState, useCallback, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { startEvaluation, getEvaluationStatus, getEvaluationResults } from '../api/evaluations'
import type { EvalRequest, EvalRunStatus, EvalResults } from '../types/api'

type RunState = 'idle' | 'pending' | 'running' | 'complete' | 'error'

interface UseEvaluationRunReturn {
  runState: RunState
  runId: string | null
  status: EvalRunStatus | null
  results: EvalResults | null
  error: string | null
  start: (request: EvalRequest) => void
  reset: () => void
}

const POLL_INTERVAL_MS = 2000

export function useEvaluationRun(): UseEvaluationRunReturn {
  const [runState, setRunState] = useState<RunState>('idle')
  const [runId, setRunId] = useState<string | null>(null)
  const [status, setStatus] = useState<EvalRunStatus | null>(null)
  const [results, setResults] = useState<EvalResults | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const poll = useCallback(async (id: string) => {
    try {
      const s = await getEvaluationStatus(id)
      setStatus(s)

      if (s.status === 'complete') {
        stopPolling()
        const r = await getEvaluationResults(id)
        setResults(r)
        setRunState('complete')
      } else if (s.status === 'error') {
        stopPolling()
        setError('Evaluation run failed.')
        setRunState('error')
      } else {
        setRunState(s.status === 'pending' ? 'pending' : 'running')
      }
    } catch (err) {
      stopPolling()
      setError(err instanceof Error ? err.message : 'Polling failed.')
      setRunState('error')
    }
  }, [stopPolling])

  const startMutation = useMutation({
    mutationFn: (request: EvalRequest) => startEvaluation(request),
    onSuccess: (data) => {
      const id = data.run_id
      setRunId(id)
      setRunState('pending')
      setError(null)
      setResults(null)
      setStatus(null)

      poll(id)
      pollRef.current = setInterval(() => poll(id), POLL_INTERVAL_MS)
    },
    onError: (err: Error) => {
      setError(err.message)
      setRunState('error')
    },
  })

  const reset = useCallback(() => {
    stopPolling()
    setRunState('idle')
    setRunId(null)
    setStatus(null)
    setResults(null)
    setError(null)
  }, [stopPolling])

  return {
    runState,
    runId,
    status,
    results,
    error,
    start: (request) => startMutation.mutate(request),
    reset,
  }
}
