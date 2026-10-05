<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __("Task Status Report") }}</div>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-2">
        <div v-if="report.data?.can_view_all !== false">
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ __("Team Member") }}</div>
          <Autocomplete
            :model-value="filters.user"
            :options="memberOptions"
            :placeholder="__('All')"
            @update:model-value="(o: any) => (filters.user = o?.value ?? '')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ __("Project / Client") }}</div>
          <Autocomplete
            :model-value="filters.project"
            :options="projectOptions"
            :placeholder="__('All')"
            @update:model-value="(o: any) => (filters.project = o?.value ?? '')"
          />
        </div>
        <FormControl v-model="filters.from_date" type="date" :label="__('Due From')" />
        <FormControl v-model="filters.to_date" type="date" :label="__('Due To')" />
        <FormControl
          v-model="filters.status"
          type="select"
          :label="__('Task Status')"
          :options="statusOptions"
        />
      </div>

      <div class="flex justify-end mb-3 h-7">
        <Button v-if="hasFilters" variant="ghost" @click="clearFilters">
          <template #prefix><LucideX class="size-4" /></template>
          {{ __("Clear filters") }}
        </Button>
      </div>

      <div class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div
          v-for="card in cards"
          :key="card.key"
          class="bg-surface-white border border-outline-gray-2 rounded-lg p-4 transition-shadow hover:shadow-md"
        >
          <div class="flex items-center gap-2 text-xs text-ink-gray-5 mb-1">
            <span class="size-2 rounded-full" :class="card.dot" />
            {{ card.label }}
          </div>
          <div class="text-2xl font-semibold" :class="card.text">
            {{ report.data?.summary?.[card.key] ?? 0 }}
          </div>
        </div>
      </div>

      <div
        v-if="chart.points.length"
        class="bg-surface-white border border-outline-gray-2 rounded-lg p-4 mb-6"
      >
        <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div class="text-sm font-medium text-ink-gray-8">
            {{ chart.title }}
            <span class="ml-2 text-xs font-normal text-ink-gray-5">
              {{ __("{0} completed tasks have no estimate", [report.data?.summary?.no_estimate ?? 0]) }}
            </span>
          </div>
          <div class="flex items-center gap-4 text-xs text-ink-gray-6">
            <span class="flex items-center gap-1.5">
              <span class="h-0.5 w-4 rounded" :style="{ background: ESTIMATED_COLOR }" />{{ __("Estimated") }}
            </span>
            <span class="flex items-center gap-1.5">
              <span class="h-0.5 w-4 rounded" :style="{ background: ACTUAL_COLOR }" />{{ __("Actual") }}
            </span>
          </div>
        </div>
        <div class="overflow-x-auto">
          <svg :viewBox="`0 0 ${chart.width} ${CHART_H}`" :width="chart.width" :height="CHART_H" class="max-w-none">
            <g v-for="tick in chart.ticks" :key="tick.value">
              <line
                :x1="PAD_L" :x2="chart.width - PAD_R" :y1="tick.y" :y2="tick.y"
                stroke="var(--outline-gray-2)" stroke-width="1"
              />
              <text :x="PAD_L - 8" :y="tick.y + 4" text-anchor="end" font-size="11" fill="var(--ink-gray-5)">
                {{ tick.value }}h
              </text>
            </g>
            <polyline
              :points="chart.estimatedLine" fill="none" :stroke="ESTIMATED_COLOR"
              stroke-width="2" stroke-linejoin="round" stroke-linecap="round"
            />
            <polyline
              :points="chart.actualLine" fill="none" :stroke="ACTUAL_COLOR"
              stroke-width="2" stroke-linejoin="round" stroke-linecap="round"
            />
            <g v-for="pt in chart.points" :key="pt.key">
              <circle :cx="pt.x" :cy="pt.yEstimated" r="4" :fill="ESTIMATED_COLOR">
                <title>{{ pt.tip }}</title>
              </circle>
              <circle :cx="pt.x" :cy="pt.yActual" r="4" :fill="ACTUAL_COLOR">
                <title>{{ pt.tip }}</title>
              </circle>
              <text
                :x="pt.x" :y="CHART_H - PAD_B + 16" font-size="11" fill="var(--ink-gray-6)"
                text-anchor="end" :transform="`rotate(-30 ${pt.x} ${CHART_H - PAD_B + 16})`"
              >
                {{ pt.label }}
              </text>
            </g>
          </svg>
        </div>
      </div>

      <div v-if="report.loading" class="text-p-base text-ink-gray-6">{{ __("Loading...") }}</div>
      <div
        v-else-if="!members.length"
        class="flex items-center justify-center py-12 text-p-base text-ink-gray-6"
      >
        {{ __("No tasks found") }}
      </div>
      <div v-else class="bg-surface-white border border-outline-gray-2 rounded-lg overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-ink-gray-5 border-b border-outline-gray-2 bg-surface-gray-1">
              <th class="px-4 py-3 font-medium">{{ __("Team Member") }}</th>
              <th v-for="card in cards" :key="card.key" class="px-4 py-3 font-medium text-right">
                <span class="inline-flex items-center gap-1.5">
                  <span class="size-2 rounded-full" :class="card.dot" />
                  {{ card.label }}
                </span>
              </th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Estimated") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Actual") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Over / Under") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in members"
              :key="row.user"
              class="group border-b border-outline-gray-2 last:border-b-0 transition-colors hover:bg-surface-gray-1"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <div class="group/donut relative shrink-0">
                    <div
                      class="size-9 rounded-full"
                      :style="{ background: donutBackground(row) }"
                    >
                      <div
                        class="absolute inset-[5px] flex items-center justify-center rounded-full bg-surface-base text-[10px] font-medium tabular-nums text-ink-gray-7"
                      >
                        {{ percent(row.completed, row.total) }}%
                      </div>
                    </div>
                    <div
                      class="pointer-events-none absolute left-0 top-full z-10 mt-1 hidden w-max rounded-md border border-outline-gray-2 bg-surface-elevation-2 px-2.5 py-1.5 text-xs text-ink-gray-8 shadow-lg group-hover/donut:block"
                    >
                      <div v-for="seg in segments" :key="seg.key" class="flex items-center gap-2">
                        <span class="size-2 rounded-full" :class="seg.bar" />
                        <span>{{ seg.label }}: {{ row[seg.key] }} ({{ percent(row[seg.key], row.total) }}%)</span>
                      </div>
                    </div>
                  </div>
                  <div class="min-w-0">
                    <div class="text-ink-gray-8">{{ row.full_name }}</div>
                    <div v-if="row.user && row.user !== row.full_name" class="text-xs text-ink-gray-5">
                      {{ row.user }}
                    </div>
                  </div>
                </div>
              </td>
              <td v-for="card in cards" :key="card.key" class="px-4 py-3 text-right">
                <span
                  class="inline-block min-w-8 px-2 py-0.5 rounded-full tabular-nums transition-colors"
                  :class="row[card.key] ? [card.text, card.hover] : 'text-ink-gray-4'"
                >
                  {{ row[card.key] }}
                </span>
              </td>
              <td class="px-4 py-3 text-right tabular-nums text-ink-gray-7">
                <span v-if="row.judged">{{ formatHours(row.estimated_hours) }}</span>
                <span v-else class="text-ink-gray-4">-</span>
              </td>
              <td class="px-4 py-3 text-right tabular-nums">
                <span
                  v-if="row.judged"
                  :class="row.actual_hours > row.estimated_hours ? 'text-ink-orange-6 font-medium' : 'text-ink-green-7'"
                >
                  {{ formatHours(row.actual_hours) }}
                </span>
                <span v-else class="text-ink-gray-4">-</span>
              </td>
              <td class="px-4 py-3 text-right tabular-nums">
                <span v-if="row.judged" :class="extraClass(row)">{{ formatExtra(row) }}</span>
                <span v-else class="text-ink-gray-4">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import { Button, createResource, FormControl } from "frappe-ui";
import { __ } from "@/translation";
import { Autocomplete } from "@/components";
import LayoutHeader from "@/components/LayoutHeader.vue";
import LucideX from "~icons/lucide/x";

interface MemberRow {
  user: string;
  full_name: string;
  judged: number;
  estimated_hours: number;
  actual_hours: number;
  no_estimate: number;
  total: number;
  completed: number;
  ongoing: number;
  pending: number;
  overdue: number;
}

const filters = reactive({ user: "", project: "", from_date: "", to_date: "", status: "" });

const cards = [
  { key: "total", label: __("Total Tasks"), dot: "bg-surface-violet-6", text: "text-ink-violet-8", hover: "group-hover:bg-surface-violet-2" },
  { key: "completed", label: __("Completed"), dot: "bg-surface-green-3", text: "text-ink-green-7", hover: "group-hover:bg-surface-green-2" },
  { key: "ongoing", label: __("Ongoing"), dot: "bg-surface-blue-3", text: "text-ink-blue-7", hover: "group-hover:bg-surface-blue-2" },
  { key: "pending", label: __("Pending"), dot: "bg-surface-amber-3", text: "text-ink-amber-7", hover: "group-hover:bg-surface-amber-2" },
  { key: "overdue", label: __("Overdue"), dot: "bg-surface-red-5", text: "text-ink-red-7", hover: "group-hover:bg-surface-red-2" },
] as const;

const segments = [
  { key: "completed", label: __("Completed"), bar: "bg-surface-green-3", color: "var(--surface-green-3)" },
  { key: "ongoing", label: __("Ongoing"), bar: "bg-surface-blue-3", color: "var(--surface-blue-3)" },
  { key: "pending", label: __("Pending"), bar: "bg-surface-amber-3", color: "var(--surface-amber-3)" },
] as const;

function formatHours(h: number) {
  return `${h}h`;
}

function extraHours(r: { actual_hours: number; estimated_hours: number }) {
  return Math.round((r.actual_hours - r.estimated_hours) * 10) / 10;
}

function formatExtra(r: { actual_hours: number; estimated_hours: number }) {
  const d = extraHours(r);
  return d > 0 ? `+${d}h` : `${d}h`;
}

function extraClass(r: { actual_hours: number; estimated_hours: number }) {
  return extraHours(r) > 0 ? "text-ink-orange-6 font-medium" : "text-ink-green-7";
}

const statusOptions = [
  { label: __("All"), value: "" },
  { label: __("Completed"), value: "Completed" },
  { label: __("Ongoing"), value: "Working" },
  { label: __("Pending Review"), value: "Pending Review" },
  { label: __("Pending / Not Started"), value: "Open" },
  { label: __("Overdue"), value: "Overdue" },
  { label: __("Over Estimate"), value: "Over Estimate" },
];

const users = createResource({
  url: "helpdesk.tasky.api.get_users",
  auto: true,
  transform: (d: any[]) => d ?? [],
});
const projects = createResource({
  url: "helpdesk.tasky.api.get_projects",
  auto: true,
  transform: (d: any[]) => d ?? [],
});

const memberOptions = computed(() => [
  ...(users.data ?? []).map((u: any) => ({ label: u.full_name || u.name, value: u.name })),
]);
const projectOptions = computed(() => [
  ...(projects.data ?? []).map((p: any) => ({ label: p.project_name || p.name, value: p.name })),
]);

const report = createResource({
  url: "helpdesk.tasky.api.get_task_status_report",
  makeParams: () => ({ ...filters }),
  auto: true,
});

watch(filters, () => report.reload());

function donutBackground(row: MemberRow) {
  if (!row.total) return "var(--surface-gray-2)";
  let start = 0;
  const stops = segments.map((seg) => {
    const end = start + (row[seg.key] / row.total) * 100;
    const stop = `${seg.color} ${start}% ${end}%`;
    start = end;
    return stop;
  });
  return `conic-gradient(${stops.join(", ")})`;
}

function percent(n: number, total: number) {
  return total ? Math.round((n / total) * 100) : 0;
}

const hasFilters = computed(() => Object.values(filters).some(Boolean));

function clearFilters() {
  Object.assign(filters, { user: "", project: "", from_date: "", to_date: "", status: "" });
}

const members = computed<MemberRow[]>(() => report.data?.members ?? []);

const ESTIMATED_COLOR = "var(--ink-blue-5, #3b82f6)";
const ACTUAL_COLOR = "var(--ink-orange-5, #f97316)";
const CHART_H = 280;
const PAD_L = 44;
const PAD_R = 24;
const PAD_T = 16;
const PAD_B = 76;

function shorten(text: string, n = 14) {
  return text.length > n ? text.slice(0, n - 1) + "…" : text;
}

// One person: each completed task is a point. Whole team: each person is a point.
const chart = computed(() => {
  const perTask = !!filters.user || report.data?.can_view_all === false;
  const source: { key: string; label: string; estimated: number; actual: number; tip: string }[] = perTask
    ? (report.data?.tasks ?? []).map((t: any) => ({
        key: t.name,
        label: shorten(t.subject),
        estimated: t.estimated,
        actual: t.actual,
        tip: `${t.subject}\n${__("Estimated")}: ${t.estimated}h, ${__("Actual")}: ${t.actual}h`,
      }))
    : members.value
        .filter((m) => m.judged)
        .sort((a, b) => b.actual_hours - a.actual_hours)
        .slice(0, 10)
        .map((m) => ({
          key: m.user,
          label: shorten(m.full_name),
          estimated: m.estimated_hours,
          actual: m.actual_hours,
          tip: `${m.full_name}\n${__("Estimated")}: ${m.estimated_hours}h, ${__("Actual")}: ${m.actual_hours}h`,
        }));

  const rawMax = Math.max(1, ...source.flatMap((p) => [p.estimated, p.actual]));
  const step = Math.pow(10, Math.floor(Math.log10(rawMax)));
  const max = Math.ceil(rawMax / step) * step;
  const width = Math.max(520, source.length * 70 + PAD_L + PAD_R);
  const plotW = width - PAD_L - PAD_R;
  const plotH = CHART_H - PAD_T - PAD_B;
  const y = (v: number) => PAD_T + (1 - v / max) * plotH;

  const points = source.map((p, i) => ({
    ...p,
    x: PAD_L + (source.length === 1 ? plotW / 2 : (i * plotW) / (source.length - 1)),
    yEstimated: y(p.estimated),
    yActual: y(p.actual),
  }));
  return {
    title: perTask ? __("Estimated vs Actual hours, by task") : __("Estimated vs Actual hours, by team member"),
    width,
    points,
    estimatedLine: points.map((p) => `${p.x},${p.yEstimated}`).join(" "),
    actualLine: points.map((p) => `${p.x},${p.yActual}`).join(" "),
    ticks: [0, 0.25, 0.5, 0.75, 1].map((f) => ({ value: Math.round(max * f * 10) / 10, y: y(max * f) })),
  };
});
</script>
