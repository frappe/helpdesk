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
      <div class="mb-4 flex items-center gap-4 overflow-x-auto">
        <Dropdown
          v-if="!showDatePicker"
          :options="options"
          class="form-control !w-48"
          v-model="preset"
          placeholder="Select Range"
          @change="filters.period = preset"
          :button="{
            label: preset,
            class:
              '!w-full justify-start [&>span]:mr-auto [&>svg]:text-ink-gray-5 ',
            variant: 'ghost',
            iconRight: 'chevron-down',
            iconLeft: 'calendar',
          }"
        >
          <template #prefix>
            <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Dropdown>
        <DateRangePicker
          v-else
          class="!w-48"
          ref="datePickerRef"
          v-model="filters.period"
          variant="outline"
          placeholder="Period"
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
          v-if="isManager"
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
            <LucideUser class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Link>
      </div>
      <!-- Charts -->
      <div v-if="!loading" class="transition-all animate-fade-in duration-300">
        <!-- Number Cards -->
        <div
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
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
        class="flex items-center justify-center h-[240px] gap-2 rounded transition-all animate-fade-in"
      >
        <Button :loading="true" size="2xl" variant="ghost" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { useAuthStore } from "@/stores/auth";
import {
  AxisChart,
  createResource,
  DateRangePicker,
  dayjs,
  DonutChart,
  Dropdown,
  NumberChart,
  Tooltip,
  usePageMeta,
} from "frappe-ui";
import { computed, h, onMounted, reactive, ref, watch } from "vue";

const { isManager, userId } = useAuthStore();

const filters = reactive({
  period: getLastXDays(),
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
    // Set Agent Filters
    agentFilter.value = { name: ["in", data] };
  },
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
const preset = ref("Last 30 Days");

const options = computed(() => [
  {
    group: "Presets",
    hideLabel: true,
    items: [
      {
        label: "Today",
        onClick: () => {
          preset.value = "Today";
          filters.period = getLastXDays(0);
        },
      },
      {
        label: "Last 7 Days",
        onClick: () => {
          preset.value = "Last 7 Days";
          filters.period = getLastXDays(7);
        },
      },
      {
        label: "Last 30 Days",
        onClick: () => {
          preset.value = "Last 30 Days";
          filters.period = getLastXDays(30);
        },
      },
      {
        label: "Last 60 Days",
        onClick: () => {
          preset.value = "Last 60 Days";
          filters.period = getLastXDays(60);
        },
      },
      {
        label: "Last 90 Days",
        onClick: () => {
          preset.value = "Last 90 Days";
          filters.period = getLastXDays(90);
        },
      },
    ],
  },
  {
    label: "Custom Range",
    onClick: () => {
      showDatePicker.value = true;
      setTimeout(() => {
        datePickerRef.value?.open();
      }, 0);
      preset.value = "Custom Range";
      filters.period = null; // Reset period to allow custom date selection
    },
  },
]);

function formatter(range: string) {
  if (!range) {
    filters.period = getLastXDays();
    preset.value = "Last 30 Days";
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
    // when filters are updated, resources are reloaded coz of the watcher
    filters.agent = userId;
    return;
  }
  // If not managers call the resources
  numberCards.reload();
  masterData.reload();
  trendData.reload();
});

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

:deep(.form-control div) {
  width: 100%;
  display: flex;
}
</style>
