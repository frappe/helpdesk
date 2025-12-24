<template>
  <div class="flex flex-col gap-4 px-5 pb-6 pt-3 lg:flex-row lg:gap-0">
    <div class="flex-1">
      <div class="rounded-xl bg-surface-white p-4">
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
    </div>

    <div
      class="hidden lg:block w-4 shrink-0 self-stretch -mt-3"
      style="background-color: #EBEEF3"
      aria-hidden="true"
    ></div>

    <div
      class="hidden lg:flex w-72 shrink-0 flex-col gap-4 bg-surface-white p-4 h-fit sticky top-4"
    >
      <div class="flex items-center justify-between">
        <span class="font-['Poppins'] text-[14px] font-normal leading-[21px] text-ink-gray-9">
          FILTERS
        </span>
        <button
          type="button"
          class="font-['Poppins'] text-[12px] font-medium leading-[18px] text-ink-gray-9 transition-colors hover:text-ink-gray-8"
        >
          Show Applied Filters
        </button>
      </div>

      <div class="relative">
        <label class="sr-only" for="ticket-filter-search">Search</label>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          class="pointer-events-none absolute left-3 top-1/2 h-3 w-3 -translate-y-1/2"
          aria-hidden="true"
        >
          <g clip-path="url(#clip0_7898_1623)">
            <path
              fill-rule="evenodd"
              clip-rule="evenodd"
              d="M5.0475 9.16873C2.68875 9.16873 0.77663 7.29 0.77663 4.96875C0.77663 2.6475 2.68875 0.765015 5.0475 0.765015C7.40625 0.765015 9.31875 2.6475 9.31875 4.96875C9.31875 7.29 7.40625 9.16873 5.0475 9.16873ZM11.883 11.3438L8.78587 8.295C9.59662 7.41375 10.095 6.25125 10.095 4.96875C10.095 2.22375 7.83525 0 5.0475 0C2.25975 0 0 2.22375 0 4.96875C0 7.71 2.25975 9.93375 5.0475 9.93375C6.252 9.93375 7.35675 9.51751 8.2245 8.82376L11.334 11.8837C11.4859 12.0337 11.7315 12.0337 11.883 11.8837C12.0349 11.7375 12.0349 11.4938 11.883 11.3438Z"
              fill="black"
            />
          </g>
          <defs>
            <clipPath id="clip0_7898_1623">
              <rect width="12" height="12" fill="white" />
            </clipPath>
          </defs>
        </svg>
        <input
          id="ticket-filter-search"
          v-model="searchQuery"
          type="text"
          placeholder="Search"
          class="h-[35px] w-full rounded border border-[#E4E4E4] bg-surface-white pl-8 pr-3 text-[12px] leading-[18px] text-ink-gray-9 placeholder-ink-gray-4 focus:border-outline-gray-3 focus:outline-none focus:ring-2 focus:ring-outline-gray-2"
        />
      </div>

      <div class="space-y-3">
        <div class="space-y-1.5">
          <label class="text-[12px] font-normal leading-[18px] text-ink-gray-7">
            Status
          </label>
          <div class="relative">
            <select
              class="h-[35px] w-full appearance-none rounded border border-[#E4E4E4] bg-surface-white px-3 pr-8 text-[12px] leading-[18px] text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none focus:ring-2 focus:ring-outline-gray-2"
              :value="selectedStatusValue"
              @change="handleStatusChange"
            >
              <option value="">--</option>
              <option
                v-for="option in statusSelectOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="text-[12px] font-normal leading-[18px] text-ink-gray-7">
            Agents
          </label>
          <div class="relative">
            <select
              class="h-[35px] w-full appearance-none rounded border border-[#E4E4E4] bg-surface-white px-3 pr-8 text-[12px] leading-[18px] text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none focus:ring-2 focus:ring-outline-gray-2"
              :value="selectedAgentValue"
              @change="handleAgentChange"
            >
              <option value="">--</option>
              <option
                v-for="option in agentFilterOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="text-[12px] font-normal leading-[18px] text-ink-gray-7">
            Created
          </label>
          <div class="relative">
            <select
              v-model="createdRange"
              class="h-[35px] w-full appearance-none rounded border border-[#E4E4E4] bg-surface-white px-3 pr-8 text-[12px] leading-[18px] text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none focus:ring-2 focus:ring-outline-gray-2"
            >
              <option
                v-for="option in createdRangeOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="text-[12px] font-normal leading-[18px] text-ink-gray-7">
            Created At
          </label>
          <div class="relative">
            <select
              v-model="createdAt"
              class="h-[35px] w-full appearance-none rounded border border-[#E4E4E4] bg-surface-white px-3 pr-8 text-[12px] leading-[18px] text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none focus:ring-2 focus:ring-outline-gray-2"
            >
              <option value="">--</option>
              <option
                v-for="option in dateOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="text-[12px] font-normal leading-[18px] text-ink-gray-7">
            Resolved At
          </label>
          <div class="relative">
            <select
              v-model="resolvedAt"
              class="h-[35px] w-full appearance-none rounded border border-[#E4E4E4] bg-surface-white px-3 pr-8 text-[12px] leading-[18px] text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none focus:ring-2 focus:ring-outline-gray-2"
            >
              <option value="">--</option>
              <option
                v-for="option in dateOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketCardView from "@/components/ticket/TicketCardView.vue";
import { Button, Dropdown } from "frappe-ui";
import { computed, ref, watch } from "vue";
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
    search?: string;
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
    search: "",
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
  (e: "update:search", value: string): void;
}>();

const searchQuery = ref(props.search || "");
const syncingSearch = ref(false);
const createdRange = ref("last_30_days");
const createdAt = ref("");
const resolvedAt = ref("");

const createdRangeOptions = [
  { label: "Last 7 days", value: "last_7_days" },
  { label: "Last 30 days", value: "last_30_days" },
  { label: "Last 90 days", value: "last_90_days" },
];

const dateOptions = [
  { label: "Today", value: "today" },
  { label: "Yesterday", value: "yesterday" },
  { label: "This week", value: "this_week" },
  { label: "This month", value: "this_month" },
];

watch(
  () => props.search,
  (value) => {
    const nextValue = value ?? "";
    if (nextValue !== searchQuery.value) {
      syncingSearch.value = true;
      searchQuery.value = nextValue;
    }
  }
);

watch(searchQuery, (value) => {
  if (syncingSearch.value) {
    syncingSearch.value = false;
    return;
  }
  emit("update:search", value);
});

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

const statusSelectOptions = computed(() =>
  (props.statusFilterOptions || []).filter((option) => option.value !== "")
);

const selectedStatusValue = computed(() => {
  const first = props.filters.status?.[0];
  if (!first) return "";
  if (typeof first === "string") return first;
  return first?.value || "";
});

function handleStatusChange(event: Event) {
  const target = event.target as HTMLSelectElement | null;
  const value = target?.value ?? "";
  const option = (props.statusFilterOptions || []).find(
    (item) => item.value === value
  );
  updateFilter("status", option || value || null);
}

const selectedAgentValue = computed(() => {
  const first = props.filters.agent?.[0];
  if (!first) return "";
  if (typeof first === "string") return first;
  return first?.value || "";
});

function handleAgentChange(event: Event) {
  const target = event.target as HTMLSelectElement | null;
  const value = target?.value || "";
  updateFilter("agent", value || null);
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

const quickViewLabel = computed(() => props.activeQuickView || "All tickets");
</script>
