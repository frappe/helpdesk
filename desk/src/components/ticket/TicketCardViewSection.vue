<template>
  <div class="flex gap-4 px-5 pb-6 pt-3">
    <div class="flex-1">
      <div
        v-if="!loading && totalCount > 0"
        class="sticky top-0 z-30 mb-4 flex flex-wrap items-center justify-between gap-4 rounded-sm border border-outline-gray-2 bg-surface-white px-5 py-3 shadow-[0_8px_18px_rgba(0,0,0,0.05)]"
      >
        <div class="flex flex-wrap items-center gap-3">
          <div
            class="flex h-9 w-9 items-center justify-center rounded-lg border border-outline-gray-3 bg-surface-gray-1"
          >
            <LucideFilter class="h-4 w-4 text-ink-gray-7" />
          </div>
          <span class="text-base font-semibold text-ink-gray-9">
            {{ quickViewLabel }}
          </span>
          <span
            class="rounded-full bg-surface-gray-9 px-2.5 py-1 text-xs font-semibold leading-none text-ink-white"
          >
            {{ totalCount }}
          </span>
          <div class="flex items-center gap-2 text-sm text-ink-gray-8">
            <span class="font-semibold text-ink-gray-9">{{ pageStart }}</span>
            <span class="text-ink-gray-4">-</span>
            <span class="font-semibold text-ink-gray-9">{{ pageEnd }}</span>
            <span class="text-ink-gray-6">of</span>
            <span class="font-semibold text-ink-gray-9">{{ totalCount }}</span>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2.5">
            <span class="text-sm font-semibold text-ink-gray-7">Show</span>
            <Dropdown :options="pageLengthOptions" placement="bottom-end">
              <template #default="{ open }">
                <button
                  type="button"
                  class="flex h-9 items-center gap-2 rounded-lg border border-outline-gray-3 bg-surface-white px-3 text-sm font-semibold text-ink-gray-9 transition-all hover:-translate-y-0.5 hover:border-outline-gray-4 hover:bg-surface-gray-1 focus:-translate-y-0.5 focus:border-outline-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
                  aria-label="Select results per page"
                >
                  <span>{{ pageLengthCount }}</span>
                  <LucideChevronDown
                    class="h-4 w-4 text-ink-gray-5 transition-transform"
                    :class="open ? 'rotate-180' : ''"
                  />
                </button>
              </template>
            </Dropdown>
          </div>
          <div class="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              theme="gray"
              class="h-9 w-9 rounded-lg border border-outline-gray-3 bg-surface-white transition-transform hover:-translate-y-0.5 hover:bg-surface-gray-1"
              :disabled="pageStart <= 1 || loading"
              @click="emit('prev-page')"
              aria-label="Previous page"
            >
              <LucideChevronLeft class="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              theme="gray"
              class="h-9 w-9 rounded-lg border border-outline-gray-3 bg-surface-white transition-transform hover:-translate-y-0.5 hover:bg-surface-gray-1"
              :disabled="currentCount >= totalCount || loading"
              @click="emit('next-page')"
              aria-label="Next page"
            >
              <LucideChevronRight class="h-4 w-4" />
            </Button>
          </div>
        </div>
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
    </div>

    <div
      class="hidden lg:flex w-80 shrink-0 flex-col gap-5 rounded-xl border border-outline-gray-2 bg-surface-white p-5 shadow-sm h-fit sticky top-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-base font-semibold text-ink-gray-9">
          <LucideFilter class="h-5 w-5" />
          <span>Filters</span>
        </div>
        <Button size="sm" variant="ghost" theme="gray" class="text-ink-gray-7" @click="handleReset">
          Reset
        </Button>
      </div>

      <button
        type="button"
        class="text-xs font-semibold text-ink-gray-7 underline underline-offset-4 text-left hover:text-ink-gray-8 transition-colors"
      >
        Show applied filters
      </button>

      <div class="space-y-4 divide-y divide-outline-gray-2">
        <div class="space-y-4 pb-4">
          <div class="space-y-2">
            <label
              class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
            >
              Status
            </label>
            <MultiSelectCombobox
              :key="selectedStatusOption ? selectedStatusOption.value ?? selectedStatusOption.label : 'all-status'"
              :model-value="selectedStatusOption"
              :options="statusFilterOptions"
              placeholder="All status"
              @update:modelValue="updateFilter('status', $event)"
              :multiple="false"
              :button-classes="'w-full justify-between !h-10 !bg-surface-white border border-outline-gray-3 hover:!bg-surface-gray-1 rounded-lg px-3 text-sm text-ink-gray-9'"
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
              :model-value="filters.priority?.[0] || null"
              :options="priorityFilterOptions"
              placeholder="Any priority"
              @update:modelValue="updateFilter('priority', $event)"
              :multiple="false"
              :button-classes="'w-full justify-between !h-10 !bg-surface-white border border-outline-gray-3 hover:!bg-surface-gray-1 rounded-lg px-3 text-sm text-ink-gray-9'"
            />
          </div>

          <div class="space-y-2">
            <label
              class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
            >
              Team
            </label>
            <MultiSelectCombobox
              :model-value="filters.team?.[0] || null"
              :options="teamFilterOptions"
              placeholder="Any team"
              @update:modelValue="updateFilter('team', $event)"
              :multiple="false"
              :button-classes="'w-full justify-between !h-10 !bg-surface-white border border-outline-gray-3 hover:!bg-surface-gray-1 rounded-lg px-3 text-sm text-ink-gray-9'"
            />
          </div>

          <div class="space-y-2">
            <label
              class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide"
            >
              Agent
            </label>
            <MultiSelectCombobox
              :model-value="filters.agent?.[0] || null"
              :options="agentFilterOptions"
              placeholder="Any agent"
              @update:modelValue="updateFilter('agent', $event)"
              :multiple="false"
              :button-classes="'w-full justify-between !h-10 !bg-surface-white border border-outline-gray-3 hover:!bg-surface-gray-1 rounded-lg px-3 text-sm text-ink-gray-9'"
            />
          </div>
        </div>

        <div class="pt-4 space-y-3">
          <div class="text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
            Quick Views
          </div>
          <div class="space-y-1">
            <button
              v-for="view in quickViews"
              :key="view.label"
              class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-gray-8 transition-colors hover:bg-surface-gray-1 hover:text-ink-gray-9"
              :class="{
                'bg-surface-gray-2 font-medium text-ink-gray-9 border border-outline-gray-3':
                  activeQuickView === view.label,
              }"
              @click="applyQuickView(view)"
            >
              <component :is="view.icon" class="h-4 w-4 flex-shrink-0 text-ink-gray-6" />
              <span class="truncate">{{ view.label }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketCardView from "@/components/ticket/TicketCardView.vue";
// @ts-expect-error - legacy component lacks types
import MultiSelectCombobox from "@/components/frappe-ui/MultiSelectCombobox.vue";
import { Button, Dropdown } from "frappe-ui";
import { computed } from "vue";
import LucideFilter from "~icons/lucide/filter";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

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
    pageLengthCount?: number;
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
    pageLengthCount: 20,
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
  (e: "next-page"): void;
  (e: "prev-page"): void;
  (e: "update:filters", value: CardFilters): void;
  (e: "apply-filters", value: CardFilters): void;
  (e: "reset-filters"): void;
  (e: "apply-quick-view", view: QuickView): void;
  (e: "update-limit", value: number): void;
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

const pageLength = computed(() => props.pageLengthCount || 20);
const pageEnd = computed(() => Math.min(props.currentCount || 0, props.totalCount || 0));
const pageStart = computed(() => {
  if (!pageEnd.value) return 0;
  const start = pageEnd.value - pageLength.value + 1;
  return start < 1 ? 1 : start;
});

const pageLengthOptions = computed(() =>
  [10, 20, 50, 100].map((value) => ({
    label: `${value} per page`,
    onClick: () => emit("update-limit", value),
  }))
);

// Computed property to get the selected status option from statusFilterOptions
const selectedStatusOption = computed(() => {
  const currentFilter = props.filters.status?.[0];
  
  if (!currentFilter) {
    // Default to "All" option
    return props.statusFilterOptions?.find(opt => opt.value === "") || null;
  }
  
  const filterValue = typeof currentFilter === "object" && "value" in currentFilter 
    ? currentFilter.value 
    : currentFilter;
  
  // Find matching option from statusFilterOptions
  return props.statusFilterOptions?.find(opt => opt.value === filterValue) || currentFilter;
});

const quickViewLabel = computed(() => props.activeQuickView || "All tickets");
</script>
