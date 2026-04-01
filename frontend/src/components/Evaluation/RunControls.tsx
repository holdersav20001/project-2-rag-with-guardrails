import { useState } from 'react'
import type { EvalRequest } from '../../types/api'

interface RunControlsProps {
  onStart: (request: EvalRequest) => void
  onReset: () => void
  isRunning: boolean
}

interface QAPair {
  question: string
  truth: string
}

const SEED_PAIRS: QAPair[] = [
  {
    question: 'What is the right of access under UK GDPR?',
    truth: 'The right of access allows individuals to obtain a copy of their personal data and supplementary information about how and why it is being used.',
  },
  {
    question: 'How long does an organisation have to respond to a subject access request?',
    truth: 'An organisation must respond to a subject access request without undue delay and within one month of receipt.',
  },
  {
    question: 'What are the requirements for valid cookie consent?',
    truth: 'Cookie consent must be freely given, specific, informed and unambiguous, demonstrated through a clear affirmative action such as ticking a box. Pre-ticked boxes are not valid.',
  },
  {
    question: 'What is a personal data breach?',
    truth: 'A personal data breach is a breach of security leading to accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to, personal data.',
  },
  {
    question: 'Can an organisation extend the one month deadline for responding to a SAR?',
    truth: 'Yes, organisations can extend the deadline by a further two months where the request is complex or there are a number of requests, but must inform the individual within one month.',
  },
]

export default function RunControls({ onStart, onReset, isRunning }: RunControlsProps) {
  const [pairs, setPairs] = useState<QAPair[]>(SEED_PAIRS)
  const [model, setModel] = useState('claude-sonnet-4-6')

  const updatePair = (index: number, field: keyof QAPair, value: string) => {
    setPairs(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p))
  }

  const addRow = () => {
    setPairs(prev => [...prev, { question: '', truth: '' }])
  }

  const removeRow = (index: number) => {
    setPairs(prev => prev.filter((_, i) => i !== index))
  }

  const handleStart = () => {
    const valid = pairs.filter(p => p.question.trim() && p.truth.trim())
    if (valid.length === 0) return
    onStart({
      questions: valid.map(p => p.question.trim()),
      ground_truths: valid.map(p => p.truth.trim()),
      model,
    })
  }

  const validCount = pairs.filter(p => p.question.trim() && p.truth.trim()).length

  return (
    <div className="run-controls">
      <div className="run-controls__field">
        <label htmlFor="eval-model" className="run-controls__label">Model</label>
        <select
          id="eval-model"
          className="run-controls__select"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          disabled={isRunning}
        >
          <option value="claude-sonnet-4-6">Claude Sonnet 4.6</option>
          <option value="claude-haiku-4-5-20251001">Claude Haiku 4.5</option>
        </select>
      </div>

      <div className="qa-editor">
        <div className="qa-editor__header">
          <h3 className="qa-editor__title">Questions &amp; Ground Truths</h3>
          <span className="qa-editor__count">{validCount} valid pair{validCount !== 1 ? 's' : ''}</span>
        </div>

        <div className="qa-editor__table-wrap">
          <table className="qa-editor__table">
            <thead>
              <tr>
                <th className="qa-editor__th qa-editor__th--num">#</th>
                <th className="qa-editor__th">Question</th>
                <th className="qa-editor__th">Ground Truth</th>
                <th className="qa-editor__th qa-editor__th--action"></th>
              </tr>
            </thead>
            <tbody>
              {pairs.map((pair, i) => (
                <tr key={i} className="qa-editor__row">
                  <td className="qa-editor__td qa-editor__td--num">{i + 1}</td>
                  <td className="qa-editor__td">
                    <textarea
                      className="qa-editor__input"
                      value={pair.question}
                      onChange={(e) => updatePair(i, 'question', e.target.value)}
                      disabled={isRunning}
                      placeholder="Enter question…"
                      rows={2}
                    />
                  </td>
                  <td className="qa-editor__td">
                    <textarea
                      className="qa-editor__input"
                      value={pair.truth}
                      onChange={(e) => updatePair(i, 'truth', e.target.value)}
                      disabled={isRunning}
                      placeholder="Enter expected answer…"
                      rows={2}
                    />
                  </td>
                  <td className="qa-editor__td qa-editor__td--action">
                    <button
                      className="qa-editor__remove-btn"
                      onClick={() => removeRow(i)}
                      disabled={isRunning || pairs.length <= 1}
                      aria-label={`Remove row ${i + 1}`}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <button
          className="qa-editor__add-btn"
          onClick={addRow}
          disabled={isRunning}
        >
          + Add row
        </button>
      </div>

      <div className="run-controls__actions">
        <button
          className="run-controls__start-btn"
          onClick={handleStart}
          disabled={isRunning || validCount === 0}
          aria-busy={isRunning}
        >
          {isRunning ? 'Running…' : `Run Evaluation (${validCount})`}
        </button>
        <button
          className="run-controls__reset-btn"
          onClick={onReset}
          disabled={isRunning}
        >
          Reset
        </button>
      </div>
    </div>
  )
}
