<template>
  <span>
    <PageTitle title="Dashboard">
      <template #right>
        <Tooltip v-if="!isEmpty(items.data)" placement="left" :text="dateInfo">
          <div class="flex h-7 w-7 items-center justify-between">
            <IconInfo class="h-5 w-5 text-gray-700" />
          </div>
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
    <div v-else class="space-y-3 overflow-y-scroll p-5">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <SingleString
          v-for="i in items.data.filter((i) => !i.is_chart)"
          :key="i.title"
          :title="i.title"
          :value="i.data"
        />
      </div>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
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
  </span>
</template>

<script setup lang="ts">
import { createResource, usePageMeta, Tooltip } from "frappe-ui";
import { isEmpty } from "lodash";
import PageTitle from "@/components/PageTitle.vue";
import LineChart from "@/components/charts/LineChart.vue";
import PieChart from "@/components/charts/PieChart.vue";
import SingleString from "@/components/charts/SingleString.vue";
import IconInfo from "~icons/espresso/alert-circle";

const items = createResource({
  url: "helpdesk.api.dashboard.get_all",
  auto: true,
});

const dateInfo =
  "📊 The information displayed in these charts are derived from data collected over the past 30 days";

usePageMeta(() => {
  return {
    title: "Dashboard",
  };
});
</script>
