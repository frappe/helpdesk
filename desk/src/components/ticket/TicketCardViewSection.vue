<template>
  <div class="flex gap-4 px-5 pb-6 pt-3">
    <div class="flex-1">
      <div
        v-if="!loading && totalCount > 0"
        class="mb-4 flex items-center justify-between"
      >
        <p class="text-sm text-ink-gray-6">
          Showing
          <span class="font-semibold text-ink-gray-9">{{ currentCount }}</span>
          of
          <span class="font-semibold text-ink-gray-9">{{ totalCount }}</span>
          tickets
        </p>
      </div>
      <TicketCardView
        :rows="rows"
        :loading="loading"
        :status-options="statusOptions"
        :priority-options="priorityOptions"
        @row-click="emit('row-click', $event)"
        @update-status="(ticketId, value) => emit('update-status', ticketId, value)"
        @update-priority="
          (ticketId, value) => emit('update-priority', ticketId, value)
        "
      />
      <div
        v-if="currentCount < totalCount"
        class="mt-4 flex items-center justify-center"
      >
        <Button variant="outline" theme="gray" :loading="loading" @click="emit('load-more')">
          Load more
        </Button>
      </div>
    </div>

    <div
      class="hidden lg:flex w-80 shrink-0 flex-col gap-5 rounded-lg border border-outline-gray-2 bg-surface-white p-5 shadow-sm h-fit sticky top-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-lg font-semibold text-ink-gray-9">
          <LucideFilter class="h-5 w-5" />
          <span>Filters</span>
        </div>
        <Button size="sm" variant="ghost" theme="gray" @click="handleReset">
          Reset
        </Button>
      </div>

      <div class="space-y-5 border-t border-outline-gray-2 pt-5">
        <div class="space-y-2">
          <label
            class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
          >
            Status
          </label>
          <MultiSelectCombobox
            :model-value="filters.status"
            :options="statusFilterOptions"
            placeholder="All Status"
            @update:modelValue="updateFilter('status', $event)"
            :multiple="false"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          >
            <template #item-prefix="{ option }">
              <span
                v-if="option.value"
                class="mr-2 h-2 w-2 rounded-full"
                :class="option.indicatorClass"
              />
            </template>
          </MultiSelectCombobox>
        </div>

        <div class="space-y-2">
          <label
            class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
          >
            Priority
          </label>
          <MultiSelectCombobox
            :model-value="filters.priority"
            :options="priorityFilterOptions"
            placeholder="Any Priority"
            @update:modelValue="updateFilter('priority', $event)"
            :multiple="false"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          />
        </div>

        <div class="space-y-2">
          <label
            class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
          >
            Team
          </label>
          <MultiSelectCombobox
            :model-value="filters.team"
            :options="teamFilterOptions"
            placeholder="Any Team"
            @update:modelValue="updateFilter('team', $event)"
            :multiple="false"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          />
        </div>

        <div class="space-y-2">
          <label
            class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
          >
            Agent
          </label>
          <MultiSelectCombobox
            :model-value="filters.agent"
            :options="agentFilterOptions"
            placeholder="Any Agent"
            @update:modelValue="updateFilter('agent', $event)"
            :multiple="false"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          />
        </div>
      </div>

      <div class="space-y-3 border-t border-outline-gray-2 pt-5">
        <div class="text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
          Quick Views
        </div>
        <div class="space-y-1">
          <button
            v-for="view in quickViews"
            :key="view.label"
            class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-gray-8 transition-colors hover:bg-surface-gray-1 hover:text-ink-gray-9"
            :class="{
              'bg-surface-gray-2 font-medium text-ink-gray-9':
                activeQuickView === view.label,
            }"
            @click="applyQuickView(view)"
          >
            <component :is="view.icon" class="h-4 w-4 flex-shrink-0" />
            <span class="truncate">{{ view.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketCardView from "@/components/ticket/TicketCardView.vue";
// @ts-expect-error - legacy component lacks types
import MultiSelectCombobox from "@/components/frappe-ui/MultiSelectCombobox.vue";
import { Button } from "frappe-ui";
import LucideFilter from "~icons/lucide/filter";

type CardFilters = {
  status: any[];
  priority: any[];
  team: any[];
  agent: any[];
};

type FilterOption = {
  label: string;
  value: string;
  indicatorClass?: string;
  category?: string;
};

type QuickView = {
  label: string;
  icon: any;
  filters: Record<string, any>;
};

const props = withDefaults(
  defineProps<{
    rows: any[];
    loading?: boolean;
    totalCount?: number;
    currentCount?: number;
    statusOptions?: Array<{
      label: string;
      value: string;
      indicatorClass?: string;
      category?: string;
    }>;
    priorityOptions?: string[];
    statusFilterOptions?: FilterOption[];
    priorityFilterOptions?: FilterOption[];
    teamFilterOptions?: FilterOption[];
    agentFilterOptions?: FilterOption[];
    filters: CardFilters;
    quickViews: QuickView[];
    activeQuickView?: string;
  }>(),
  {
    rows: () => [],
    loading: false,
    totalCount: 0,
    currentCount: 0,
    statusOptions: () => [],
    priorityOptions: () => [],
    statusFilterOptions: () => [],
    priorityFilterOptions: () => [],
    teamFilterOptions: () => [],
    agentFilterOptions: () => [],
    filters: () => ({
      status: [],
      priority: [],
      team: [],
      agent: [],
    }),
    quickViews: () => [],
    activeQuickView: "",
  }
);

const emit = defineEmits<{
  (e: "row-click", ticketId: string): void;
  (e: "update-status", ticketId: string, value: string): void;
  (e: "update-priority", ticketId: string, value: string): void;
  (e: "load-more"): void;
  (e: "update:filters", value: CardFilters): void;
  (e: "apply-filters", value: CardFilters): void;
  (e: "reset-filters"): void;
  (e: "apply-quick-view", view: QuickView): void;
}>();

function updateFilter(key: keyof CardFilters, value: any) {
  const optionPool: Record<keyof CardFilters, FilterOption[]> = {
    status: props.statusFilterOptions || [],
    priority: props.priorityFilterOptions || [],
    team: props.teamFilterOptions || [],
    agent: props.agentFilterOptions || [],
  };

  const normalize = (v: any) => {
    const base = Array.isArray(v) ? v : v ? [v] : [];
    return base
      .filter(Boolean)
      .map((item) => {
        if (typeof item === "object" && item?.label && item?.value) return item;
        const raw = typeof item === "object" && "value" in item ? item.value : item;
        const match = (optionPool[key] || []).find((o) => o.value === raw);
        const valueStr = raw ?? "";
        return match || { label: String(valueStr), value: String(valueStr) };
      })
      .slice(0, 1);
  };

  const nextFilters = {
    ...props.filters,
    [key]: normalize(value),
  };
  emit("update:filters", nextFilters);
  emit("apply-filters", nextFilters);
}

function handleReset() {
  emit("reset-filters");
}

function applyQuickView(view: QuickView) {
  emit("apply-quick-view", view);
}
</script>

