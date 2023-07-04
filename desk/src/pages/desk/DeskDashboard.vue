<template>
  <div class="flex flex-col">
    <PageTitle>
      <template #title>
        <div
          class="flex select-none items-center text-2xl font-semibold text-gray-900"
        >
          Hello,
          <div class="mx-1 text-gray-800">{{ authStore.userFirstName }}</div>
          👋
        </div>
      </template>
      <template #right>
        <Tooltip v-if="!isEmpty(items.data)" placement="left" :text="dateInfo">
          <IconInfo class="h-5 w-5 text-gray-800" />
        </Tooltip>
      </template>
    </PageTitle>
    <div
      v-if="isEmpty(items.data)"
      class="flex grow select-none items-center justify-center text-base text-gray-700"
    >
      📊 Oops, looks like there are no charts to display on the dashboard right
      now.
    </div>
    <div v-else class="space-y-3 overflow-y-scroll p-4">
      <div class="grid grid-cols-3 gap-3">
        <SingleString
          v-for="i in items.data.filter((i) => !i.is_chart)"
          :key="i.title"
          :title="i.title"
          :value="i.data"
        />
      </div>
      <div class="grid grid-cols-3 gap-3">
        <div
          v-for="i in items.data.filter((i) => i.is_chart)"
          :key="i.title"
          class="h-64 rounded border p-2"
        >
          <PieChart
            v-if="i.is_chart && i.chart_type === 'Pie'"
            :title="i.title"
            :data="i.data"
          />
          <LineChart
            v-else-if="i.is_chart && i.chart_type === 'Line'"
            :title="i.title"
            :data="i.data"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createResource, Tooltip } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { isEmpty } from "lodash";
import PageTitle from "@/components/PageTitle.vue";
import LineChart from "@/components/charts/LineChart.vue";
import PieChart from "@/components/charts/PieChart.vue";
import SingleString from "@/components/charts/SingleString.vue";
import IconInfo from "~icons/espresso/alert-circle";

const authStore = useAuthStore();
const items = createResource({
  url: "helpdesk.api.dashboard.get_all",
  auto: true,
});

const dateInfo =
  "📊 The information displayed in these charts are derived from data collected over the past 30 days";
</script>
