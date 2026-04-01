import { useEvaluationRun } from '../../hooks/useEvaluationRun'
import MetricCard from './MetricCard'
import ProgressBar from './ProgressBar'
import RunControls from './RunControls'
import QuestionTable from './QuestionTable'

const METRICS = [
  {
    key: 'faithfulness' as const,
    label: 'Faithfulness',
    description: 'Does the answer only use information from the retrieved documents?',
    meaning: 'High = LLM stayed grounded. Low = LLM is making things up.',
  },
  {
    key: 'answer_relevancy' as const,
    label: 'Answer Relevancy',
    description: 'Does the answer actually address what was asked?',
    meaning: 'High = answer is on-point. Low = answer is vague or off-topic.',
  },
  {
    key: 'context_precision' as const,
    label: 'Context Precision',
    description: 'Of the chunks retrieved, how many were actually useful?',
    meaning: 'High = retrieval finds signal. Low = too much irrelevant content pulled in.',
  },
  {
    key: 'context_recall' as const,
    label: 'Context Recall',
    description: 'Did retrieval surface all the information needed to answer?',
    meaning: 'High = nothing important was missed. Low = relevant content exists but was not found.',
  },
]

export default function EvaluationView() {
  const { runState, results, error, start, reset } = useEvaluationRun()
  const isRunning = runState === 'pending' || runState === 'running'

  return (
    <div className="evaluation-view">
      <div className="evaluation-view__header">
        <h1 className="evaluation-view__title">Evaluation</h1>
        <p className="evaluation-view__subtitle">
          Measure RAG quality using Ragas metrics
        </p>
      </div>

      <div className="evaluation-view__metrics">
        {METRICS.map(({ key, label, description, meaning }) => (
          <MetricCard
            key={key}
            label={label}
            score={results?.scores[key]}
            description={description}
            meaning={meaning}
          />
        ))}
      </div>

      <ProgressBar state={runState} />

      {error && (
        <p className="evaluation-view__error" role="alert">{error}</p>
      )}

      <RunControls
        onStart={start}
        onReset={reset}
        isRunning={isRunning}
      />

      {results && runState === 'complete' && (
        <QuestionTable results={results} />
      )}
    </div>
  )
}
