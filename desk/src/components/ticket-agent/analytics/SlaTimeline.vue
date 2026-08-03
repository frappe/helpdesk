<template>
  <div class="rounded-lg border border-outline-gray-1 bg-surface-white">
    <div class="flex items-center gap-1.5 px-4 pt-4">
      <h3 class="text-lg font-semibold text-ink-gray-8">
        {{ __("SLA Timeline") }}
      </h3>
      <Tooltip :text="tooltip">
        <LucideInfo class="size-3.5 text-ink-gray-5" />
      </Tooltip>
    </div>
    <div class="p-16">
      <div class="flex items-start">
        <template v-for="(node, index) in timeline" :key="node.key">
          <div
            class="group relative flex w-3.5 flex-none flex-col items-center"
          >
            <div
              class="relative size-3.5 flex-none rounded-full after:absolute after:inset-[4.5px] after:rounded-full after:bg-surface-base after:content-['']"
              :class="dotClass[node.state]"
            />
            <div
              v-if="badgeFor(node)"
              class="invisible absolute bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap opacity-0 transition-opacity duration-150 group-hover:visible group-hover:opacity-100"
            >
              <Badge
                :label="badgeFor(node)!.text"
                :theme="badgeFor(node)!.tone"
                variant="subtle"
                size="sm"
              />
            </div>
            <div
              class="absolute left-1/2 top-[18px] w-40 -translate-x-1/2 text-center"
            >
              <b
                class="block whitespace-nowrap text-base font-medium text-ink-gray-8"
              >
                {{ labelFor(node) }}
              </b>
              <Tooltip :text="timeTooltip(node)">
                <span
                  class="mt-0.5 inline-block whitespace-pre text-sm tabular-nums"
                  :class="
                    node.state === 'pending'
                      ? 'text-ink-gray-4'
                      : 'text-ink-gray-5'
                  "
                >
                  {{ timeFor(node) }}
                </span>
              </Tooltip>
            </div>
          </div>
          <div
            v-if="index < timeline.length - 1"
            class="relative mt-[5px] h-1 flex-1"
            :class="segmentClass(index)"
            :style="segmentStyle(index)"
          >
            <span
              v-if="segmentLabel(index)"
              class="absolute bottom-3 left-1/2 -translate-x-1/2 whitespace-nowrap text-center"
            >
              <b
                v-if="segmentLabel(index)!.value"
                class="block text-base font-medium text-ink-gray-8"
              >
                {{ segmentLabel(index)!.value }}
              </b>
              <span
                v-if="segmentLabel(index)!.caption"
                class="text-xs tabular-nums text-ink-gray-6"
              >
                {{ segmentLabel(index)!.caption }}
              </span>
            </span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { dateFormat, dateTooltipFormat } from "@/utils";
import { Badge, dayjsLocal, Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideInfo from "~icons/lucide/info";
import { formatSeconds, TimelineBadge, TimelineNode } from "./types";

const props = defineProps<{ timeline: TimelineNode[]; hasSla: boolean }>();

const nodeTime = "MMM D, h:mm a";

// Figma icon/solid/stages donut: colored 14px ring, surface core
// arbitrary values: the espresso preset exposes ink-* for text and outline-*
// for borders only, so bg-ink-* utilities do not exist
const dotClass: Record<string, string> = {
  done: "bg-[var(--ink-green-6)]",
  hold: "bg-[var(--ink-blue-6)]",
  breach: "bg-[var(--ink-red-6)]",
  pending: "bg-[var(--outline-gray-3)]",
};

const tooltip = computed(() => {
  const first = props.timeline[0]?.timestamp;
  const last = [...props.timeline]
    .reverse()
    .find((n) => n.timestamp)?.timestamp;
  const range =
    first && last && !dayjsLocal(first).isSame(dayjsLocal(last), "day")
      ? `${dayjsLocal(first).format("MMM D")} – ${dayjsLocal(last).format(
          "MMM D"
        )}`
      : dayjsLocal(first).format("MMM D");
  const basis = props.hasSla ? __("business hours") : __("wall-clock, no SLA");
  return `${range} · ${basis}`;
});

// the first pending milestone owns the in-progress gradient; later pending
// legs stay gray so elapsed time is not double-drawn
const activePendingIndex = computed(() =>
  props.timeline.findIndex((n) => n.state === "pending" && n.progress != null)
);

function hasGradient(index: number): boolean {
  // a hold leg is always dashed blue, never a progress gradient
  if (props.timeline[index].state === "hold") return false;
  const next = props.timeline[index + 1];
  if (next.progress == null) return false;
  return next.state === "breach" || index + 1 === activePendingIndex.value;
}

function segmentClass(index: number): string {
  if (props.timeline[index].state === "hold")
    return "bg-[repeating-linear-gradient(90deg,var(--ink-blue-6)_0_8px,transparent_8px_14px)]";
  if (hasGradient(index)) return "";
  const next = props.timeline[index + 1];
  return next.state === "done" || next.state === "hold"
    ? "bg-[var(--ink-green-6)]"
    : "bg-[var(--outline-gray-2)]";
}

function segmentStyle(index: number): Record<string, string> {
  if (!hasGradient(index)) return {};
  const next = props.timeline[index + 1];
  const pct = Math.round((next.progress as number) * 100);
  const rest =
    next.state === "breach" ? "var(--ink-red-6)" : "var(--outline-gray-2)";
  return {
    background: `linear-gradient(90deg, var(--ink-green-6) 0 ${pct}%, ${rest} ${pct}% 100%)`,
  };
}

interface SegmentLabel {
  value?: string | null;
  caption: string;
}

function segmentLabel(index: number): SegmentLabel | undefined {
  // duration only; the node label below already says "On hold"
  const node = props.timeline[index];
  if (node.state === "hold") {
    return { value: formatSeconds(node.took ?? null), caption: "" };
  }
  if (hasGradient(index)) {
    return { caption: props.timeline[index + 1].leg_label || "" };
  }
  return undefined;
}

function badgeFor(node: TimelineNode): TimelineBadge | null {
  // hold duration lives above the segment, not in a badge
  if (node.key === "hold") return null;
  if (node.badge) return node.badge;
  if (node.state === "pending" && node.eta) {
    const seconds = dayjsLocal(node.eta).diff(dayjsLocal(), "second");
    return { text: __("Due in {0}", [formatSeconds(seconds)]), tone: "gray" };
  }
  return null;
}

function labelFor(node: TimelineNode): string {
  switch (node.key) {
    case "created":
      return __("Ticket created");
    case "first_response":
      return __("First response");
    case "hold":
      return __("SLA paused");
    case "exchanges":
      return __("{0} exchanges", [node.count]);
    default:
      if (node.state === "pending") return __("Resolution");
      if (node.state === "breach") return __("Resolved late");
      return node.timestamp ? __("Resolved") : __("Closed");
  }
}

function timeFor(node: TimelineNode): string {
  if (node.key === "exchanges") return node.range || "";
  if (node.key === "hold") return holdWindow(node);
  if (node.timestamp) return dayjsLocal(node.timestamp).format(nodeTime);
  if (node.state === "breach" && node.eta)
    return __("was due {0}", [dayjsLocal(node.eta).format(nodeTime)]);
  return __("pending");
}

function holdWindow(node: TimelineNode): string {
  if (!node.window) return "";
  const start = dayjsLocal(node.window.start);
  if (!node.window.end) return __("since {0}", [start.format(nodeTime)]);
  const end = dayjsLocal(node.window.end);
  if (end.isSame(start, "day"))
    return `${start.format(nodeTime)} – ${end.format("h:mm a")}`;
  // multi-day windows show dates only; exact times live in the tooltip
  return `${start.format("MMM D")} – ${end.format("MMM D")}`;
}

function timeTooltip(node: TimelineNode): string {
  if (node.key === "hold" && node.window?.end) {
    const start = dayjsLocal(node.window.start);
    const end = dayjsLocal(node.window.end);
    return `${start.format(nodeTime)} – ${end.format(nodeTime)}`;
  }
  return node.timestamp ? dateFormat(node.timestamp, dateTooltipFormat) : "";
}
</script>
