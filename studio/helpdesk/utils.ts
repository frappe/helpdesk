export function parseJson(value: unknown, fallback: any = undefined) {
  if (!value) return fallback
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value) ?? fallback
  } catch {
    return fallback
  }
}

export function parseJsonArray(value: unknown): any[] {
  const parsed = parseJson(value, [])
  return Array.isArray(parsed) ? parsed : []
}

export function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

const MINUTE = 60
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

// Two units at most, and no trailing seconds: a countdown that re-renders only on load
// reads as a frozen timer when it shows them. The desk has no equivalent — its
// `shortDuration` counts to a date, this one formats an elapsed span.
export function compactDuration(seconds: number) {
  return (
    compactUnits(seconds)
      .map(([value, unit]) => `${value}${unit}`)
      .join(' ') || '0s'
  )
}

// The largest unit and the one below it, so 83 days and 59 minutes reads as "83 days".
function compactUnits(seconds: number) {
  const all: [number, string][] = [
    [Math.floor(seconds / DAY), 'd'],
    [Math.floor((seconds % DAY) / HOUR), 'h'],
    [Math.floor((seconds % HOUR) / MINUTE), 'm'],
    [Math.floor(seconds % MINUTE), 's'],
  ]
  const largest = all.findIndex(([value]) => value)
  if (largest < 0) return []
  return all.slice(largest, largest + 2).filter(([value]) => value)
}
