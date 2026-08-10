export interface TimelineBadge {
  text: string;
  tone: "green" | "red" | "amber" | "gray";
}

export interface TimelineNode {
  key: "created" | "first_response" | "hold" | "resolution";
  state: "done" | "breach" | "pending" | "hold";
  timestamp: string | null;
  badge: TimelineBadge | null;
  eta?: string | null;
  took?: number | null;
  target?: number | null;
  active?: boolean;
  window?: { start: string; end: string | null } | null;
}

export interface TimelineEvent {
  side: "customer" | "agent";
  at: string;
  sender: string;
  sender_name: string;
  wait_seconds: number | null;
}

export interface AnalyticsMetrics {
  avg_agent_gap: number | null;
  avg_customer_gap: number | null;
  hold_time: number | null;
}

export interface AnalyticsSummary {
  customer_messages: number;
  agent_messages: number;
  internal_comments: number;
  agents_involved: string[];
  churn: { sla_changes: number; team_changes: number };
}

export interface TicketAnalytics {
  has_sla: boolean;
  timeline: TimelineNode[];
  metrics: AnalyticsMetrics;
  events: TimelineEvent[];
  summary: AnalyticsSummary;
}

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
