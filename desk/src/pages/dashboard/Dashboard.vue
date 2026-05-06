<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-ink-gray-9">
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
          v-model="filters.period"
          variant="outline"
          :placeholder="__('Period')"
          @update:model-value="
            (e:string) => {
              showDatePicker = false;
              preset = formatter(e);
            }
          "
          :formatter="formatRange"
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
            class="border rounded-md"
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

const filters = reactive({
  period: getLastXDays(),
  agent: null,
  team: null,
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

const numberCards = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  cache: ["Analytics", "NumberCards"],
  params: {
    dashboard_type: "number_card",
    filters,
  },
});

const masterData = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  cache: ["Analytics", "MasterCharts"],
  params: {
    dashboard_type: "master",
    filters,
  },
});

const trendData = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  cache: ["Analytics", "TrendCharts"],
  params: {
    dashboard_type: "trend",
    filters,
  },
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
  (newVal) => {
    if (showDatePicker.value) {
      return;
    }
    const filters = {
      from_date: newVal.period?.split(",")[0] || null,
      to_date: newVal.period?.split(",")[1] || null,
      agent: newVal.agent || null,
      team: newVal.team || null,
    };

    numberCards.update({
      params: {
        dashboard_type: "number_card",
        filters: filters,
      },
    });
    numberCards.reload();

    masterData.update({
      params: {
        dashboard_type: "master",
        filters: filters,
      },
    });
    masterData.reload();

    trendData.update({
      params: {
        dashboard_type: "trend",
        filters: filters,
      },
    });
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
</script>

<style scoped>
:deep(.form-control button) {
  @apply text-base rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark];
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
