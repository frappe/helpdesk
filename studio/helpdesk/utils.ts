import { dayjs } from 'frappe-ui'

// The portal's shared helpers, one home each — the same shape as desk/src/utils.ts.
// Three duration formats coexist on purpose: a list chip, the sidebar's SLA wording
// and a message byline each read differently, exactly as they do in the agent portal.

export function parseJson(value: unknown, fallback: any = undefined) {
  if (!value) return fallback
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value) ?? fallback
  } catch {
    return fallback
  }
}

/** A JSON-string field that should hold an array (`_assign`, `_seen`, filters…). */
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

/** `shortDuration` from desk/src/utils.ts — compact, direction-agnostic: "2 days 3h". */
export function shortDuration(target: string) {
  const seconds = Math.abs(dayjs(target).diff(dayjs(), 'second'))
  if (seconds >= DAY) {
    const days = Math.floor(seconds / DAY)
    const hours = Math.floor((seconds % DAY) / HOUR)
    const label = `${days} ${days === 1 ? 'day' : 'days'}`
    return hours ? `${label} ${hours}h` : label
  }
  if (seconds >= HOUR) {
    const hours = Math.floor(seconds / HOUR)
    const minutes = Math.floor((seconds % HOUR) / MINUTE)
    return minutes ? `${hours}h ${minutes}m` : `${hours}h`
  }
  return `${Math.floor(seconds / MINUTE)}m`
}

// The two most significant units, as `formatSeconds` words them in the agent portal's
// analytics: "2d 9h", "44m". Never four — and never trailing seconds on anything larger,
// because a countdown that only re-renders on load reads as a frozen timer when it shows
// them (the reasoning behind `coarseDuration` in desk's useSLA.ts).
export function compactDuration(seconds: number) {
  return (
    compactUnits(seconds)
      .map(([value, unit]) => `${value}${unit}`)
      .join(' ') || '0s'
  )
}

/** The largest unit with anything in it, plus the one below it — and only that one, so a
 *  span of 83 days and 59 minutes reads as "83 days" rather than skipping the empty hours
 *  to pair two units that were never adjacent. */
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

// `prettyDate` from desk/src/utils.ts, not dayjs's own `fromNow`: the agent portal
// words a week as a week where dayjs would still be counting days.
export function timeAgo(value: string) {
  const seconds = dayjs().diff(dayjs(value), 'second')
  const days = Math.floor(seconds / DAY)
  if (days < 1) return withinDay(seconds)
  if (days < 2) return 'Yesterday'
  return olderThanDay(days)
}

function withinDay(seconds: number) {
  if (seconds < 60) return 'Just now'
  if (seconds < 120) return '1 minute ago'
  if (seconds < HOUR) return `${Math.floor(seconds / MINUTE)} minutes ago`
  if (seconds < 2 * HOUR) return '1 hour ago'
  return `${Math.floor(seconds / HOUR)} hours ago`
}

function olderThanDay(days: number) {
  if (days < 7) return `${days} days ago`
  if (days < 14) return '1 week ago'
  if (days < 31) return `${Math.floor(days / 7)} weeks ago`
  if (days < 62) return '1 month ago'
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  if (days < 730) return '1 year ago'
  return `${Math.floor(days / 365)} years ago`
}
