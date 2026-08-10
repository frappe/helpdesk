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
        v-show="fadeLeft"
        class="pointer-events-none absolute inset-y-0 left-0 z-10 w-10 bg-gradient-to-r from-[var(--surface-base)] to-transparent"
      />
      <div
        v-show="fadeRight"
        class="pointer-events-none absolute inset-y-0 right-0 z-10 w-10 bg-gradient-to-l from-[var(--surface-base)] to-transparent"
      />
      <div
        ref="scroller"
        class="overflow-x-auto hide-scrollbar"
        @scroll.passive="updateFades"
      >
        <div
          ref="rail"
          class="flex w-max min-w-full items-start pl-12 pr-16 pb-16 pt-8"
        >
          <template v-for="(seg, index) in segments" :key="index">
            <Tooltip
              v-if="seg.kind === 'node'"
              :hover-delay="0.2"
              arrow-class="!hidden"
            >
              <span
                class="group relative flex-none rounded-full before:absolute before:-inset-2 before:content-['']"
                :class="[seg.cls, seg.tick ? '-mt-0.5 h-3 w-[3px]' : 'size-2']"
              >
                <span
                  v-if="seg.label"
                  class="absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-center"
                  :class="[
                    index === 0 ? 'rail-first-label' : '',
                    seg.tick ? 'top-[18px]' : 'top-4',
                  ]"
                >
                  <b
                    v-if="seg.label.title"
                    class="block text-sm text-ink-gray-8"
                  >
                    {{ seg.label.title }}
                  </b>
                  <span v-if="seg.label.sub" class="text-xs text-ink-gray-5">
                    {{ seg.label.sub }}
                  </span>
                </span>
              </span>
              <template v-if="seg.tip.length" #body>
                <div
                  class="space-y-1.5 rounded-md border border-outline-gray-1 bg-surface-elevation-2 px-3 py-2 shadow-sm"
                >
                  <span
                    v-for="line in seg.tip"
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
              :class="[seg.cls, seg.grow ? '' : 'flex-none']"
              :style="
                seg.grow
                  ? { flex: `1 0 ${seg.width}px` }
                  : { width: `${seg.width}px` }
              "
            >
              <span
                v-if="seg.over"
                class="absolute bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs capitalize tracking-wide text-ink-gray-4"
              >
                {{ seg.over }}
              </span>
              <span
                v-if="seg.wait"
                class="absolute bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs text-ink-gray-6"
              >
                {{ seg.wait }}
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
        v-for="item in legend"
        :key="item.label"
        class="flex items-center gap-1.5"
      >
        <span class="size-2 rounded-full" :class="item.cls" />
        {{ item.label }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { dayjsLocal, Tooltip } from "frappe-ui";
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { formatSeconds, TimelineEvent, TimelineNode } from "./types";

const props = defineProps<{
  timeline: TimelineNode[];
  events: TimelineEvent[];
}>();

const scroller = ref<HTMLElement>();
const rail = ref<HTMLElement>();
const fadeLeft = ref(false);
const fadeRight = ref(false);

// the first label is centered under its dot but its left edge must sit on the
// card's content axis, so the rail's left padding is half the label's width
function alignFirstLabel(): void {
  const el = rail.value;
  const label = el?.querySelector<HTMLElement>(".rail-first-label");
  if (!el) return;
  el.style.paddingLeft = label
    ? `${Math.max(0, Math.round(label.offsetWidth / 2 - 4))}px`
    : "";
}

// reka-ui only dismisses tooltips on window scroll, and this app scrolls
// inner containers, so popovers stay stranded when their anchor moves; once
// a gesture passes trackpad jitter range, close them via reka's own
// close-others signal, the "tooltip.open" window event
const scrollPositions = new WeakMap<Element, number>();
let gestureDelta = 0;
let lastScrollAt = 0;

function dismissPopoversOnScroll(event: Event): void {
  const el =
    event.target instanceof Element ? event.target : document.scrollingElement;
  if (!el) return;
  const position = el.scrollLeft + el.scrollTop;
  const previous = scrollPositions.get(el);
  scrollPositions.set(el, position);
  const now = performance.now();
  if (now - lastScrollAt > 200) gestureDelta = 0;
  lastScrollAt = now;
  if (previous == null) return;
  gestureDelta += Math.abs(position - previous);
  if (gestureDelta > 8) window.dispatchEvent(new CustomEvent("tooltip.open"));
}

function updateFades(): void {
  const el = scroller.value;
  if (!el) return;
  const overflow = el.scrollWidth - el.clientWidth;
  fadeLeft.value = overflow > 12 && el.scrollLeft > 4;
  fadeRight.value = overflow > 12 && el.scrollLeft < overflow - 4;
}

interface RailNode {
  kind: "node";
  cls: string;
  tip: string[];
  tick?: boolean;
  label?:
    | { title?: string; sub?: string | undefined; strong?: boolean }
    | undefined;
}

interface RailLine {
  kind: "line";
  cls: string;
  width: number;
  grow?: boolean;
  over?: string;
  wait?: string | undefined;
  slow?: boolean;
}

type RailSegment = RailNode | RailLine;

// arbitrary values: the espresso preset exposes ink-* for text and outline-*
// for borders only, so bg-ink-* utilities do not exist
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

const legend = [
  { cls: GREEN, label: __("SLA met") },
  { cls: RED, label: __("SLA missed / longest wait") },
  { cls: CUSTOMER, label: __("Customer message") },
  { cls: BLUE, label: __("Agent reply") },
];

const nodes = computed(() => {
  const byKey: Partial<Record<TimelineNode["key"], TimelineNode>> = {};
  props.timeline.forEach((n) => (byKey[n.key] = n));
  return byKey;
});

const maxWait = computed(() => {
  const waits = props.events
    .map((e) => e.wait_seconds)
    .filter((w): w is number => w != null);
  return waits.length > 1 ? Math.max(...waits) : 0;
});

const segments = computed<RailSegment[]>(() => {
  const segs: RailSegment[] = [];
  const created = nodes.value.created;
  const fr = nodes.value.first_response;
  segs.push({
    kind: "node",
    cls: CUSTOMER,
    tip: milestoneTip(created),
    label: label(__("Created"), fmtAt(created?.timestamp)),
  });
  // the milestone sits at its chronological spot: customer messages sent
  // before the first response (or its missed deadline) stay on its left
  const responded = fr?.timestamp;
  const overdueEta =
    !responded && fr?.state === "breach" ? fr.eta ?? null : null;
  const boundary = responded ?? overdueEta;
  const before = boundary
    ? props.events.filter(
        (e) => !dayjsLocal(e.at).isAfter(dayjsLocal(boundary))
      )
    : props.events;
  pushEvents(segs, before, created?.timestamp, null);
  if (fr) pushFirstResponse(segs, fr);
  const after = props.events.slice(before.length);
  if (responded) pushEvents(segs, after, responded, before.at(-1) ?? null);
  else if (overdueEta) pushOverdueTail(segs, after, overdueEta);
  pushEnding(segs);
  dedupeDayPrefixes(segs);
  widenCrowdedLegs(segs);
  return segs;
});

function pushFirstResponse(segs: RailSegment[], fr: TimelineNode): void {
  const took = formatSeconds(fr.took) || undefined;
  const split = Boolean(
    fr.state === "breach" && fr.timestamp && fr.took && fr.target
  );
  if (fr.state === "done")
    segs.push(line(GREEN, 120, { grow: true, wait: took }));
  else if (split) pushBreachSplit(segs, fr);
  else if (fr.state === "breach" && !fr.timestamp && fr.eta)
    return pushOverdueStart(segs, fr);
  else if (fr.state === "breach")
    segs.push(line(RED, 130, { grow: true, wait: took }));
  else segs.push(line(IDLE, 120, { grow: true }));
  const cls =
    fr.state === "done" ? GREEN : fr.state === "breach" ? RED : PENDING;
  const sub = fr.timestamp
    ? fmtAt(fr.timestamp)
    : fr.state === "breach" && fr.eta
    ? __("was due {0}", fmtAt(fr.eta) ?? "")
    : fr.eta
    ? dueLabel(fr.eta)
    : __("pending");
  segs.push({
    kind: "node",
    cls,
    tip: milestoneTip(fr),
    label: label(split ? __("Responded") : __("First response"), sub),
  });
}

// a breached milestone splits its leg at the deadline: green for the allowed
// window, a tick where the SLA expired, red for the overtime
function pushBreachSplit(segs: RailSegment[], node: TimelineNode): void {
  const took = node.took as number;
  const target = node.target as number;
  const green = Math.min(126, Math.max(24, Math.round((150 * target) / took)));
  segs.push(line(GREEN, green, { wait: formatSeconds(target) || undefined }));
  segs.push(deadlineTick(node.eta));
  segs.push(line(RED, 150 - green, { grow: true, wait: overtime(node) }));
}

function deadlineTick(eta?: string | null): RailNode {
  const seg: RailNode = { kind: "node", cls: RED, tick: true, tip: [] };
  if (eta)
    seg.label = label(__("First response"), __("due at {0}", fmtAt(eta) ?? ""));
  return seg;
}

// an overdue first response has no reply node: the deadline tick opens a red
// dashed stretch that pushOverdueTail closes at a Today marker
function pushOverdueStart(segs: RailSegment[], fr: TimelineNode): void {
  segs.push(line(GREEN, 120, { wait: formatSeconds(fr.target) || undefined }));
  const tick = deadlineTick(fr.eta);
  tick.tip = milestoneTip(fr);
  segs.push(tick);
}

// customer nudges after the deadline sit on the red stretch: the wait only
// ends when an agent replies, and no agent reply can exist in this state
function pushOverdueTail(
  segs: RailSegment[],
  events: TimelineEvent[],
  eta: string
): void {
  let prevDay = dayjsLocal(eta).format("MMM D");
  for (const event of events) {
    const day = dayjsLocal(event.at).format("MMM D");
    segs.push(line(OVERDUE, 72, { grow: true }));
    segs.push(eventNode(event, day !== prevDay ? day : undefined));
    prevDay = day;
  }
  segs.push(line(OVERDUE, 140, { grow: true }));
  segs.push({
    kind: "node",
    cls: TODAY,
    tip: [],
    label: label(__("Today"), dayjsLocal().format("MMM D")),
  });
}

function overtime(node: TimelineNode): string | undefined {
  const over = formatSeconds((node.took ?? 0) - (node.target ?? 0));
  return over ? `+${over}` : undefined;
}

function pushEvents(
  segs: RailSegment[],
  events: TimelineEvent[],
  startAt: string | null | undefined,
  carried: TimelineEvent | null
): void {
  let prev = carried;
  let atGroupStart = true;
  let prevDay = startAt ? dayjsLocal(startAt).format("MMM D") : "";
  for (const event of events) {
    const day = dayjsLocal(event.at).format("MMM D");
    const newDay = day !== prevDay;
    segs.push(connectorBefore(prev, event, atGroupStart));
    segs.push(eventNode(event, newDay ? day : undefined));
    prevDay = day;
    prev = event;
    atGroupStart = false;
  }
}

function connectorBefore(
  prev: TimelineEvent | null,
  event: TimelineEvent,
  groupStart: boolean
): RailLine {
  const answers =
    event.side === "agent" &&
    event.wait_seconds != null &&
    prev?.side === "customer";
  if (answers) return waitLine(event.wait_seconds as number);
  if (groupStart || !prev) return line(IDLE, 64, { grow: true });
  if (prev.side === event.side) return line(CHAIN, 26, {});
  const days = dayjsLocal(event.at)
    .startOf("day")
    .diff(dayjsLocal(prev.at).startOf("day"), "day");
  if (!days) return line(IDLE, 32, {});
  const over = days === 1 ? __("next day") : __("{0} days", String(days));
  return line(IDLE, days === 1 ? 76 : 96, { over });
}

function waitLine(wait: number): RailLine {
  const width = Math.max(24, Math.min(130, Math.round((wait / 60) * 1.2)));
  const slow = maxWait.value > 0 && wait === maxWait.value;
  return {
    kind: "line",
    cls: slow ? RED : BLUE,
    width,
    wait: formatSeconds(wait) || undefined,
    slow,
  };
}

function eventNode(event: TimelineEvent, newDay?: string): RailNode {
  const slow =
    event.side === "agent" &&
    maxWait.value > 0 &&
    event.wait_seconds === maxWait.value;
  return {
    kind: "node",
    cls: slow ? RED : event.side === "agent" ? BLUE : CUSTOMER,
    tip: eventTip(event, slow),
    label: newDay
      ? { title: newDay, sub: dayjsLocal(event.at).format("h:mm a") }
      : undefined,
  };
}

function eventTip(event: TimelineEvent, slow: boolean): string[] {
  const who = event.sender_name || event.sender;
  if (event.side === "customer")
    return [__("Customer message"), fmtAt(event.at)];
  const lines = [__("{0} replied", who)];
  if (event.wait_seconds != null) {
    const took = formatSeconds(event.wait_seconds) || "0m";
    lines.push(slow ? __("{0} · longest wait", took) : __("{0} wait", took));
  } else {
    lines.push(__("Follow-up"));
  }
  lines.push(fmtAt(event.at));
  return lines;
}

function pushEnding(segs: RailSegment[]): void {
  const hold = nodes.value.hold;
  const res = nodes.value.resolution;
  if (hold?.active) return pushHold(segs, hold, res);
  if (!res) return;
  const tip = milestoneTip(res);
  if (hold?.badge?.text) tip.push(hold.badge.text);
  if (res.state === "done" || (res.state === "breach" && res.timestamp)) {
    segs.push(line(IDLE, 48, { grow: true }));
    const sub = res.timestamp ? fmtAt(res.timestamp) : undefined;
    const cls = res.state === "done" ? GREEN : RED;
    segs.push({
      kind: "node",
      cls,
      tip,
      label: label(resolutionName(res), sub),
    });
    return;
  }
  segs.push(line(IDLE, 120, { grow: true }));
  const breach = res.state === "breach";
  segs.push({
    kind: "node",
    cls: breach ? RED : PENDING,
    tip,
    label: label(
      __("Resolution"),
      breach && res.eta
        ? __("was due {0}", fmtAt(res.eta) ?? "")
        : res.eta
        ? dueLabel(res.eta)
        : __("pending")
    ),
  });
}

function pushHold(
  segs: RailSegment[],
  hold: TimelineNode,
  res?: TimelineNode
): void {
  segs.push(line(PAUSE, 120, { grow: true, over: __("clock stopped") }));
  const tip = hold.took
    ? [__("Paused {0} so far", formatSeconds(hold.took) ?? "")]
    : [];
  segs.push({
    kind: "node",
    cls: BLUE,
    tip,
    label: label(
      __("SLA paused"),
      hold.timestamp ? __("since {0}", fmtAt(hold.timestamp) ?? "") : undefined
    ),
  });
  if (!res) return;
  segs.push(line(IDLE, 110, { grow: true }));
  const tipRes = milestoneTip(res);
  tipRes.push(__("clock resumes when the ticket reopens"));
  segs.push({
    kind: "node",
    cls: PENDING,
    tip: tipRes,
    label: label(__("Resolution"), __("pending")),
  });
}

// a label repeating the date already shown by the previous label keeps only
// the time, e.g. "Jul 17, 10:02 am" becomes "10:02 am" and "due at Jul 17,
// 10:02 am" becomes "due at 10:02 am"
function dedupeDayPrefixes(segs: RailSegment[]): void {
  let prevDay = "";
  for (const seg of segs) {
    if (seg.kind !== "node" || !seg.label) continue;
    if (!seg.label.strong) {
      prevDay = seg.label.title || prevDay;
      continue;
    }
    const [, prefix, day, rest] =
      seg.label.sub?.match(/^(.*?)(\w{3} \d{1,2}), (.+)$/) ?? [];
    if (!day || !rest) continue;
    if (day === prevDay) seg.label.sub = prefix + rest;
    else prevDay = day;
  }
}

// labels are centered under their dots, so the line span between two labeled
// nodes must fit both label halves or the texts collide
function widenCrowdedLegs(segs: RailSegment[]): void {
  let prevHalf = 0;
  let span = Infinity;
  let lastLine: RailLine | null = null;
  for (const seg of segs) {
    if (seg.kind === "line") {
      span += seg.width;
      lastLine = seg;
    } else if (seg.label) {
      const needed = prevHalf + labelHalfWidth(seg.label) + 12;
      if (lastLine && span < needed) lastLine.width += needed - span;
      prevHalf = labelHalfWidth(seg.label);
      span = 0;
      lastLine = null;
    } else {
      span += 8;
    }
  }
}

// rough text metrics: ~7px per text-sm char, ~6px per text-xs char
function labelHalfWidth(label: NonNullable<RailNode["label"]>): number {
  const title = (label.title?.length ?? 0) * 7;
  const sub = (label.sub?.length ?? 0) * 6;
  return Math.max(title, sub) / 2;
}

// milestone labels already show name and time below the dot, so the hover
// only carries what the label does not: the SLA verdict
function milestoneTip(node?: TimelineNode): string[] {
  return node?.badge?.text ? [node.badge.text] : [];
}

function resolutionName(res: TimelineNode): string {
  if (res.state === "breach" && res.timestamp) return __("Resolved late");
  if (res.state === "done")
    return res.timestamp ? __("Resolved") : __("Closed");
  return __("Resolution");
}

function label(title: string, sub?: string): RailNode["label"] {
  return { title, sub, strong: true };
}

function line(cls: string, width: number, extra: Partial<RailLine>): RailLine {
  return { kind: "line", cls, width, ...extra };
}

function dueLabel(eta: string): string {
  return __("due {0}", dayjsLocal(eta).format("MMM D, h:mm a"));
}

function fmtAt(timestamp: string): string;
function fmtAt(timestamp?: string | null): string | undefined;
function fmtAt(timestamp?: string | null): string | undefined {
  if (!timestamp) return undefined;
  return dayjsLocal(timestamp).format("MMM D, h:mm a");
}

watch(segments, () =>
  nextTick(() => {
    alignFirstLabel();
    updateFades();
  })
);

onMounted(() => {
  alignFirstLabel();
  updateFades();
  window.addEventListener("scroll", dismissPopoversOnScroll, true);
});

onUnmounted(() =>
  window.removeEventListener("scroll", dismissPopoversOnScroll, true)
);
</script>
