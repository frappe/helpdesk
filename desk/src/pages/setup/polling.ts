// Delays between status checks: 6 at 5s, 8 at 15s, 10 at 30s, then stop (about 7 minutes).
const SCHEDULE: [count: number, delayMs: number][] = [
  [6, 5000],
  [8, 15000],
  [10, 30000],
];

export const MAX_POLLS = SCHEDULE.reduce((total, [count]) => total + count, 0);

/** Wait before poll number `attempt` (from 0), or null once polling should stop. */
export function pollDelay(attempt: number): number | null {
  let remaining = attempt;
  for (const [count, delayMs] of SCHEDULE) {
    if (remaining < count) return delayMs;
    remaining -= count;
  }
  return null;
}
