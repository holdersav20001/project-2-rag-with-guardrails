

interface ProgressBarProps {
  state: 'idle' | 'pending' | 'running' | 'complete' | 'error'
}

const STATE_LABELS: Record<ProgressBarProps['state'], string> = {
  idle: 'Ready',
  pending: 'Starting…',
  running: 'Running evaluation…',
  complete: 'Complete',
  error: 'Failed',
}

export default function ProgressBar({ state }: ProgressBarProps) {
  if (state === 'idle') return null

  const indeterminate = state === 'pending' || state === 'running'
  const percent = state === 'complete' ? 100 : state === 'error' ? 100 : 0

  return (
    <div className="progress-bar-wrapper" aria-label={STATE_LABELS[state]}>
      <div
        className={`progress-bar progress-bar--${state} ${indeterminate ? 'progress-bar--indeterminate' : ''}`}
        role="progressbar"
        aria-valuenow={indeterminate ? undefined : percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={STATE_LABELS[state]}
      />
      <p className="progress-bar__label" aria-live="polite">{STATE_LABELS[state]}</p>
    </div>
  )
}
