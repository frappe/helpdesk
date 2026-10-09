import { Badge, Tooltip, dayjsLocal } from "frappe-ui";
import { h } from "vue";
import { __ } from "./translation";
import { shortDuration } from "./utils";

/** Tallest bars faded per level: High is fully solid, Low nearly empty. */
const FADED_BARS: Record<string, number> = { High: 0, Medium: 1, Low: 2 };

// Shortest first, so a bar's index from the top counts down.
const BARS = [
  { x: 0, y: 8, height: 4 },
  { x: 4, y: 4, height: 8 },
  { x: 8, y: 0, height: 12 },
];

export function PriorityIcon({ level }: { level: string }) {
  return level === "Urgent" ? urgentIcon() : levelBars(level);
}
PriorityIcon.props = ["level"];

// No SLA means nothing was promised, so there is nothing to report against.
export function responseBadge(row: any, due?: string) {
  if (!row.sla) return null;
  return slaBadge(row.first_responded_on, due, "amber");
}

export function resolutionBadge(row: any, due: string | undefined, paused: boolean) {
  if (!row.sla) return null;
  if (paused) return badge(__("Paused"), "blue");
  return slaBadge(row.resolution_date, due, "violet");
}

function urgentIcon() {
  const glyph = "fill-surface-gray-1";
  return h("svg", { class: "h-3.5 w-3.5", viewBox: "0 0 14 14", fill: "none" }, [
    h("rect", { width: 14, height: 14, rx: 4, class: "fill-ink-gray-6" }),
    h("rect", { x: 6.25, y: 3, width: 1.5, height: 4.75, rx: 0.75, class: glyph }),
    h("circle", { cx: 7, cy: 10, r: 0.9, class: glyph }),
  ]);
}

function levelBars(level: string) {
  const faded = FADED_BARS[level] ?? 0;
  const bars = BARS.map(({ x, y, height }, index) =>
    h("rect", {
      x,
      y,
      width: 2.5,
      height,
      rx: 0.5,
      class: BARS.length - 1 - index < faded ? "fill-ink-gray-3" : "fill-ink-gray-6",
    })
  );
  return h("svg", { class: "h-3 w-3", viewBox: "0 0 10 12", fill: "none" }, bars);
}

function slaBadge(metOn: string | undefined, due: string | undefined, countdownTheme: string) {
  // No target means it was never breached, so meeting it at all fulfils it.
  if (metOn) return outcomeBadge(!due || dayjsLocal(metOn).isBefore(dayjsLocal(due)));
  if (!due) return null;
  if (dayjsLocal(due).isBefore(dayjsLocal())) return outcomeBadge(false);
  return h(Tooltip, { text: dayjsLocal(due).format("LLLL") }, () =>
    badge(shortDuration(due), countdownTheme)
  );
}

function outcomeBadge(fulfilled: boolean) {
  return fulfilled ? badge(__("Fulfilled"), "gray") : badge(__("Failed"), "red");
}

function badge(label: string, theme: string) {
  return h(Badge, { label, theme, variant: "subtle" });
}
