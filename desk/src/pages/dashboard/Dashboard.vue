<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Dashboard</div>
      </template>
      <template #right-header> </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-scroll">
      <!-- Filters -->
      <div class="mb-4 flex items-center gap-4">
        <DateRangePicker
          class="!w-48"
          v-model="filters.period"
          variant="outline"
          placeholder="Period"
          :formatter="(date: string) => {
            const dateObj = new Date(date);
            return dateObj.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: dateObj.getFullYear() === new Date().getFullYear() ? undefined : 'numeric',
            });
          }"
        />
        <Link
          class="form-control w-48"
          doctype="HD Team"
          placeholder="Team"
          v-model="filters.team"
          :page-length="5"
          :hide-me="true"
        >
          <template #prefix>
            <LucideUsers class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Link>
        <Link
          class="form-control w-48"
          doctype="HD Agent"
          placeholder="Agent"
          v-model="filters.agent"
          :page-length="5"
        >
          <template #prefix>
            <LucideUser class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Link>
      </div>
      <div v-if="!loading">
        <!-- Number Cards -->
        <div
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
          v-if="!numberCards.loading"
        >
          <NumberChart
            v-for="(config, index) in numberCards.data"
            :key="index"
            class="border rounded-md"
            :config="config"
          />
        </div>
        <!-- Trend Charts -->
        <div
          class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4"
          v-if="!trendData.loading"
        >
          <div
            class="border rounded-md min-h-80"
            v-for="(chart, index) in trendData.data"
            :key="index"
          >
            <component :is="getChartType(chart)" />
          </div>
        </div>
        <!-- Master Data Charts -->
        <div
          class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mt-4"
          v-if="!masterData.loading"
        >
          <div
            class="border rounded-md"
            v-for="(chart, index) in masterData.data"
            :key="index"
          >
            <component :is="getChartType(chart)" />
          </div>
        </div>
      </div>
      <!-- Loading State -->
      <div
        v-else
        class="flex items-center justify-center h-[240px] gap-2 rounded"
      >
        <Button :loading="true" size="2xl" variant="ghost" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import {
  AxisChart,
  createResource,
  DateRangePicker,
  dayjs,
  DonutChart,
  NumberChart,
  usePageMeta,
} from "frappe-ui";
import { computed, h, reactive, watch } from "vue";

const filters = reactive({
  period: getLastXDays(),
  // period: null,
  agent: null,
  team: null,
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

const numberCards = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  cache: ["Analytics", "NumberCards"],
  params: {
    type: "number_card",
  },
  auto: true,
});

const masterData = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  cache: ["Analytics", "MasterCharts"],
  params: {
    type: "master",
  },
  auto: true,
});

const trendData = createResource({
  url: "helpdesk.api.dashboard.get_dashboard_data",
  cache: ["Analytics", "TrendCharts"],
  params: {
    type: "trend",
  },
  auto: true,
});

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
  const last30Days = new Date(today);
  last30Days.setDate(today.getDate() - range);

  return `${dayjs(last30Days).format("YYYY-MM-DD")},${dayjs(today).format(
    "YYYY-MM-DD"
  )}`;
}

watch(
  () => filters,
  (newVal) => {
    const filters = {
      from_date: newVal.period?.split(",")[0] || null,
      to_date: newVal.period?.split(",")[1] || null,
      agent: newVal.agent || null,
      team: newVal.team || null,
    };
    numberCards.update({
      params: {
        type: "number_card",
        filters: filters,
      },
    });
    numberCards.reload();
    masterData.update({
      params: {
        type: "master",
        filters: filters,
      },
    });
    masterData.reload();
    trendData.update({
      params: {
        type: "trend",
        filters: filters,
      },
    });
    trendData.reload();
  },
  { deep: true }
);

usePageMeta(() => {
  return {
    title: "Dashboard",
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
</style>
