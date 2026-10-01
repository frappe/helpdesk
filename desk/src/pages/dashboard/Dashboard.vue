<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ __(dashboardTitle) }}
        </div>
      </template>
      <template #right-header>
        <!-- Segmented pill toggle: only visible to managers -->
        <div v-if="isManager">
          <TabButtons v-model="activeTab" :buttons="tabButtons" />
        </div>
      </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-scroll">
      <!-- Filters -->
      <div class="mb-4 flex items-center gap-4 overflow-x-auto">
        <Dropdown
          v-if="!showDatePicker"
          :options="options"
          class="!form-control !w-48"
          v-model="preset"
          :placeholder="__('Select Range')"
          @change="filters.period = preset"
        >
          <template #default>
            <div
              class="flex justify-between !min-w-48 items-center border border-outline-gray-2 rounded text-ink-gray-8 px-2 py-1.5 hover:border-outline-gray-3 hover:shadow-sm focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 transition-colors h-7 cursor-pointer"
            >
              <div class="flex items-center">
                <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
                <span class="text-base whitespace-nowrap">{{ preset }}</span>
              </div>
              <LucideChevronDown class="size-4 text-ink-gray-5" />
            </div>
          </template>
        </Dropdown>
        <DateRangePicker
          v-else
          class="!w-48"
          ref="datePickerRef"
          v-model="periodRange"
          variant="outline"
          :placeholder="__('Period')"
          :format="'MMM D'"
        >
          <template #prefix>
            <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </DateRangePicker>
        <Link
          v-if="isManager && !viewMyStats"
          class="form-control w-48"
          doctype="HD Team"
          :placeholder="__('Team')"
          v-model="filters.team"
          :page-length="5"
          :hide-me="true"
        >
          <template #prefix>
            <LucideUsers class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Link>
        <Link
          v-if="isManager && !viewMyStats"
          class="form-control w-48"
          doctype="HD Agent"
          :placeholder="__('Agent')"
          v-model="filters.agent"
          :page-length="5"
          :filters="agentFilter"
          :hide-me="true"
        >
          <template #prefix>
            <LucideUser class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Link>
      </div>
      <!-- Charts -->

      <!-- Number Cards -->
      <div
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4"
        v-if="!numberCards.loading"
      >
        <Tooltip
          v-for="(config, index) in numberCards.data"
          :text="config.tooltip"
        >
          <NumberChart
            :key="index"
            class="border rounded-md min-h-[114px]"
            :config="config"
          />
        </Tooltip>
      </div>
      <div
        v-if="!loading && !isEmpty"
        class="transition-all animate-fade-in duration-300"
      >
        <!-- Trend Charts -->
        <div
          class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4"
          v-if="!trendData.loading"
        >
          <template v-for="(chart, index) in trendData.data" :key="index">
            <!-- has data -->
            <div v-if="!isChartEmpty(chart)" class="border rounded-md min-h-80">
              <component :is="getChartType(chart)" />
            </div>

            <!-- chart with no data -->
            <SkeletonLoader
              v-else
              :variants="['bar-chart', 'empty-state']"
              :bar-chart-count="1"
              :has-applied-filter="hasAppliedFilter"
              :empty-states="[
                {
                  title: `No ${(chart?.title).toLowerCase()} available.`,
                },
              ]"
            />
          </template>
        </div>
        <!-- Master Data Charts -->
        <div
          class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mt-4"
          v-if="!masterData.loading"
        >
          <template v-for="(chart, index) in masterData.data" :key="index">
            <!-- has data -->
            <div v-if="!isChartEmpty(chart)" class="border rounded-md min-h-80">
              <component :is="getChartType(chart)" />
            </div>

            <!-- chart with no data -->
            <SkeletonLoader
              v-else
              :variants="['bar-chart', 'empty-state']"
              :bar-chart-count="1"
              :has-applied-filter="hasAppliedFilter"
              :empty-states="[
                {
                  title: `No ${(chart?.title).toLowerCase()} available.`,
                },
              ]"
            />
          </template>
        </div>
      </div>

      <!-- Skeleton Loading State -->
      <div class="flex flex-col gap-4">
        <SkeletonLoader
          v-if="numberCards.loading"
          :variants="['number-cards']"
          :number-cards-count="5"
          :loading="true"
        />
        <SkeletonLoader
          v-if="trendData.loading"
          :variants="['bar-chart']"
          :bar-chart-count="4"
          :loading="true"
        />
      </div>

      <!-- complete empty state -->
      <div
        v-if="isEmpty"
        class="transition-all animate-fade-in duration-300 relative"
      >
        <div>
          <SkeletonLoader
            :variants="['bar-chart', 'empty-state']"
            :bar-chart-count="6"
            :empty-states="emptyStates"
            :has-applied-filter="hasAppliedFilter"
          />
        </div>
      </div>

      <div v-if="!projects.loading && projects.data?.length" class="mt-6">
        <div class="text-sm-medium text-ink-gray-7 mb-3">{{ __("Projects") }}</div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <router-link
            v-for="p in projects.data"
            :key="p.name"
            :to="{ name: 'TaskyProject', params: { projectId: p.name } }"
            class="bg-surface-white border border-outline-gray-2 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm-medium text-ink-gray-9 truncate">{{ p.project_name }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="p.status === 'Completed' ? 'bg-ink-green-1 text-ink-green-8' : 'bg-ink-blue-1 text-ink-blue-8'">{{ p.status }}</span>
            </div>
            <div class="w-full h-2 rounded-full bg-surface-gray-2 overflow-hidden mb-2 flex">
              <div v-if="p._stats?.completed" class="h-full bg-ink-green-5" :style="{ width: (p._stats.completed / p._stats.total * 100) + '%' }" />
              <div v-if="p._stats?.in_progress" class="h-full bg-ink-amber-5" :style="{ width: (p._stats.in_progress / p._stats.total * 100) + '%' }" />
              <div v-if="p._stats?.cancelled" class="h-full bg-ink-red-5" :style="{ width: (p._stats.cancelled / p._stats.total * 100) + '%' }" />
            </div>
            <div class="flex items-center gap-3 text-xs text-ink-gray-5">
              <span>{{ p._stats?.completed || 0 }}/{{ p._stats?.total || 0 }} tasks</span>
              <span v-if="p._stats?.overdue" class="text-ink-red-6">{{ p._stats.overdue }} overdue</span>
            </div>
          </router-link>
        </div>
      </div>

      <div v-if="!myTasks.loading && myTasks.data?.length" class="mt-6">
        <div class="text-sm-medium text-ink-gray-7 mb-3">{{ __("My Tasks") }}</div>
        <div class="bg-surface-white border border-outline-gray-2 rounded-lg overflow-hidden">
          <div v-for="t in myTasks.data.slice(0, 5)" :key="t.name" class="flex items-center gap-3 px-4 py-2.5 border-b border-outline-gray-2 last:border-b-0 hover:bg-surface-gray-1">
            <router-link :to="{ name: 'TaskyProject', params: { projectId: t.project } }" class="size-1.5 rounded-full shrink-0" :class="t.status === 'Completed' ? 'bg-ink-green-5' : t.status === 'Working' ? 'bg-ink-amber-5' : 'bg-ink-gray-4'" />
            <span class="flex-1 text-sm text-ink-gray-8 truncate">{{ t.subject }}</span>
            <span class="text-xs text-ink-gray-5">{{ t.phase }}</span>
            <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="t.status === 'Completed' ? 'bg-ink-green-1 text-ink-green-8' : 'bg-ink-gray-2 text-ink-gray-7'">{{ t.status }}</span>
          </div>
          <router-link :to="{ name: 'TaskyMyTasks' }" class="block text-center text-xs text-ink-gray-6 hover:text-ink-gray-8 py-2 transition-colors">{{ __("View all tasks") }} →</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import {
  AxisChart,
  createResource,
  DateRangePicker,
  dayjs,
  DonutChart,
  Dropdown,
  TabButtons,
  NumberChart,
  Tooltip,
  usePageMeta,
} from "frappe-ui";
const { isMobileView } = useScreenSize();
import { computed, h, onMounted, reactive, ref, watch } from "vue";
import LucideBuilding2 from "~icons/lucide/building-2";
import LucideUser from "~icons/lucide/user";
import { useScreenSize } from "@/composables/screen";
import { useStorage } from "@vueuse/core";

interface NumberCardData {
  title: string;
  value: number;
  delta: number | null;
  deltaSuffix: string;
  suffix?: string;
  negativeIsBetter?: boolean;
  tooltip: string;
}

type Filters = {
  period: string;
  agent: null | string;
  team: null | string;
};

const filters = reactive<Filters>({
  period: getLastXDays(),
  agent: null,
  team: null,
});

interface ChartData {
  data: ChartValues[];
  title: string;
  type: "axis" | "pie";
}

interface ChartValues {
  date: Date;
  Open: number;
  Closed: number;
  "SLA Fulfilled": number;
}

const dashboardTitle = computed(() => {
  if (!isManager) return __("Agent Dashboard");
  return viewMyStats.value ? __("My Dashboard") : __("Organization Dashboard");
});

const colors = [
  "#318AD8",
  "#F683AE",
  "#48BB74",
  "#F56B6B",
  "#FACF7A",
  "#44427B",
  "#5FD8C4",
  "#F8814F",
  "#15CCEF",
  "#A6B1B9",
];
const emptyStates = [
  {
    title: "No ticket activity",
    message: "Ticket trends will appear here once tickets are created.",
  },
  {
    title: "No feedback data",
    message: "Feedback insights will appear once responses are collected.",
  },
  {
    title: "No team data",
    message: "Tickets will be grouped by team once available.",
  },
  {
    title: "No ticket type data",
    message: "Tickets will be categorized by type once created.",
  },
  {
    title: "No priority data",
    message: "Ticket priorities will be reflected here once assigned.",
  },
  {
    title: "No channel data",
    message: "Tickets will be grouped by channel once received.",
  },
];

const tabButtons = computed(() => {
  if (isMobileView.value) {
    return [
      { value: "organization", icon: h(LucideBuilding2, { class: "size-4" }) },
      { value: "my_stats", icon: h(LucideUser, { class: "size-4" }) },
    ];
  }
  return [
    {
      value: "organization",
      iconLeft: h(LucideBuilding2, { class: "size-4" }),
      label: "My Organization",
    },
    {
      value: "my_stats",
      iconLeft: h(LucideUser, { class: "size-4" }),
      label: "My Stats",
    },
  ];
});

const hasAppliedFilter = computed(() => {
  return (
    filters.agent ||
    filters.team ||
    (filters.period && filters.period !== getLastXDays(30))
  );
});

const isEmpty = computed(() => {
  if (!numberCards.data || !trendData.data || !masterData.data) return false;
  return (
    (numberCards.data as NumberCardData[]).every((d) => d.value === 0) &&
    (trendData.data as ChartData[]).every((d) => !d.data?.length) &&
    (masterData.data as ChartData[]).every((d) => !d.data?.length)
  );
});

const parseFilters = (filters: Filters) => {
  return {
    from_date: filters.period?.split(",")[0] ?? null,
    to_date: filters.period?.split(",")[1] ?? null,
    team: filters.team,
    agent: filters.agent,
  };
};

// No `cache` key here: a static cache key makes frappe-ui return the same
// resource instance across navigations, still bound to the previous mount's
// `filters` closure, so reloads after navigating back send stale params.
const numberCards = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  makeParams: () => ({
    dashboard_type: "number_card",
    filters: parseFilters(filters),
  }),
});

const masterData = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  makeParams: () => ({
    dashboard_type: "master",
    filters: parseFilters(filters),
  }),
});

const trendData = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  makeParams: () => ({
    dashboard_type: "trend",
    filters: parseFilters(filters),
  }),
});

const agentFilter = ref(null);
const teamMembers = createResource({
  url: "helpdesk.helpdesk.doctype.hd_team.hd_team.get_team_members",
  cache: ["Analytics", "TeamMembers"],
  params: {
    team: filters.team,
  },
  onSuccess: (data) => {
    agentFilter.value = { name: ["in", data] };
  },
});

const { isManager, userId } = useAuthStore();

const viewMyStats = ref(false);
const activeTab = useStorage("dashboard_active_tab", "organization");
function validateView(myStats: boolean) {
  viewMyStats.value = myStats;
  if (myStats) {
    filters.team = null;
    filters.agent = userId;
  } else {
    filters.agent = null;
  }
}

watch(activeTab, (val) => {
  validateView(val === "my_stats");
});

watch(
  () => filters.team,
  (newVal) => {
    filters.agent = null; // Reset agent when team is selected
    if (newVal) {
      teamMembers.update({
        params: {
          team: newVal,
        },
      });
      teamMembers.reload();
    }
    if (!newVal) {
      agentFilter.value = null; // Reset agent filter if no team is selected
    }
  }
);

//check empty for individual charts
function isChartEmpty(chart: any) {
  if (!chart.data?.length) return true;
  return chart.data.every((row: any) =>
    Object.entries(row)
      .filter(([key]) => key !== "date")
      .every(([, val]) => val === null || val === 0)
  );
}

const loading = computed(() => {
  return numberCards.loading || masterData.loading || trendData.loading;
});

function getChartType(chart: any) {
  chart.colors = colors;
  if (chart["type"] === "axis") {
    return h(AxisChart, {
      config: chart,
    });
  }
  if (chart["type"] === "pie") {
    return h(DonutChart, {
      config: chart,
    });
  }
}

function getLastXDays(range: number = 30): string {
  const today = new Date();
  const lastXDate = new Date(today);
  lastXDate.setDate(today.getDate() - range);

  return `${dayjs(lastXDate).format("YYYY-MM-DD")},${dayjs(today).format(
    "YYYY-MM-DD"
  )}`;
}

const showDatePicker = ref(false);
const datePickerRef = ref(null);
const preset = ref(__("Last 30 Days"));

// frappe-ui v1 DateRangePicker models a [from, to] tuple; filters.period and
// the API keep the legacy "from,to" string, so convert at the picker boundary.
const periodRange = computed({
  get: (): string[] => (filters.period ? filters.period.split(",") : []),
  set: (range: string[]) => {
    showDatePicker.value = false;
    filters.period = range?.length ? range.join(",") : "";
    preset.value = formatter(filters.period);
  },
});

const options = computed(() => [
  {
    group: __("Presets"),
    hideLabel: true,
    items: [
      {
        label: __("Today"),
        onClick: () => {
          preset.value = __("Today");
          filters.period = getLastXDays(0);
        },
      },
      {
        label: __("Last 7 Days"),
        onClick: () => {
          preset.value = __("Last 7 Days");
          filters.period = getLastXDays(7);
        },
      },
      {
        label: __("Last 30 Days"),
        onClick: () => {
          preset.value = __("Last 30 Days");
          filters.period = getLastXDays(30);
        },
      },
      {
        label: __("Last 60 Days"),
        onClick: () => {
          preset.value = __("Last 60 Days");
          filters.period = getLastXDays(60);
        },
      },
      {
        label: __("Last 90 Days"),
        onClick: () => {
          preset.value = __("Last 90 Days");
          filters.period = getLastXDays(90);
        },
      },
    ],
  },
  {
    label: __("Custom Range"),
    onClick: () => {
      showDatePicker.value = true;
      setTimeout(() => {
        datePickerRef.value?.open();
      }, 0);
      preset.value = __("Custom Range");
      filters.period = null; // Reset period to allow custom date selection
    },
  },
]);

function formatter(range: string) {
  if (!range) {
    filters.period = getLastXDays();
    preset.value = __("Last 30 Days");
    return preset.value;
  }
  let [from, to] = range.split(",");
  return `${formatRange(from)} to ${formatRange(to)}`;
}

function formatRange(date: string) {
  const dateObj = new Date(date);
  return dateObj.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year:
      dateObj.getFullYear() === new Date().getFullYear()
        ? undefined
        : "numeric",
  });
}

watch(
  () => filters,
  () => {
    if (showDatePicker.value && !filters.period) return;
    numberCards.reload();
    masterData.reload();
    trendData.reload();
  },
  { deep: true }
);

onMounted(() => {
  if (!isManager) {
    filters.agent = userId;
  } else {
    validateView(activeTab.value === "my_stats");
  }
  numberCards.reload();
  masterData.reload();
  trendData.reload();
});

usePageMeta(() => {
  return {
    title: __("Dashboard"),
  };
});
const myTasks = createResource({
  url: "helpdesk.tasky.api.get_my_tasks",
  auto: true,
  transform: (d: any[]) => d ?? [],
});

const projects = createResource({
  url: "helpdesk.tasky.api.get_projects",
  auto: true,
  transform(d: any[]) {
    if (!d) return [];
    // Fetch dashboard stats for each project
    d.forEach((p: any) => {
      createResource({
        url: "helpdesk.tasky.api.get_project_dashboard",
        params: { project: p.name },
        auto: true,
        onSuccess(stats: any) { p._stats = stats.stats; }
      });
    });
    return d;
  },
});

</script>

<style scoped>
:deep(.form-control button) {
  @apply text-base rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-base placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-base focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark];
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
