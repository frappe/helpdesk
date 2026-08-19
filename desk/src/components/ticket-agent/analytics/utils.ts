/** Duration as at most two units, never decimal hours: "2h 30m", "45m"; sub-minute rounds up to "1m" */
export function formatSeconds(
  seconds: number | null | undefined
): string | null {
  if (seconds === null || seconds === undefined || seconds < 0) return null;
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days) return hours ? `${days}d ${hours}h` : `${days}d`;
  if (hours) return minutes ? `${hours}h ${minutes}m` : `${hours}h`;
  if (minutes) return `${minutes}m`;
  return "1m";
}
