export interface TimeRange {
  start: string
  end: string
}

interface Props {
  timeRange: TimeRange
  onTimeRangeChange: (range: TimeRange) => void
}

export function TimeRangeBar({ timeRange, onTimeRangeChange }: Props) {
  const hasValue = timeRange.start !== '' || timeRange.end !== ''

  return (
    <div className="time-range-bar">
      <label>
        Start:{' '}
        <input
          type="datetime-local"
          data-testid="time-range-start"
          value={timeRange.start}
          onChange={(e) => onTimeRangeChange({ ...timeRange, start: e.target.value })}
        />
      </label>
      <label>
        End:{' '}
        <input
          type="datetime-local"
          data-testid="time-range-end"
          value={timeRange.end}
          onChange={(e) => onTimeRangeChange({ ...timeRange, end: e.target.value })}
        />
      </label>
      {hasValue && (
        <button
          type="button"
          data-testid="time-range-clear"
          onClick={() => onTimeRangeChange({ start: '', end: '' })}
        >
          Clear
        </button>
      )}
    </div>
  )
}
