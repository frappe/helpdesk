<template>
  <div class="p-5 grid grid-cols-4 gap-2.5 min-h-[160px]">
    <template v-if="!analytics.loading && analytics.data">
      <div
        v-for="(chartData, key) in analytics.data"
        class="h-full w-full rounded border border-outline-gray-1"
      >
        <BarChartCard
          v-if="key === 'feedback_received'"
          :title="__('Avg. Feedback Received')"
          :data="chartData"
          bar-color="#E79913"
          measure="average"
          :timelineFilter="false"
          :dt="props.dt"
          :dn="props.dn"
          orientation="horizontal"
          :negativeIsBetter="false"
        >
          <template #text="{ text }">
            <div class="flex flex-col gap-2">
              <div class="flex items-center gap-2">
                <LucideStar class="size-4 fill-ink-amber-2 text-ink-amber-2" />
                <span class="text-2xl font-medium text-ink-gray-8">
                  {{ text }}
                </span>
              </div>
              <span class="text-sm text-ink-gray-5">
                {{ (chartData as any).total ?? 0 }} {{ __("reviews") }}
              </span>
            </div>
          </template>
        </BarChartCard>
        <BarChartCard
          v-if="key === 'sla_violations'"
          :title="__('Failed SLAs')"
          :data="chartData"
          api-url="helpdesk.api.ticket_stats.get_sla_violations"
          :dt="props.dt"
          :dn="props.dn"
          orientation="horizontal"
          bar-color="#D13A26"
        />
        <LineChartCard
          v-if="key === 'avg_first_response_time'"
          :title="__('Avg. First Response Time')"
          :data="chartData"
          :chart-color="{
            lineColor: '#F35555',
            gradientColor: { start: '#ee9d9f', end: 'rgba(251,232,233,0)' },
          }"
          api-url="helpdesk.api.ticket_stats.get_avg_first_response_time"
          :dt="props.dt"
          :dn="props.dn"
          orientation="horizontal"
        />
        <LineChartCard
          v-if="key === 'avg_resolution_time'"
          :title="__('Avg. Resolution Time')"
          :data="chartData"
          :chart-color="{
            lineColor: '#7263E8',
            gradientColor: { start: '#a093ee', end: 'rgba(239, 237, 252,0)' },
          }"
          api-url="helpdesk.api.ticket_stats.get_avg_resolution_time"
          :dt="props.dt"
          :dn="props.dn"
          orientation="horizontal"
        />
      </div>
    </template>
    <template v-else-if="analytics.loading">
      <!-- TODO: add skeleton here when we pull latest changes -->
      <div class="col-span-4 flex items-center justify-center h-full">
        <LoadingIndicator />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import BarChartCard from "../BarChartCard.vue";
import LineChartCard from "../LineChartCard.vue";

const props = defineProps<{
  dt: "HD Customer" | "Contact";
  dn: string;
}>();

const analytics = createResource({
  url: "helpdesk.api.ticket_stats.get_ticket_stats",
  method: "GET",
  makeParams: () => ({
    dt: props.dt,
    dn: props.dn,
  }),
  auto: true,
});
</script>
