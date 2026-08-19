<template>
  <div
    class="rounded-md border border-outline-gray-1 bg-surface-base flex flex-col gap-10"
  >
    <div class="flex items-center px-4 pt-4">
      <h3 class="text-lg font-semibold text-ink-gray-8">
        {{ __("Ticket Timeline") }}
      </h3>
    </div>
    <div class="relative mx-4">
      <div
        v-show="showLeftFade"
        class="pointer-events-none absolute inset-y-0 left-0 z-10 w-10 bg-gradient-to-r from-[var(--surface-base)] to-transparent"
      />
      <div
        v-show="showRightFade"
        class="pointer-events-none absolute inset-y-0 right-0 z-10 w-10 bg-gradient-to-l from-[var(--surface-base)] to-transparent"
      />
      <div
        ref="scroller"
        class="overflow-x-auto hide-scrollbar"
        @scroll.passive="updateScrollFades"
      >
        <div
          ref="rail"
          class="flex w-max min-w-full items-start pl-12 pr-16 pb-16 pt-8"
        >
          <template v-for="(segment, index) in segments" :key="index">
            <Tooltip
              v-if="segment.kind === 'node'"
              :hover-delay="0.2"
              arrow-class="!hidden"
            >
              <span
                class="group relative flex-none rounded-full before:absolute before:-inset-2 before:content-['']"
                :class="[
                  segment.colorClass,
                  segment.isDeadline ? '-mt-0.5 h-3 w-[3px]' : 'size-2',
                ]"
              >
                <span
                  v-if="segment.label"
                  class="absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-center"
                  :class="[
                    index === 0 ? 'rail-first-label' : '',
                    segment.isDeadline ? 'top-[18px]' : 'top-4',
                  ]"
                >
                  <b
                    v-if="segment.label.title"
                    class="block text-sm text-ink-gray-8"
                  >
                    {{ segment.label.title }}
                  </b>
                  <span
                    v-if="segment.label.subtitle"
                    class="text-xs text-ink-gray-5"
                  >
                    {{ segment.label.subtitle }}
                  </span>
                </span>
              </span>
              <template v-if="segment.tooltip.length" #body>
                <div
                  class="space-y-1.5 rounded-md border border-outline-gray-1 bg-surface-elevation-2 px-3 py-2 shadow-sm"
                >
                  <span
                    v-for="line in segment.tooltip"
                    :key="line"
                    class="block whitespace-nowrap text-xs text-ink-gray-6 first:text-ink-gray-8"
                  >
                    {{ line }}
                  </span>
                </div>
              </template>
            </Tooltip>
            <span
              v-else
              class="relative mt-[3px] h-0.5 rounded-full"
              :class="[
                segment.colorClass,
                segment.isGrowing ? '' : 'flex-none',
              ]"
              :style="
                segment.isGrowing
                  ? { flex: `1 0 ${segment.width}px` }
                  : { width: `${segment.width}px` }
              "
            >
              <span
                v-if="segment.caption"
                class="absolute bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs capitalize tracking-wide text-ink-gray-4"
              >
                {{ segment.caption }}
              </span>
              <span
                v-if="segment.duration"
                class="absolute bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs text-ink-gray-6"
              >
                {{ segment.duration }}
              </span>
            </span>
          </template>
        </div>
      </div>
    </div>
    <div
      class="flex flex-wrap gap-x-4 gap-y-1 px-4 pb-4 text-xs text-ink-gray-5"
    >
      <span
        v-for="item in LEGEND"
        :key="item.label"
        class="flex items-center gap-1.5"
      >
        <span class="size-2 rounded-full" :class="item.colorClass" />
        {{ item.label }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { dayjsLocal, Tooltip } from "frappe-ui";
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import type {
  LineOptions,
  RailLabel,
  RailLine,
  RailMarker,
  RailNode,
  RailSegment,
  TimelineEvent,
  TimelineNode,
} from "./types";
import { formatSeconds } from "./utils";

const GREEN = "bg-[var(--ink-green-6)]";
const RED = "bg-[var(--ink-red-6)]";
const BLUE = "bg-[var(--ink-blue-6)]";
const CUSTOMER = "bg-[var(--outline-gray-4)]";
const PENDING = "bg-[var(--ink-gray-7)]";
const CHAIN = "bg-[var(--outline-gray-2)]";
const IDLE =
  "bg-[repeating-linear-gradient(90deg,var(--outline-gray-2)_0_5px,transparent_5px_11px)]";
const PAUSE =
  "bg-[repeating-linear-gradient(90deg,var(--ink-blue-6)_0_7px,transparent_7px_13px)]";
const OVERDUE =
  "bg-[repeating-linear-gradient(90deg,var(--ink-red-6)_0_5px,transparent_5px_11px)]";
const TODAY =
  "bg-[var(--surface-base)] border-[1.5px] border-[var(--outline-gray-4)]";

const LEGEND = [
  { colorClass: GREEN, label: __("SLA met") },
  { colorClass: RED, label: __("SLA missed / longest wait") },
  { colorClass: CUSTOMER, label: __("Customer message") },
  { colorClass: BLUE, label: __("Agent reply") },
];

const props = defineProps<{
  timeline: TimelineNode[];
  events: TimelineEvent[];
}>();

const scroller = ref<HTMLElement>();
const rail = ref<HTMLElement>();
const showLeftFade = ref(false);
const showRightFade = ref(false);

const milestones = computed(() => {
  const byKey: Partial<Record<TimelineNode["key"], TimelineNode>> = {};
  props.timeline.forEach((node) => (byKey[node.key] = node));
  return byKey;
});

const respondedAt = computed(
  () => milestones.value.first_response?.timestamp ?? null
);

// with no reply at all, the missed deadline stands in for the reply time
const overdueDeadline = computed(() => {
  const firstResponse = milestones.value.first_response;
  const isOverdue = !respondedAt.value && firstResponse?.state === "breach";
  return isOverdue ? firstResponse?.eta ?? null : null;
});

// the milestone sits at its chronological spot: customer messages sent before
// the first response (or its missed deadline) stay on its left
const eventsBeforeMilestone = computed(() => {
  const boundary = respondedAt.value ?? overdueDeadline.value;
  if (!boundary) return props.events;
  return props.events.filter(
    (event) => !dayjsLocal(event.at).isAfter(dayjsLocal(boundary))
  );
});

const eventsAfterMilestone = computed(() =>
  props.events.slice(eventsBeforeMilestone.value.length)
);

// the resolution sits at its own moment on the rail, not pinned to the end:
// its deadline is drawn only when it was missed, exactly like the first response
const resolutionMarkers = computed(() => {
  const resolution = milestones.value.resolution;
  if (milestones.value.hold?.active || !resolution) return [];
  const markers: RailMarker[] = [];
  if (resolution.state === "breach" && resolution.eta)
    markers.push({
      at: resolution.eta,
      build: () => getResolutionDueNode(resolution),
      isDeadline: true,
    });
  if (resolution.timestamp)
    markers.push({
      at: resolution.timestamp,
      build: () => getResolvedNode(resolution),
      overtime: getOvertimeLabel(resolution),
    });
  return markers;
});

const longestWait = computed(() => {
  const waits = props.events
    .map((event) => event.wait_seconds)
    .filter((wait): wait is number => wait != null);
  return waits.length > 1 ? Math.max(...waits) : 0;
});

const segments = computed<RailSegment[]>(() => {
  const created = milestones.value.created;
  const firstResponse = milestones.value.first_response;
  const result: RailSegment[] = [
    {
      kind: "node",
      colorClass: CUSTOMER,
      tooltip: getMilestoneTooltip(created),
      label: getLabel(__("Created"), formatDateTime(created?.timestamp)),
    },
    ...getEventSegments(eventsBeforeMilestone.value, created?.timestamp, null),
  ];
  if (firstResponse) result.push(...getFirstResponseSegments(firstResponse));
  const markers = [...resolutionMarkers.value];
  if (respondedAt.value)
    result.push(
      ...getEventSegments(
        eventsAfterMilestone.value,
        respondedAt.value,
        eventsBeforeMilestone.value.at(-1) ?? null,
        markers
      )
    );
  else if (overdueDeadline.value)
    result.push(
      ...getOverdueTailSegments(
        eventsAfterMilestone.value,
        overdueDeadline.value,
        markers
      )
    );
  result.push(...drainMarkers(markers, null, IDLE));
  if (!resolutionMarkers.value.length) result.push(...getEndingSegments());
  hideRepeatedDates(result);
  preventLabelOverlap(result);
  return result;
});

function getFirstResponseSegments(node: TimelineNode): RailSegment[] {
  if (node.state === "breach" && !node.timestamp && node.eta)
    return getOverdueStartSegments(node);

  const duration = formatSeconds(node.took) || undefined;
  const isLate = node.state === "breach" && Boolean(node.timestamp);
  // an overshoot that swallows the whole duration leaves no window to split
  const isSplit = isLate && Boolean(node.took && node.target);
  let leg: RailSegment[];
  if (node.state === "done")
    leg = [getLine(GREEN, { width: 120, isGrowing: true, duration })];
  else if (isSplit) leg = getBreachSplitSegments(node);
  else if (node.state === "breach")
    leg = [getLine(RED, { width: 130, isGrowing: true, duration })];
  else leg = [getLine(IDLE, { width: 120, isGrowing: true })];

  const colorClass =
    node.state === "done" ? GREEN : node.state === "breach" ? RED : PENDING;
  return [
    ...leg,
    {
      kind: "node",
      colorClass,
      tooltip: getMilestoneTooltip(node),
      label: getLabel(
        isLate ? __("Responded late") : __("First response"),
        getMilestoneSubtitle(node)
      ),
    },
  ];
}

function getMilestoneSubtitle(node: TimelineNode): string {
  if (node.timestamp) return formatDateTime(node.timestamp);
  return node.eta ? getDueLabel(node.eta) : __("pending");
}

// a breached milestone splits its leg at the deadline: green for the allowed
// window, a tick where the SLA expired, red for the overtime
function getBreachSplitSegments(node: TimelineNode): RailSegment[] {
  const took = node.took as number;
  const target = node.target as number;
  const allowed = Math.min(
    126,
    Math.max(24, Math.round((150 * target) / took))
  );
  return [
    getLine(GREEN, {
      width: allowed,
      duration: formatSeconds(target) || undefined,
    }),
    getDeadlineNode(node.eta, __("First response due")),
    getLine(RED, {
      width: 150 - allowed,
      isGrowing: true,
      duration: getOvertimeLabel(node),
    }),
  ];
}

// the tick carries the commitment, never the verdict: the node that follows it
// says what actually happened, or Today says nothing has
function getDeadlineNode(
  eta: string | null | undefined,
  title: string
): RailNode {
  const node: RailNode = {
    kind: "node",
    colorClass: RED,
    isDeadline: true,
    tooltip: [],
  };
  if (eta) node.label = getLabel(title, formatDateTime(eta) ?? "");
  return node;
}

// an overdue first response has no reply node: the deadline tick opens a red
// dashed stretch that getOverdueTailSegments closes at a Today marker
function getOverdueStartSegments(node: TimelineNode): RailSegment[] {
  const deadline = getDeadlineNode(node.eta, __("First response overdue"));
  deadline.tooltip = getMilestoneTooltip(node);
  return [
    getLine(GREEN, {
      width: 120,
      duration: formatSeconds(node.target) || undefined,
    }),
    deadline,
  ];
}

// customer nudges after the deadline sit on the red stretch: the wait only
// ends when an agent replies, and no agent reply can exist in this state
function getOverdueTailSegments(
  events: TimelineEvent[],
  deadline: string,
  markers: RailMarker[]
): RailSegment[] {
  const result: RailSegment[] = [];
  let previousDay = dayjsLocal(deadline).format("MMM D");
  let previousYear = dayjsLocal(deadline).year();
  for (const event of events) {
    const at = dayjsLocal(event.at);
    const day = at.format("MMM D");
    result.push(...drainMarkers(markers, event.at, OVERDUE));
    result.push(getLine(OVERDUE, { width: 72, isGrowing: true }));
    result.push(
      getEventNode(
        event,
        day !== previousDay ? getDayTitle(at, previousYear) : undefined
      )
    );
    previousDay = day;
    previousYear = at.year();
  }
  result.push(...drainMarkers(markers, null, OVERDUE));
  result.push(getLine(OVERDUE, { width: 140, isGrowing: true }));
  result.push({
    kind: "node",
    colorClass: TODAY,
    tooltip: [],
    label: getLabel(__("Today"), dayjsLocal().format("MMM D")),
  });
  return result;
}

// pops every marker due on or before `until` (all of them when it is null),
// so the caller stays a plain chronological walk over its own events
function drainMarkers(
  markers: RailMarker[],
  until: string | null,
  colorClass: string
): RailSegment[] {
  const result: RailSegment[] = [];
  // two markers draining together means no event fell between them
  let isAfterDeadline = false;
  while (
    markers.length &&
    (!until || !dayjsLocal(markers[0].at).isAfter(dayjsLocal(until)))
  ) {
    const marker = markers.shift() as RailMarker;
    result.push(
      isAfterDeadline && marker.overtime
        ? getLine(RED, {
            width: 90,
            isGrowing: true,
            duration: marker.overtime,
          })
        : getLine(colorClass, { width: 64, isGrowing: true })
    );
    result.push(marker.build());
    isAfterDeadline = Boolean(marker.isDeadline);
  }
  return result;
}

function getResolutionDueNode(resolution: TimelineNode): RailNode {
  return {
    kind: "node",
    colorClass: RED,
    isDeadline: true,
    tooltip: getMilestoneTooltip(resolution),
    label: getLabel(
      resolution.timestamp ? __("Resolution due") : __("Resolution overdue"),
      formatDateTime(resolution.eta as string)
    ),
  };
}

function getResolvedNode(resolution: TimelineNode): RailNode {
  const tooltip = getMilestoneTooltip(resolution);
  const hold = milestones.value.hold;
  if (hold?.badge?.text) tooltip.push(hold.badge.text);
  return {
    kind: "node",
    colorClass: resolution.state === "done" ? GREEN : RED,
    tooltip,
    label: getLabel(
      getResolutionTitle(resolution),
      formatDateTime(resolution.timestamp as string)
    ),
  };
}

function getOvertimeLabel(node: TimelineNode): string | undefined {
  const overtime = formatSeconds((node.took ?? 0) - (node.target ?? 0));
  return overtime ? `+${overtime}` : undefined;
}

function getEventSegments(
  events: TimelineEvent[],
  startAt: string | null | undefined,
  carriedEvent: TimelineEvent | null,
  markers: RailMarker[] = []
): RailSegment[] {
  const result: RailSegment[] = [];
  let previousEvent = carriedEvent;
  let isGroupStart = true;
  let previousDay = startAt ? dayjsLocal(startAt).format("MMM D") : "";
  let previousYear = dayjsLocal(startAt ?? undefined).year();
  for (const event of events) {
    const at = dayjsLocal(event.at);
    const day = at.format("MMM D");
    const isNewDay = day !== previousDay;
    const drained = drainMarkers(markers, event.at, IDLE);
    if (drained.length) {
      result.push(...drained);
      previousEvent = null;
      isGroupStart = true;
    }
    result.push(getConnectorLine(previousEvent, event, isGroupStart));
    result.push(
      getEventNode(event, isNewDay ? getDayTitle(at, previousYear) : undefined)
    );
    previousDay = day;
    previousYear = at.year();
    previousEvent = event;
    isGroupStart = false;
  }
  return result;
}

// a day label carries its year when it differs from the last one on the rail
function getDayTitle(
  at: ReturnType<typeof dayjsLocal>,
  previousYear: number
): string {
  return at.year() === previousYear
    ? at.format("MMM D")
    : at.format("MMM D, YYYY");
}

function getConnectorLine(
  previousEvent: TimelineEvent | null,
  event: TimelineEvent,
  isGroupStart: boolean
): RailLine {
  const answersCustomer =
    event.side === "agent" &&
    event.wait_seconds != null &&
    previousEvent?.side === "customer";
  if (answersCustomer) return getWaitLine(event.wait_seconds as number);
  if (isGroupStart || !previousEvent)
    return getLine(IDLE, { width: 64, isGrowing: true });
  if (previousEvent.side === event.side) return getLine(CHAIN, { width: 26 });
  const days = dayjsLocal(event.at)
    .startOf("day")
    .diff(dayjsLocal(previousEvent.at).startOf("day"), "day");
  if (!days) return getLine(IDLE, { width: 32 });
  const caption = days === 1 ? __("next day") : __("{0} days", String(days));
  return getLine(IDLE, { width: days === 1 ? 76 : 96, caption });
}

function getWaitLine(wait: number): RailLine {
  const width = Math.max(24, Math.min(130, Math.round((wait / 60) * 1.2)));
  const isSlowest = longestWait.value > 0 && wait === longestWait.value;
  return getLine(isSlowest ? RED : BLUE, {
    width,
    duration: formatSeconds(wait) || undefined,
    isSlowest,
  });
}

function getEventNode(event: TimelineEvent, dayTitle?: string): RailNode {
  const isSlowest =
    event.side === "agent" &&
    longestWait.value > 0 &&
    event.wait_seconds === longestWait.value;
  const colorClass = event.side === "agent" ? BLUE : CUSTOMER;
  return {
    kind: "node",
    colorClass: isSlowest ? RED : colorClass,
    tooltip: getEventTooltip(event, isSlowest),
    label: dayTitle
      ? { title: dayTitle, subtitle: dayjsLocal(event.at).format("h:mm a") }
      : undefined,
  };
}

function getEventTooltip(event: TimelineEvent, isSlowest: boolean): string[] {
  const who = event.sender_name || event.sender;
  if (event.side === "customer")
    return [__("Customer message"), formatDateTime(event.at)];
  const lines = [__("{0} replied", who)];
  if (event.wait_seconds != null) {
    const took = formatSeconds(event.wait_seconds) || "0m";
    lines.push(
      isSlowest ? __("{0} · longest wait", took) : __("{0} wait", took)
    );
  } else {
    lines.push(__("Follow-up"));
  }
  lines.push(formatDateTime(event.at));
  return lines;
}

function getEndingSegments(): RailSegment[] {
  const hold = milestones.value.hold;
  const resolution = milestones.value.resolution;
  if (hold?.active) return getHoldSegments(hold, resolution);
  if (!resolution) return [];

  const tooltip = getMilestoneTooltip(resolution);
  if (hold?.badge?.text) tooltip.push(hold.badge.text);
  const isResolved =
    resolution.state === "done" ||
    (resolution.state === "breach" && resolution.timestamp);
  if (isResolved)
    return [
      getLine(IDLE, { width: 48, isGrowing: true }),
      {
        kind: "node",
        colorClass: resolution.state === "done" ? GREEN : RED,
        tooltip,
        label: getLabel(
          getResolutionTitle(resolution),
          resolution.timestamp
            ? formatDateTime(resolution.timestamp)
            : undefined
        ),
      },
    ];

  // a missed deadline is drawn as a marker on the rail, so only a live
  // countdown reaches here
  return [
    getLine(IDLE, { width: 120, isGrowing: true }),
    {
      kind: "node",
      colorClass: PENDING,
      tooltip,
      label: getLabel(__("Resolution"), getMilestoneSubtitle(resolution)),
    },
  ];
}

function getHoldSegments(
  hold: TimelineNode,
  resolution?: TimelineNode
): RailSegment[] {
  const result: RailSegment[] = [
    getLine(PAUSE, {
      width: 120,
      isGrowing: true,
      caption: __("clock stopped"),
    }),
    {
      kind: "node",
      colorClass: BLUE,
      tooltip: hold.took
        ? [__("Paused {0} so far", formatSeconds(hold.took) ?? "")]
        : [],
      label: getLabel(
        __("SLA paused"),
        hold.timestamp
          ? __("since {0}", formatDateTime(hold.timestamp) ?? "")
          : undefined
      ),
    },
  ];
  if (!resolution) return result;
  const tooltip = getMilestoneTooltip(resolution);
  tooltip.push(__("clock resumes when the ticket reopens"));
  result.push(getLine(IDLE, { width: 110, isGrowing: true }));
  result.push({
    kind: "node",
    colorClass: PENDING,
    tooltip,
    label: getLabel(__("Resolution"), __("pending")),
  });
  return result;
}

// a label drops whatever the rail has already established: the date when the
// previous label shared it, so "due at Jul 17, 10:02 am" becomes "due at 10:02
// am", and the year until it changes, so only the first 2025 label carries it
function hideRepeatedDates(segments: RailSegment[]): void {
  let previousDay = "";
  let previousYear = String(dayjsLocal().year());
  for (const segment of segments) {
    if (segment.kind !== "node" || !segment.label) continue;
    if (!segment.label.isMilestone) {
      const [, day, year] =
        segment.label.title?.match(/^(\w{3} \d{1,2})(?:, (\d{4}))?$/) ?? [];
      previousDay = day || segment.label.title || previousDay;
      if (year) previousYear = year;
      continue;
    }
    const [, prefix, day, year, time] =
      segment.label.subtitle?.match(
        /^(.*?)(\w{3} \d{1,2})(?:, (\d{4}))?, (.+)$/
      ) ?? [];
    if (!day || !time) {
      // a bare date like the Today marker still breaks the run
      previousDay = segment.label.subtitle || previousDay;
      continue;
    }
    const isNewYear = Boolean(year) && year !== previousYear;
    if (year) previousYear = year;
    if (day === previousDay && !isNewYear) {
      segment.label.subtitle = prefix + time;
      continue;
    }
    previousDay = day;
    segment.label.subtitle = isNewYear
      ? `${prefix}${day}, ${year}, ${time}`
      : `${prefix}${day}, ${time}`;
  }
}

// labels are centered under their dots, so the line span between two labeled
// nodes must fit both label halves or the texts collide
function preventLabelOverlap(segments: RailSegment[]): void {
  let previousHalf = 0;
  let span = Infinity;
  let lastLine: RailLine | null = null;
  for (const segment of segments) {
    if (segment.kind === "line") {
      span += segment.width;
      lastLine = segment;
    } else if (segment.label) {
      const needed = previousHalf + getLabelHalfWidth(segment.label) + 12;
      if (lastLine && span < needed) lastLine.width += needed - span;
      previousHalf = getLabelHalfWidth(segment.label);
      span = 0;
      lastLine = null;
    } else {
      span += 8;
    }
  }
}

// rough text metrics: ~7px per text-sm char, ~6px per text-xs char
function getLabelHalfWidth(label: RailLabel): number {
  const title = (label.title?.length ?? 0) * 7;
  const subtitle = (label.subtitle?.length ?? 0) * 6;
  return Math.max(title, subtitle) / 2;
}

// milestone labels already show name and time below the dot, so the hover
// only carries what the label does not: the SLA verdict
function getMilestoneTooltip(node?: TimelineNode): string[] {
  return node?.badge?.text ? [node.badge.text] : [];
}

function getResolutionTitle(resolution: TimelineNode): string {
  if (resolution.state === "breach" && resolution.timestamp)
    return __("Resolved late");
  if (resolution.state === "done")
    return resolution.timestamp ? __("Resolved") : __("Closed");
  return __("Resolution");
}

function getLabel(title: string, subtitle?: string): RailLabel {
  return { title, subtitle, isMilestone: true };
}

function getLine(colorClass: string, options: LineOptions): RailLine {
  return { kind: "line", colorClass, ...options };
}

function getDueLabel(eta: string): string {
  return __("due {0}", formatDateTime(eta));
}

function formatDateTime(timestamp: string): string;
function formatDateTime(timestamp?: string | null): string | undefined;
function formatDateTime(timestamp?: string | null): string | undefined {
  if (!timestamp) return undefined;
  const at = dayjsLocal(timestamp);
  return at.year() === dayjsLocal().year()
    ? at.format("MMM D, h:mm a")
    : at.format("MMM D, YYYY, h:mm a");
}

// the first label is centered under its dot but its left edge must sit on the
// card's content axis, so the rail's left padding is half the label's width
function alignFirstLabel(): void {
  const element = rail.value;
  const label = element?.querySelector<HTMLElement>(".rail-first-label");
  if (!element) return;
  element.style.paddingLeft = label
    ? `${Math.max(0, Math.round(label.offsetWidth / 2 - 4))}px`
    : "";
}

function updateScrollFades(): void {
  const element = scroller.value;
  if (!element) return;
  const overflow = element.scrollWidth - element.clientWidth;
  showLeftFade.value = overflow > 12 && element.scrollLeft > 4;
  showRightFade.value = overflow > 12 && element.scrollLeft < overflow - 4;
}

// reka-ui only dismisses tooltips on window scroll, and this app scrolls
// inner containers, so popovers stay stranded when their anchor moves; once
// a gesture passes trackpad jitter range, close them via reka's own
// close-others signal, the "tooltip.open" window event
const scrollPositions = new WeakMap<Element, number>();
let gestureDelta = 0;
let lastScrollAt = 0;

function handleWindowScroll(event: Event): void {
  const element =
    event.target instanceof Element ? event.target : document.scrollingElement;
  if (!element) return;
  const position = element.scrollLeft + element.scrollTop;
  const previous = scrollPositions.get(element);
  scrollPositions.set(element, position);
  const now = performance.now();
  if (now - lastScrollAt > 200) gestureDelta = 0;
  lastScrollAt = now;
  if (previous == null) return;
  gestureDelta += Math.abs(position - previous);
  if (gestureDelta > 8) window.dispatchEvent(new CustomEvent("tooltip.open"));
}

watch(segments, () =>
  nextTick(() => {
    alignFirstLabel();
    updateScrollFades();
  })
);

onMounted(() => {
  alignFirstLabel();
  updateScrollFades();
  window.addEventListener("scroll", handleWindowScroll, true);
});

onUnmounted(() =>
  window.removeEventListener("scroll", handleWindowScroll, true)
);
</script>
