<template>
  <div class="flex flex-col h-full bg-gray-50">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">My Dashboard</div>
      </template>
      <template #right-header>
        <span class="text-sm text-blue-600 cursor-pointer hover:underline">
          Recent activities &gt;
        </span>
      </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-auto flex-1">
      <!-- Filters -->
      <div class="mb-4 flex items-center gap-4 overflow-x-auto">
        <Dropdown
          v-if="!showDatePicker"
          :options="options"
          class="!form-control !w-48"
          v-model="preset"
          placeholder="Select Range"
          @change="filters.period = preset"
        >
          <template #default>
            <div
              class="flex justify-between !w-48 items-center border border-gray-200 rounded-lg bg-white text-gray-700 px-3 py-2 hover:border-gray-300 hover:shadow-sm transition-colors cursor-pointer"
            >
              <div class="flex items-center">
                <LucideCalendar class="size-4 text-gray-400 mr-2" />
                <span class="text-sm">{{ preset }}</span>
              </div>
              <LucideChevronDown class="size-4 text-gray-400" />
            </div>
          </template>
        </Dropdown>
        <DateRangePicker
          v-else
          class="!w-48"
          ref="datePickerRef"
          v-model="filters.period"
          variant="outline"
          placeholder="Period"
          @update:model-value="handleDateChange"
          :formatter="formatRange"
        >
          <template #prefix>
            <LucideCalendar class="size-4 text-gray-400 mr-2" />
          </template>
        </DateRangePicker>
        <Link
          v-if="isManager"
          class="form-control w-48"
          doctype="HD Team"
          placeholder="Team"
          v-model="filters.team"
          :page-length="5"
          :hide-me="true"
        >
          <template #prefix>
            <LucideUsers class="size-4 text-gray-400 mr-2" />
          </template>
        </Link>
        <Link
          v-if="isManager"
          class="form-control w-48"
          doctype="HD Agent"
          placeholder="Agent"
          v-model="filters.agent"
          :page-length="5"
          :filters="agentFilter"
          :hide-me="true"
        >
          <template #prefix>
            <LucideUser class="size-4 text-gray-400 mr-2" />
          </template>
        </Link>
      </div>

      <!-- Status Cards Row -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-4">
        <StatusCard
          v-for="card in statusCards.data || []"
          :key="card.label"
          :label="card.label"
          :count="card.count"
          :color="card.color"
          :filters="{ status: card.status_filter }"
        />
        <template v-if="statusCards.loading">
          <div
            v-for="i in 6"
            :key="i"
            class="bg-white border border-gray-200 rounded-lg p-4 animate-pulse"
          >
            <div class="h-4 bg-gray-200 rounded w-20 mb-2"></div>
            <div class="h-8 bg-gray-200 rounded w-12"></div>
          </div>
        </template>
      </div>

      <!-- Today's Trends Section -->
      <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4">
        <TrendChartSection
          v-if="!trendData.loading && trendData.data"
          :today-data="trendData.data?.today || []"
          :yesterday-data="trendData.data?.yesterday || []"
          :summary-metrics="trendData.data?.summary || { received: 0, avgFirstResponse: 0, resolutionRate: 0 }"
        />
        <div v-else class="flex items-center justify-center h-64">
          <Button :loading="true" size="lg" variant="ghost" />
        </div>
      </div>

      <!-- Bottom Row: Unresolved, Undelivered Emails, Customer Satisfaction -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Unresolved Tickets -->
        <UnresolvedSection
          :groups="unresolvedData.data || []"
        />

        <!-- Undelivered Emails (placeholder) -->
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h3 class="text-base font-medium text-gray-900">Undelivered emails</h3>
              <p class="text-xs text-gray-500">Across helpdesk</p>
            </div>
            <button class="text-sm text-blue-600 hover:text-blue-700">
              View details
            </button>
          </div>
          <div class="flex flex-col items-center justify-center py-8 text-gray-400">
            <LucideMail class="w-12 h-12 mb-2 opacity-50" />
            <span class="text-sm">No undelivered emails</span>
          </div>
        </div>

        <!-- Customer Satisfaction -->
        <CustomerSatisfactionSection
          :responses-received="satisfactionData.data?.responsesReceived || 0"
          :positive="satisfactionData.data?.positive || 0"
          :neutral="satisfactionData.data?.neutral || 0"
          :negative="satisfactionData.data?.negative || 0"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { useAuthStore } from "@/stores/auth";
import {
  DateRangePicker,
  Dropdown,
  createResource,
  dayjs,
  usePageMeta,
} from "frappe-ui";
import { computed, onMounted, reactive, ref, watch } from "vue";
import LucideCalendar from "~icons/lucide/calendar";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideMail from "~icons/lucide/mail";
import LucideUser from "~icons/lucide/user";
import LucideUsers from "~icons/lucide/users";

import {
  StatusCard,
  TrendChartSection,
  UnresolvedSection,
  CustomerSatisfactionSection,
} from "./components";

const { isManager, userId } = useAuthStore();

const filters = reactive({
  period: getLastXDays(),
  agent: null as string | null,
  team: null as string | null,
});

// Status Cards Resource
const statusCards = createResource({
  url: "helpdesk.api.dashboard.get_status_card_data",
  cache: ["Dashboard", "StatusCards"],
  params: {
    filters: getApiFilters(),
  },
});

// Today's Trend Data Resource
const trendData = createResource({
  url: "helpdesk.api.dashboard.get_today_trend_data",
  cache: ["Dashboard", "TrendData"],
  params: {
    filters: getApiFilters(),
  },
});

// Unresolved Grouped Data Resource
const unresolvedData = createResource({
  url: "helpdesk.api.dashboard.get_unresolved_grouped_data",
  cache: ["Dashboard", "UnresolvedData"],
  params: {
    filters: getApiFilters(),
  },
});

// Satisfaction Data Resource
const satisfactionData = createResource({
  url: "helpdesk.api.dashboard.get_satisfaction_data",
  cache: ["Dashboard", "SatisfactionData"],
  params: {
    filters: getApiFilters(),
  },
});

const agentFilter = ref(null);
const teamMembers = createResource({
  url: "helpdesk.helpdesk.doctype.hd_team.hd_team.get_team_members",
  cache: ["Dashboard", "TeamMembers"],
  params: {
    team: filters.team,
  },
  onSuccess: (data: string[]) => {
    agentFilter.value = { name: ["in", data] };
  },
});

watch(
  () => filters.team,
  (newVal) => {
    filters.agent = null;
    if (newVal) {
      teamMembers.update({ params: { team: newVal } });
      teamMembers.reload();
    }
    if (!newVal) {
      agentFilter.value = null;
    }
  }
);

function getApiFilters() {
  return {
    from_date: filters.period?.split(",")[0] || null,
    to_date: filters.period?.split(",")[1] || null,
    agent: filters.agent || null,
    team: filters.team || null,
  };
}

function reloadAllResources() {
  const apiFilters = getApiFilters();

  statusCards.update({ params: { filters: apiFilters } });
  statusCards.reload();

  trendData.update({ params: { filters: apiFilters } });
  trendData.reload();

  unresolvedData.update({ params: { filters: apiFilters } });
  unresolvedData.reload();

  satisfactionData.update({ params: { filters: apiFilters } });
  satisfactionData.reload();
}

function getLastXDays(range: number = 30): string {
  const today = new Date();
  const lastXDate = new Date(today);
  lastXDate.setDate(today.getDate() - range);
  return `${dayjs(lastXDate).format("YYYY-MM-DD")},${dayjs(today).format("YYYY-MM-DD")}`;
}

const showDatePicker = ref(false);
const datePickerRef = ref(null);
const preset = ref("Last 30 Days");

const options = computed(() => [
  {
    group: "Presets",
    hideLabel: true,
    items: [
      { label: "Today", onClick: () => setPreset("Today", 0) },
      { label: "Last 7 Days", onClick: () => setPreset("Last 7 Days", 7) },
      { label: "Last 30 Days", onClick: () => setPreset("Last 30 Days", 30) },
      { label: "Last 60 Days", onClick: () => setPreset("Last 60 Days", 60) },
      { label: "Last 90 Days", onClick: () => setPreset("Last 90 Days", 90) },
    ],
  },
  {
    label: "Custom Range",
    onClick: () => {
      showDatePicker.value = true;
      setTimeout(() => datePickerRef.value?.open(), 0);
      preset.value = "Custom Range";
      filters.period = null;
    },
  },
]);

function setPreset(label: string, days: number) {
  preset.value = label;
  filters.period = getLastXDays(days);
}

function handleDateChange(e: string) {
  showDatePicker.value = false;
  preset.value = formatter(e);
}

function formatter(range: string) {
  if (!range) {
    filters.period = getLastXDays();
    preset.value = "Last 30 Days";
    return preset.value;
  }
  const [from, to] = range.split(",");
  return `${formatRange(from)} to ${formatRange(to)}`;
}

function formatRange(date: string) {
  const dateObj = new Date(date);
  return dateObj.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: dateObj.getFullYear() === new Date().getFullYear() ? undefined : "numeric",
  });
}

watch(
  () => filters,
  () => {
    if (!showDatePicker.value) {
      reloadAllResources();
    }
  },
  { deep: true }
);

onMounted(() => {
  if (!isManager) {
    filters.agent = userId;
    return;
  }
  reloadAllResources();
});

usePageMeta(() => ({ title: "Dashboard" }));
</script>

<style scoped>
:deep(.form-control button) {
  @apply text-sm rounded-lg py-2 border border-gray-200 bg-white placeholder-gray-400 hover:border-gray-300 hover:shadow-sm focus:bg-white focus:border-gray-400 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-gray-700 transition-colors w-full;
}
:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:deep(.form-control div) {
  width: 100%;
  display: flex;
}
</style>
