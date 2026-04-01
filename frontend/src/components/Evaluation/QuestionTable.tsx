
import type { EvalResults } from '../../types/api'
import { formatScore, getConfidenceLevel } from '../../types/ui'

interface QuestionTableProps {
  results: EvalResults
}

export default function QuestionTable({ results }: QuestionTableProps) {
  const { scores } = results
  const metrics = [
    { key: 'faithfulness' as const, label: 'Faithfulness' },
    { key: 'answer_relevancy' as const, label: 'Relevancy' },
    { key: 'context_precision' as const, label: 'Precision' },
    { key: 'context_recall' as const, label: 'Recall' },
  ]

  return (
    <div className="question-table">
      <h3 className="question-table__title">Overall Scores</h3>
      <table className="question-table__table" aria-label="Evaluation scores">
        <thead>
          <tr>
            <th scope="col">Metric</th>
            <th scope="col">Score</th>
            <th scope="col">Level</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map(({ key, label }) => {
            const score = scores[key]
            const level = getConfidenceLevel(score)
            return (
              <tr key={key} className={`question-table__row question-table__row--${level}`}>
                <td>{label}</td>
                <td>{formatScore(score)}</td>
                <td>
                  <span className={`question-table__badge question-table__badge--${level}`}>
                    {level}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
