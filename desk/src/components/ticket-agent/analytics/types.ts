export interface TimelineBadge {
  text: string;
  tone: "green" | "red" | "amber" | "gray";
}

export interface TimelineNode {
  key: "created" | "first_response" | "hold" | "exchanges" | "resolution";
  state: "done" | "breach" | "pending" | "hold";
  timestamp: string | null;
  badge: TimelineBadge | null;
  eta?: string | null;
  took?: number | null;
  target?: number | null;
  leg_label?: string;
  progress?: number | null;
  active?: boolean;
  window?: { start: string; end: string | null } | null;
  count?: number;
  range?: string;
}

export interface GapRow {
  replied_at: string;
  agent: string;
  gap_seconds: number;
}

export interface AnalyticsMetrics {
  avg_agent_gap: number | null;
  resolution_time: number | null;
  longest_agent_silence: number | null;
}

export interface AnalyticsSummary {
  customer_messages: number;
  agent_messages: number;
  total_exchanges: number;
  internal_comments: number;
  agents_involved: { user: string; full_name: string }[];
  churn: { sla_changes: number; team_changes: number; reassignments: number };
}

export interface TicketAnalytics {
  has_sla: boolean;
  timeline: TimelineNode[];
  metrics: AnalyticsMetrics;
  gaps: GapRow[];
  first_response_target: number | null;
  summary: AnalyticsSummary;
}

/** Duration as at most two units, never decimal hours: "2h 30m", "45m", "<1m" */
export function formatSeconds(seconds: number | null | undefined): string | null {
  if (seconds === null || seconds === undefined || seconds < 0) return null;
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days) return hours ? `${days}d ${hours}h` : `${days}d`;
  if (hours) return minutes ? `${hours}h ${minutes}m` : `${hours}h`;
  if (minutes) return `${minutes}m`;
  return "<1m";
}
