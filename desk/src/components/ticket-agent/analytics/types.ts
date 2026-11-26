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
  agents_involved: { email: string; image: string; name: string }[];
  churn: { sla_changes: number; team_changes: number };
}

export interface TicketAnalytics {
  has_sla: boolean;
  timeline: TimelineNode[];
  metrics: AnalyticsMetrics;
  events: TimelineEvent[];
  summary: AnalyticsSummary;
}

// a dot on the rail; isDeadline draws it as a short vertical tick instead
export interface RailNode {
  kind: "node";
  colorClass: string;
  tooltip: string[];
  isDeadline?: boolean;
  label?: RailLabel | undefined;
}

// isMilestone marks a label whose subtitle carries a full date, which is what
// hideRepeatedDates rewrites
export interface RailLabel {
  title?: string;
  subtitle?: string | undefined;
  isMilestone?: boolean;
}

// the leg between two dots; duration is a measurement, caption is a state note
export interface RailLine {
  kind: "line";
  colorClass: string;
  width: number;
  isGrowing?: boolean;
  caption?: string;
  duration?: string | undefined;
  isSlowest?: boolean;
}

// a node that belongs at its own timestamp rather than at a fixed rail position
export interface RailMarker {
  at: string;
  build: () => RailNode;
  isDeadline?: boolean;
  // shown when a deadline lands immediately before this marker, which makes the
  // leg between them pure overtime rather than an idle stretch
  overtime?: string | undefined;
}

export type RailSegment = RailNode | RailLine;
export type LineOptions = Omit<RailLine, "kind" | "colorClass">;
