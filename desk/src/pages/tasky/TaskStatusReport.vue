<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __("Task Status Report") }}</div>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-2">
        <div>
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
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in members"
              :key="row.user"
              class="group border-b border-outline-gray-2 last:border-b-0 transition-colors hover:bg-surface-gray-1"
            >
              <td class="px-4 py-3">
                <div class="text-ink-gray-8">{{ row.full_name }}</div>
                <div v-if="row.user && row.user !== row.full_name" class="text-xs text-ink-gray-5">
                  {{ row.user }}
                </div>
                <div v-if="row.total" class="group/bar relative mt-1.5 w-40 max-w-full">
                  <div class="flex h-1.5 rounded-full overflow-hidden bg-surface-gray-2">
                    <div
                      v-for="seg in segments"
                      :key="seg.key"
                      :class="seg.bar"
                      :style="{ width: (row[seg.key] / row.total) * 100 + '%' }"
                    />
                  </div>
                  <div
                    class="pointer-events-none absolute left-0 top-full z-10 mt-1 hidden w-max rounded-md border border-outline-gray-2 bg-surface-elevation-2 px-2.5 py-1.5 text-xs text-ink-gray-8 shadow-lg group-hover/bar:block"
                  >
                    <div v-for="seg in segments" :key="seg.key" class="flex items-center gap-2">
                      <span class="size-2 rounded-full" :class="seg.bar" />
                      <span>{{ seg.label }}: {{ row[seg.key] }} ({{ percent(row[seg.key], row.total) }}%)</span>
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
  { key: "completed", label: __("Completed"), bar: "bg-surface-green-3" },
  { key: "ongoing", label: __("Ongoing"), bar: "bg-surface-blue-3" },
  { key: "pending", label: __("Pending"), bar: "bg-surface-amber-3" },
] as const;

const statusOptions = [
  { label: __("All"), value: "" },
  { label: __("Completed"), value: "Completed" },
  { label: __("Ongoing"), value: "Working" },
  { label: __("Pending Review"), value: "Pending Review" },
  { label: __("Pending / Not Started"), value: "Open" },
  { label: __("Overdue"), value: "Overdue" },
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

function percent(n: number, total: number) {
  return total ? Math.round((n / total) * 100) : 0;
}

const hasFilters = computed(() => Object.values(filters).some(Boolean));

function clearFilters() {
  Object.assign(filters, { user: "", project: "", from_date: "", to_date: "", status: "" });
}

const members = computed<MemberRow[]>(() => report.data?.members ?? []);
</script>
