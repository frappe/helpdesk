<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __("Performance") }}</div>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-2">
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
      </div>
      <div class="flex justify-end mb-3 h-7">
        <Button v-if="hasFilters" variant="ghost" @click="clearFilters">
          <template #prefix><LucideX class="size-4" /></template>
          {{ __("Clear filters") }}
        </Button>
      </div>

      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div
          v-for="card in cards"
          :key="card.label"
          class="bg-surface-white border border-outline-gray-2 rounded-lg p-4 transition-shadow hover:shadow-md"
        >
          <div class="flex items-center gap-2 text-xs text-ink-gray-5 mb-1">
            <span class="size-2 rounded-full" :class="card.dot" />
            {{ card.label }}
          </div>
          <div class="text-2xl font-semibold" :class="card.text">{{ card.value }}</div>
          <div class="text-xs text-ink-gray-5 mt-1">{{ card.hint }}</div>
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
              <th class="px-4 py-3 font-medium w-12">#</th>
              <th class="px-4 py-3 font-medium">{{ __("Team Member") }}</th>
              <th class="px-4 py-3 font-medium w-56">{{ __("Score") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Tasks") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Completion") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("On-time") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Overdue") }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ __("Hours") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in members"
              :key="row.user"
              class="border-b border-outline-gray-2 last:border-b-0 transition-colors hover:bg-surface-gray-1"
              :class="row.low_data ? 'opacity-60' : ''"
            >
              <td class="px-4 py-3 text-ink-gray-5 tabular-nums">
                {{ row.low_data ? "-" : i + 1 }}
              </td>
              <td class="px-4 py-3">
                <div class="text-ink-gray-8">{{ row.full_name }}</div>
                <div v-if="row.user !== row.full_name" class="text-xs text-ink-gray-5">{{ row.user }}</div>
                <div v-if="row.low_data" class="text-xs text-ink-gray-5">
                  {{ __("Fewer than {0} tasks, not ranked", [report.data?.min_tasks]) }}
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div class="h-2 flex-1 rounded-full bg-surface-gray-2 overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :class="scoreBar(row.score)"
                      :style="{ width: row.score + '%' }"
                    />
                  </div>
                  <span class="w-8 text-right font-medium tabular-nums text-ink-gray-8">{{ row.score }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-right tabular-nums text-ink-gray-7">{{ row.total }}</td>
              <td class="px-4 py-3 text-right tabular-nums text-ink-gray-7">
                {{ row.completion_rate }}%
                <span class="text-xs text-ink-gray-5">({{ row.completed }})</span>
              </td>
              <td class="px-4 py-3 text-right tabular-nums">
                <span v-if="row.on_time_rate !== null" class="text-ink-gray-7">
                  {{ row.on_time_rate }}%
                  <span class="text-xs text-ink-gray-5">({{ row.on_time }}/{{ row.on_time_judged }})</span>
                </span>
                <span v-else class="text-ink-gray-4" :title="__('No completion dates recorded yet')">n/a</span>
              </td>
              <td class="px-4 py-3 text-right tabular-nums">
                <span :class="row.overdue ? 'text-ink-red-7 font-medium' : 'text-ink-gray-4'">{{ row.overdue }}</span>
              </td>
              <td class="px-4 py-3 text-right tabular-nums text-ink-gray-7">{{ row.hours }}h</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-4 text-xs text-ink-gray-5">
        {{ __("Score = 60% completion rate + 40% on-time rate. Where on-time is n/a, score is the completion rate alone.") }}
      </p>
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
  total: number;
  completed: number;
  completion_rate: number;
  on_time: number;
  on_time_judged: number;
  on_time_rate: number | null;
  overdue: number;
  hours: number;
  score: number;
  low_data: boolean;
}

const filters = reactive({ user: "", project: "", from_date: "", to_date: "" });
const hasFilters = computed(() => Object.values(filters).some(Boolean));

function clearFilters() {
  Object.assign(filters, { user: "", project: "", from_date: "", to_date: "" });
}

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

const memberOptions = computed(() =>
  (users.data ?? []).map((u: any) => ({ label: u.full_name || u.name, value: u.name }))
);
const projectOptions = computed(() =>
  (projects.data ?? []).map((p: any) => ({ label: p.project_name || p.name, value: p.name }))
);

const report = createResource({
  url: "helpdesk.tasky.api.get_performance_report",
  makeParams: () => ({ ...filters }),
  auto: true,
});

watch(filters, () => report.reload());

const members = computed<MemberRow[]>(() => report.data?.members ?? []);

const cards = computed(() => {
  const s = report.data?.summary;
  return [
    {
      label: __("Completion Rate"),
      value: s ? `${s.completion_rate}%` : "-",
      hint: s ? __("{0} of {1} tasks done", [s.completed, s.total]) : "",
      dot: "bg-surface-green-3",
      text: "text-ink-green-7",
    },
    {
      label: __("On-time Rate"),
      value: s?.on_time_rate != null ? `${s.on_time_rate}%` : "n/a",
      hint: s ? __("Based on {0} completed tasks with dates", [s.on_time_judged]) : "",
      dot: "bg-surface-blue-3",
      text: "text-ink-blue-7",
    },
    {
      label: __("Overdue Now"),
      value: String(s?.overdue ?? 0),
      hint: __("Open tasks past their due date"),
      dot: "bg-surface-red-5",
      text: "text-ink-red-7",
    },
    {
      label: __("Hours Logged"),
      value: s ? `${s.hours}h` : "-",
      hint: __("Total time recorded on tasks"),
      dot: "bg-surface-violet-6",
      text: "text-ink-violet-8",
    },
  ];
});

function scoreBar(score: number) {
  if (score >= 75) return "bg-surface-green-3";
  if (score >= 40) return "bg-surface-amber-3";
  return "bg-surface-red-5";
}
</script>
